
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to Admin users who have full access."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'admin'


class BaseUserPermission(BasePermission):
    """
    Base class for user permissions that automatically allows admin users
    and checks specific user_type for non-admin users.
    """
    user_type = None  # To be overridden by subclasses

    def has_permission(self, request, view):
        # Admin always has permission
        if request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'admin':
            return True

        # Check specific user type for non-admin users
        return request.user.is_authenticated and getattr(request.user, 'user_type', None) == self.user_type


class IsFamilyUser(BaseUserPermission):
    """Allows access to Admin and Family users."""
    user_type = 'family'


class IsOfficerUser(BaseUserPermission):
    """Allows access to Admin and Officer users."""
    user_type = 'officer'


class IsReportingUser(BaseUserPermission):
    """Allows access to Admin and Reporting users."""
    user_type = 'reporting_person'


class IsVolunteerUser(BaseUserPermission):
    """Allows access to Admin and Volunteer users."""
    user_type = 'volunteer'


class IsPoliceStationUser(BaseUserPermission):
    """Allows access to Admin and Police Station users."""
    user_type = 'police_station'


class IsMedicalStaffUser(BaseUserPermission):
    """Allows access to Admin and Medical Staff users."""
    user_type = 'medical_staff'


class AllUserAccess(BasePermission):
    """
    Allows access to Admin and specific user types.
    By default, allows all users if no specific user type is provided.
    Admin always has access regardless of specified types.
    """

    def __init__(self, *allowed_user_types):
        self.allowed_user_types = allowed_user_types or [
            "family", "officer", "reporting_person", "volunteer",
            "police_station", "medical_staff"
        ]

    def has_permission(self, request, view):
        # Admin always has permission
        if request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'admin':
            return True

        # Check if user's type is in allowed types
        return (request.user.is_authenticated and
                getattr(request.user, 'user_type', '') in self.allowed_user_types)