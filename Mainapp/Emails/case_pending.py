"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""



from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from New_Backend import settings

import logging
logger = logging.getLogger(__name__)

def send_case_back_to_pending_email(user_email, reporter_name, case_id, previous_status, reason):
    logger.info(f"Preparing to send case hold email for case ID: {case_id} to {user_email}")
    logger.debug(f"Email parameters - Reporter: {reporter_name}, Case ID: {case_id}, Reason: {reason}")

    subject = f"Your Case {case_id} is Back to Pending Review"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user_email]
    logger.debug(f"Email details - Subject: {subject}, From: {from_email}, To: {to_email}")


    text_content = f"""
    Dear {reporter_name},

    Your case with Case ID: {case_id} has been moved from {previous_status} status back to Pending.

    Reason: {reason}

    Our admin team will review your case again and update you shortly.

    Regards,
    Chhaya Foundation Team
    """

    logger.debug("Plain text email content generated")

    html_content = render_to_string('emails/case_back_to_pending.html', {
        'reporter_name': reporter_name,
        'case_id': case_id,
        'previous_status': previous_status,
        'reason': reason
    })

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()