
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework import viewsets ,permissions
from rest_framework.response import Response

from Mainapp.Serializers.change_log import ChangeLogSerializer
from ..models import ChangeLog

class IsAuthenticatedOrReadOnlyForChangeLog(permissions.BasePermission):
    """
    Custom permission: Allow unrestricted GET (safe) requests,
    but require authentication for others.
    """
    def has_permission(self, request, view):
        # Allow all safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for other methods
        return request.user and request.user.is_authenticated

class ChangeLogViewSet(viewsets.ModelViewSet):
    queryset = ChangeLog.objects.all().order_by('-date', '-id')
    serializer_class = ChangeLogSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForChangeLog]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Log deleted successfully"}, status=204)
