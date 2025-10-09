
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

# from rest_framework.permissions import BasePermission
#
# # ----------------------------
# # Feature definitions
# # ----------------------------
# class FeatureChoices:
#     VIEW_DASHBOARD = "view_dashboard"
#     SUBMIT_REPORT = "submit_report"
#     VIEW_REPORT = "view_report"
#     EDIT_REPORT = "edit_report"
#     APPROVE_REPORT = "approve_report"
#     VIEW_AI_MATCH = "view_ai_match"
#     MANAGE_HOSPITAL = "manage_hospital"
#     APPROVE_USER = "approve_user"
#
# # ----------------------------
# # Role -> allowed features
# # ----------------------------
# # Important: police_station intentionally does NOT include MANAGE_HOSPITAL
# ROLE_PERMISSIONS = {
#     "admin": [
#         FeatureChoices.VIEW_DASHBOARD,
#         FeatureChoices.SUBMIT_REPORT,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.EDIT_REPORT,
#         FeatureChoices.APPROVE_REPORT,
#         FeatureChoices.VIEW_AI_MATCH,
#         FeatureChoices.MANAGE_HOSPITAL,
#         FeatureChoices.APPROVE_USER,
#     ],
#     "reporting_person": [
#         FeatureChoices.SUBMIT_REPORT,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.VIEW_AI_MATCH,
#     ],
#     "volunteer": [
#         FeatureChoices.SUBMIT_REPORT,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.VIEW_AI_MATCH,
#     ],
#     "family": [
#         FeatureChoices.SUBMIT_REPORT,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.VIEW_AI_MATCH,
#     ],
#     "police_station": [
#         # intentionally exclude FeatureChoices.MANAGE_HOSPITAL
#         FeatureChoices.VIEW_DASHBOARD,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.VIEW_AI_MATCH,
#     ],
#     "medical_staff": [
#         FeatureChoices.VIEW_DASHBOARD,
#         FeatureChoices.VIEW_REPORT,
#         FeatureChoices.EDIT_REPORT,
#         FeatureChoices.MANAGE_HOSPITAL,  # medical staff allowed
#         FeatureChoices.VIEW_AI_MATCH,
#     ],
#     # additional roles if any...
# }
#
# # ----------------------------
# # Helper function
# # ----------------------------
# def user_has_permission(user, feature: str) -> bool:
#     """
#     Returns True if the user has the specified feature permission.
#     Admin always allowed.
#     """
#     if not user or not getattr(user, "is_authenticated", False):
#         return False
#
#     # Admin by user_type gets everything (you already use is_superuser too)
#     if getattr(user, "user_type", None) == "admin" or getattr(user, "is_superuser", False):
#         return True
#
#     allowed = ROLE_PERMISSIONS.get(getattr(user, "user_type", ""), [])
#     return feature in allowed
#
# # ----------------------------
# # DRF permission class
# # ----------------------------
# class HasFeaturePermission(BasePermission):
#     """
#     DRF permission that checks for a feature required by the view.
#     The view can define one of:
#       - view.required_feature (str): single feature
#       - view.feature_map (dict): mapping of viewset actions -> feature, e.g. {'create': 'manage_hospital'}
#     If neither exists, permission grants access.
#     """
#
#     def has_permission(self, request, view):
#         # Admin / superuser bypass (fast path)
#         if request.user and getattr(request.user, "is_superuser", False):
#             return True
#
#         # Try to pick a feature from view.feature_map using view.action (for viewsets)
#         feature = None
#         action = getattr(view, "action", None)
#         feature_map = getattr(view, "feature_map", None)
#         if feature_map and action:
#             feature = feature_map.get(action)
#
#         # fallback to view.required_feature
#         if not feature:
#             feature = getattr(view, "required_feature", None)
#
#         # if view does not require a feature, allow access
#         if not feature:
#             return True
#
#         # finally check mapping
#         return user_has_permission(request.user, feature)