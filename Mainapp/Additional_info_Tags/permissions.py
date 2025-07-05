"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from Mainapp.access_permision import AllUserAccess, IsAdminUser

class CastePermission(BasePermission):
    """
    Custom permission:
    - Allows GET and POST for users that pass AllUserAccess check.
    - Allows DELETE only for admin users.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method == 'POST':
            # Allow GET and POST for users passing AllUserAccess
            return AllUserAccess().has_permission(request, view)

        if request.method == 'DELETE':
            # Allow DELETE only for admin
            return IsAdminUser().has_permission(request, view)

        return False
