from rest_framework.permissions import BasePermission
from .utils import has_feature_access

class HasFeaturePermission(BasePermission):
    """
    DRF permission to check feature-based access.
    """

    def __init__(self, feature_code):
        self.feature_code = feature_code

    def has_permission(self, request, view):
        return has_feature_access(request.user, self.feature_code)
