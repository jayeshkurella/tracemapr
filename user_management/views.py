from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from Mainapp.models.person import Person
from Mainapp.models.user import User   # import your User model
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from .models import Feature, RoleFeatureAccess
from .serializers import FeatureSerializer, RoleFeatureAccessSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    """
    API to manage Features (CRUD).
    Only Admins can manage features.
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAdminUser]


class RoleFeatureAccessViewSet(viewsets.ModelViewSet):
    """
    API to manage Role–Feature Access mapping.
    Only Admins can manage mappings.
    """
    queryset = RoleFeatureAccess.objects.all()
    serializer_class = RoleFeatureAccessSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"], url_path="by-role/(?P<role>[^/.]+)")
    def get_by_role(self, request, role=None):
        """
        Get all features with access status for a specific role.
        """
        features = Feature.objects.all()
        role_features = RoleFeatureAccess.objects.filter(role=role)

        # Create a mapping of feature_id -> access
        access_map = {rf.feature_id: rf.is_allowed for rf in role_features}

        data = []
        for feature in features:
            data.append({
                "feature_id": feature.id,
                "feature_code": feature.code,
                "feature_name": feature.name,
                "is_allowed": access_map.get(feature.id, False)
            })

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="update-role-access")
    def update_role_access(self, request):
        """
        Bulk update role-feature access.
        Expected payload:
        {
            "role": "reporting_person",
            "features": [
                {"feature_id": 1, "is_allowed": true},
                {"feature_id": 2, "is_allowed": false}
            ]
        }
        """
        role = request.data.get("role")
        features_data = request.data.get("features", [])

        if not role or not isinstance(features_data, list):
            return Response(
                {"error": "Invalid payload"},
                status=status.HTTP_400_BAD_REQUEST
            )

        for f in features_data:
            feature_id = f.get("feature_id")
            is_allowed = f.get("is_allowed", False)
            try:
                feature = Feature.objects.get(id=feature_id)
                RoleFeatureAccess.objects.update_or_create(
                    role=role,
                    feature=feature,
                    defaults={"is_allowed": is_allowed}
                )
            except Feature.DoesNotExist:
                continue

        return Response({"message": f"Access updated for role '{role}'"}, status=status.HTTP_200_OK)

class UserCountAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # only logged-in users can see

    def get(self, request, *args, **kwargs):
        total_users = User.objects.count()
        active_users = User.objects.filter(status=User.StatusChoices.ACTIVE).count()
        pending_users = User.objects.filter(status=User.StatusChoices.PENDING).count()
        hold_users = User.objects.filter(status=User.StatusChoices.HOLD).count()
        rejected_users = User.objects.filter(status=User.StatusChoices.REJECTED).count()

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "hold_users": hold_users,
            "rejected_users": rejected_users
        })
class CaseCountAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_cases = Person.objects.count()

        # Count by type
        missing_cases = Person.objects.filter(type=Person.TypeChoices.MISSING).count()
        unidentified_person_cases = Person.objects.filter(type=Person.TypeChoices.Unidentified_Person).count()
        unidentified_body_cases = Person.objects.filter(type=Person.TypeChoices.Unidnetified_Body).count()

        # Count by status
        pending_cases = Person.objects.filter(case_status='pending').count()
        resolved_cases = Person.objects.filter(case_status='resolved').count()
        matched_cases = Person.objects.filter(case_status='matched').count()

        return Response({
            "total_cases": total_cases,
            "by_type": {
                "missing_person": missing_cases,
                "unidentified_person": unidentified_person_cases,
                "unidentified_body": unidentified_body_cases,
            },
            "by_status": {
                "pending": pending_cases,
                "resolved": resolved_cases,
                "matched": matched_cases,
            }
        })

from .models import UserFeatureAccess
from .serializers import UserFeatureAccessSerializer

class UserFeatureAccessViewSet(viewsets.ModelViewSet):
    """
    Manage per-user feature access (override role defaults).
    """
    queryset = UserFeatureAccess.objects.all()
    serializer_class = UserFeatureAccessSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"], url_path="by-user/(?P<user_id>[^/.]+)")
    def get_by_user(self, request, user_id=None):
        features = Feature.objects.all()
        user_features = UserFeatureAccess.objects.filter(user_id=user_id)

        access_map = {uf.feature_id: uf.is_allowed for uf in user_features}

        data = []
        for feature in features:
            data.append({
                "feature_id": feature.id,
                "feature_code": feature.code,
                "feature_name": feature.name,
                "is_allowed": access_map.get(feature.id, False)
            })

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="update-user-access")
    def update_user_access(self, request):
        """
        Update per-user feature access.
        Payload:
        {
            "user_id": "uuid-here",
            "features": [
                {"feature_id": 1, "is_allowed": true},
                {"feature_id": 2, "is_allowed": false}
            ]
        }
        """
        user_id = request.data.get("user_id")
        features_data = request.data.get("features", [])

        if not user_id or not isinstance(features_data, list):
            return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        for f in features_data:
            feature_id = f.get("feature_id")
            is_allowed = f.get("is_allowed", False)
            try:
                feature = Feature.objects.get(id=feature_id)
                UserFeatureAccess.objects.update_or_create(
                    user_id=user_id,
                    feature=feature,
                    defaults={"is_allowed": is_allowed}
                )
            except Feature.DoesNotExist:
                continue

        return Response({"message": f"Access updated for user {user_id}"}, status=status.HTTP_200_OK)