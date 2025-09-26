"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""





from django.core.mail import send_mail
import traceback

from New_Backend import settings
import logging
logger = logging.getLogger(__name__)

def send_welcome_email(full_name, email_id):
    logger.info(f"Preparing to send welcome email to: {email_id}")
    logger.debug(f"Email parameters - Full Name: {full_name}, Email: {email_id}")
    try:
        subject = "Welcome to Our Platform"
        message = (
            f"Hi {full_name},\n\n"
            "Thank you for registering with us.\n"
            "Your account is currently under review and will be activated once approved by the admin.\n\n"
            "Regards,\nChhaya Foundation Team"
        )
        logger.debug(f"Email content - Subject: {subject}, Message length: {len(message)} characters")
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_id],
            fail_silently=False
        )
        logger.info(f"Welcome email sent successfully to {email_id}. Send result: {result}")
        print(f"[EMAIL SENT] To: {email_id}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"[EMAIL ERROR] Failed to send email to {email_id}")
        print(traceback.format_exc())
