from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from New_Backend import settings

def send_case_back_to_pending_email(user_email, reporter_name, case_id, previous_status, reason):
    subject = f"Your Case {case_id} is Back to Pending Review"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user_email]

    text_content = f"""
    Dear {reporter_name},

    Your case with Case ID: {case_id} has been moved from {previous_status} status back to Pending.

    Reason: {reason}

    Our admin team will review your case again and update you shortly.

    Regards,
    Chhaya Foundation Team
    """

    html_content = render_to_string('emails/case_back_to_pending.html', {
        'reporter_name': reporter_name,
        'case_id': case_id,
        'previous_status': previous_status,
        'reason': reason
    })

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()