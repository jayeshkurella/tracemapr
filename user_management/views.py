from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from Mainapp.models.person import Person
from Mainapp.models.user import User   # import your User model

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