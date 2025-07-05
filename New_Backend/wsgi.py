"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'New_Backend.settings')

application = get_wsgi_application()
