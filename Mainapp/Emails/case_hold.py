"""
Created By : Sanket Lodhe
Created Date : AUG 2025
"""




from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from New_Backend import settings

def send_case_to_hold_email(user_email, reporter_name, case_id, reason):
    subject = f"Your Case {case_id} is on Hold."
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user_email]

    text_content = f"""
    Dear {reporter_name},

    Your case with Case ID: {case_id} is on hold.

    Reason: {reason}

    Our admin team will review your case again and update you shortly.

    Regards,
    Chhaya Foundation Team
    """

    html_content = render_to_string('emails/case_move_to_hold.html', {
        'reporter_name': reporter_name,
        'case_id': case_id,
        'reason': reason
    })

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()