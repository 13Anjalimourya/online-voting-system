import uuid
import base64
import random
import qrcode
from django.template.loader import get_template
from django.http import JsonResponse
from django.db.models import Count
from datetime import timedelta
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from reportlab.pdfgen import canvas
from django.contrib.auth.decorators import login_required
from .models import Voter, Party, Vote, Election
from django.contrib import messages
from .utils import generate_otp, otp_valid, generate_qr
from django.conf import settings

from io import BytesIO
from reportlab.lib.utils import ImageReader


# ----------------------------
# 1️⃣ Index / Static Pages
# ----------------------------
def index_view(request):
    return render(request, 'voting/index.html')

def about_view(request):
    return render(request, 'voting/about.html')

@login_required
def profile(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        return redirect('voter_id')  # agar session me voter_id nahi, login page

    voter = Voter.objects.get(voter_id=voter_id)
    return render(request, 'voting/profile.html', {'voter': voter})

@login_required
def profile_edit_view(request):
    return render(request, 'voting/profile_edit.html')

@login_required
def change_password_view(request):
    return render(request, 'voting/change_password.html')


# ----------------------------
# 2️⃣ Voter ID & OTP Handling
# ----------------------------
def voter_id_view(request):
    if request.method == 'POST':
        voter_id = request.POST.get('voter_id')
        try:
            voter = Voter.objects.get(voter_id=voter_id)
        except Voter.DoesNotExist:
            messages.error(request, "Invalid Voter ID")
            return redirect('voter-id')

        if voter.is_blocked:
            return HttpResponse("❌ You are blocked due to multiple wrong OTP attempts")

        # Generate OTP
        voter.otp = generate_otp()
        voter.otp_created_at = timezone.now()
        voter.otp_attempts = 0
        voter.save()

        # Send OTP email
        html_content = f"""
        <h2>Online Voting OTP</h2>
        <p>Hello {voter.full_name},</p>
        <p>Your OTP is:</p>
        <h1 style="color:blue">{voter.otp}</h1>
        <p>This OTP is valid for 5 minutes.</p>
        """
        email = EmailMultiAlternatives(
            subject="Your Voting OTP",
            body=f"Your OTP is {voter.otp}",
            from_email=settings.EMAIL_HOST_USER,
            to=[voter.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        request.session['voter_id'] = voter_id
        return redirect('otp')

    return render(request, 'voting/voter_id.html')


def otp_valid(voter):
    """Check if OTP is still valid (5 minutes)"""
    if not voter.otp_created_at:
        return False
    return timezone.now() <= voter.otp_created_at + timedelta(minutes=5)


def otp_view(request):
    voter_id = request.session.get('voter_id')
    
    if not voter_id:
        return redirect('voter-id')

    try:
        voter = Voter.objects.get(voter_id=voter_id)
    except Voter.DoesNotExist:
        return HttpResponse("Voter not found")

    if voter.is_blocked:
        return HttpResponse("❌ You are blocked due to multiple wrong OTP attempts")

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        device_id = request.POST.get('device_id')
        ip = request.META.get('REMOTE_ADDR')

        if entered_otp != voter.otp or not otp_valid(voter):
            voter.otp_attempts += 1
            if voter.otp_attempts >= 3:
                voter.is_blocked = True
            voter.save()
            messages.error(request, "Invalid or expired OTP")
            return redirect('otp')

        # One device & IP check
        if voter.device_id and voter.device_id != device_id:
            return HttpResponse("Already logged in on another device")
        if voter.ip_address and voter.ip_address != ip:
            return HttpResponse("IP address mismatch")

        # OTP success
        voter.device_id = device_id
        voter.ip_address = ip
        voter.otp = None
        voter.otp_created_at = None
        voter.otp_attempts = 0
        voter.save()
        
        request.session['voter_name'] = voter.full_name
        return redirect('voter-info')

    return render(request, 'voting/otp_verify.html')


def resend_otp(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        return redirect('voter-id')

    voter = Voter.objects.get(voter_id=voter_id)
    if voter.is_blocked:
        return HttpResponse("❌ You are blocked")

    voter.otp = generate_otp()
    voter.otp_created_at = timezone.now()
    voter.otp_attempts = 0
    voter.save()

    # Send email again
    html_content = f"<h2>Your new OTP: {voter.otp}</h2>"
    email = EmailMultiAlternatives(
        subject="New Voting OTP",
        body=f"Your new OTP is {voter.otp}",
        from_email=settings.EMAIL_HOST_USER,
        to=[voter.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    messages.success(request, "A new OTP has been sent to your email")
    return redirect('otp')


# ----------------------------
# 3️⃣ Voter Info Page
# ----------------------------
def voter_info(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        return redirect('voter-id')

    voter = Voter.objects.get(voter_id=voter_id)
    return render(request, 'voting/voter_info.html', {'voter': voter})


# ----------------------------
# 4️⃣ Voting / Parties
# ----------------------------


def parties_view(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        messages.error(request, "Please login or enter your Voter ID first.")
        return redirect('voter-id')

    voter = get_object_or_404(Voter, voter_id=voter_id)

    if voter.has_voted:
        return redirect('receipt')

    # Fetch parties for voter's constituency
    #parties = Party.objects.filter(constituency=voter.constituency)
    parties = Party.objects.all()

    if request.method == 'POST':
        now = timezone.now()
        election = Election.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).first()

        if not election:
            messages.error(request, "Voting is closed at this time.")
            return redirect('home')

        party_id = request.POST.get('party_id')
        try:
            party = Party.objects.get(id=party_id)
        except Party.DoesNotExist:
            messages.error(request, "Selected party does not exist.")
            return redirect('parties')

        receipt_id = str(uuid.uuid4())[:10].upper()
        Vote.objects.create(voter=voter, party=party, )
        voter.has_voted = True
        voter.save()

        return redirect('receipt')

    return render(request, 'voting/parties.html', {
        'parties': parties,
        'voter': voter
    })


# ----------------------------
# 5️⃣ Receipt & PDF
# ----------------------------
def receipt_view(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        messages.error(request, "No voter session found.")
        return redirect('home')

    voter = Voter.objects.get(voter_id=voter_id)

    try:
        vote = Vote.objects.get(voter=voter)
    except Vote.DoesNotExist:
        messages.error(request, "You have not voted yet.")
        return redirect('parties')

    election = Election.objects.filter(is_active=True).first()

    # ✅ Clear session safely AFTER retrieving vote info
    request.session.flush()
    logout(request)

    return render(request, 'voting/receipt.html', {
        'voter': voter,
        'vote': vote,
        'election': election
    })


def receipt_pdf(request):
    voter_id = request.session.get('voter_id')
    voter = Voter.objects.get(voter_id=voter_id)
    vote = Vote.objects.get(voter=voter)
    election = Election.objects.get(is_active=True)

    qr_image = generate_qr(f"Receipt:{vote.receipt_id}|Voter:{voter.voter_id}")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vote_receipt_{vote.receipt_id}.pdf"'

    p = canvas.Canvas(response, pagesize=(400, 600))
    p.setFont("Helvetica", 12)

    p.drawString(50, 550, "🗳️ Online Voting Receipt")
    p.drawString(50, 520, f"Name: {voter.full_name}")
    p.drawString(50, 500, f"Voter ID: {voter.voter_id}")
    p.drawString(50, 480, f"Party: {vote.party.name}")
    p.drawString(50, 460, f"Election: {election.name}")
    p.drawString(50, 440, f"Receipt ID: {vote.receipt_id}")
    p.drawString(50, 420, f"Date & Time: {vote.voted_at.strftime('%d %b %Y, %I:%M %p')}")

    # Draw QR code
    p.drawImage(qr_image, 50, 250, width=120, height=120)

    p.showPage()
    p.save()
    return response
def generate_qr(data):
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)

# ----------------------------
# 6️⃣ Results
# ----------------------------
def results_view(request):
    data = (
        Vote.objects
        .values('party__name')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    return JsonResponse(list(data), safe=False)


# ----------------------------
# 7️⃣ Logout
# ----------------------------
def logout_view(request):
    request.session.flush()
    
    return redirect('voter_id')


def election_page(request):
    return render(request, 'voting/election.html')
def voting_booth(request):
    voter_id = request.session.get('voter_id')
    if not voter_id:
        messages.error(request, "Please login or enter your Voter ID first.")
        return redirect('voter-id')

    voter = get_object_or_404(Voter, voter_id=voter_id)

    if voter.has_voted:
        return redirect('receipt')

    parties = Party.objects.filter(constituency=voter.constituency)

    if request.method == "POST":
        party_id = request.POST.get("party_id")

        try:
            party = Party.objects.get(id=party_id)
        except Party.DoesNotExist:
            messages.error(request, "Selected party does not exist.")
            return redirect('voting_booth')

        vote = Vote.objects.create(voter=voter, party=party)

        voter.has_voted = True
        voter.save()

        request.session['receipt_id'] = str(vote.receipt_id)

        return redirect('receipt')

    return render(request, 'voting/parties.html', {
        'parties': parties,
        'voter': voter
    })

