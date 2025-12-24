from django.core.mail import EmailMessage

def send_receipt_email(email, pdf):
    mail = EmailMessage(
        subject="Your Vote Receipt",
        body="Thank you for voting. Your receipt is attached.",
        to=[email]
    )
    mail.attach('vote_receipt.pdf', pdf, 'application/pdf')
    mail.send()
