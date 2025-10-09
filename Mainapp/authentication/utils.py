# utils.py
def get_client_info(request):
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    return ip, user_agent
