import random
import qrcode
import base64
from io import BytesIO
from django.utils import timezone
from datetime import timedelta


OTP_EXPIRY = 5  # minutes


def generate_otp():
    return str(random.randint(100000, 999999))


def generate_qr(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def otp_valid(voter):
    if not voter.otp_time:
        return False

    return timezone.now() - voter.otp_time <= timedelta(minutes=OTP_EXPIRY)
