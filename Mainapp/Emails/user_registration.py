"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""





from django.core.mail import send_mail
import traceback

from New_Backend import settings


def send_welcome_email(full_name, email_id):
    try:
        subject = "Welcome to Our Platform"
        message = (
            f"Hi {full_name},\n\n"
            "Thank you for registering with us.\n"
            "Your account is currently under review and will be activated once approved by the admin.\n\n"
            "Regards,\nChhaya Foundation Team"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_id],
            fail_silently=False
        )
        print(f"[EMAIL SENT] To: {email_id}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {email_id}")
        print(traceback.format_exc())
