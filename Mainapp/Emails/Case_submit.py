"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""






from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

import logging
logger = logging.getLogger(__name__)
# to send the mail to user for submitted case
def send_submission_email(user_email,reporter_name, full_name, case_id,type, submitted_at):
    logger.info(f"Preparing to send case submission email for case ID: {case_id} to {user_email}")
    logger.debug(f"Email parameters - Reporter: {reporter_name}, Full Name: {full_name}, "
                 f"Case ID: {case_id}, Type: {type}, Submitted At: {submitted_at}")

    subject = f"Case Submission Successful - {case_id}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user_email]
    logger.debug(f"Email details - Subject: {subject}, From: {from_email}, To: {to_email}")


    html_content = render_to_string("emails/submission_success.html", {
        "reporter_name":reporter_name,
        "full_name": full_name,
        "case_id": case_id,
        "type":type,
        "submitted_at": submitted_at
    })

    msg = EmailMultiAlternatives(subject, "", from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
