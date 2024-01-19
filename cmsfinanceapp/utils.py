# utils.py
import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=4):
    """Generate a random OTP of the specified length."""
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def send_otp_email(email, otp):
    """Send OTP to the specified email address."""
    subject = 'Your OTP for Verification'
    message = f'''Your OTP is:{otp}. Please don't share it with any one.'''
    print(otp)
    from_email = settings.EMAIL_HOST_USER  # Update with your SMTP email
    send_mail(subject, message, from_email, [email])
