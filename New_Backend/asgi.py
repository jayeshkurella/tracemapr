"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'New_Backend.settings')

application = get_asgi_application()
