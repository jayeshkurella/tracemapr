"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""



from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from New_Backend import settings


def send_case_approval_email(user_email,reporter_name, full_name, case_id,type, approved_at):
    subject = f"Your Case {case_id} Has Been Approved"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user_email]

    # Plain text version (for email clients that don't support HTML)
    text_content = f"""
    Dear {reporter_name},

    We are pleased to inform you that your case with Case ID: {case_id} 
    has been approved by our admin team.

    You can now log in to the portal and track further updates.

    Approval Date: {approved_at}

    Thank you for your patience and trust.

    Regards,
    Case Management Team
    """

    # HTML version (styled)
    html_content = render_to_string('emails/case_approval_email.html', {
        "reporter_name":reporter_name,
        "full_name": full_name,
        "case_id": case_id,
        "type":type,
        'approved_at': approved_at
    })

    # Create and send email
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
