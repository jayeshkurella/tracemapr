"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework import status, generics
from django.db.models import Q
from django.utils.timezone import now

from django.core.mail import send_mail
from django.conf import settings

from Mainapp.all_paginations.users_pagination import AdminUserPagination
from Mainapp.authentication.auth_serializer import User, UserSerializer

from django.db.models import Q


class AdminUserApprovalView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = AdminUserPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = User.objects.order_by('id')
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        email_id = self.request.query_params.get("email_id")
        phone_no = self.request.query_params.get("phone_no")
        user_type = self.request.query_params.get("user_type")
        search_query = self.request.query_params.get("search")


        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)
        if email_id:
            queryset = queryset.filter(email_id__icontains=email_id)
        if phone_no:
            queryset = queryset.filter(phone_no__icontains=phone_no)
        if user_type:
            queryset = queryset.filter(user_type__iexact=user_type)

        # Optional: General search (if you still want this)
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email_id__icontains=search_query) |
                Q(phone_no__icontains=search_query) |
                Q(user_type__icontains=search_query)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Count for each status (respects all filters)
        counts = {
            "hold": queryset.filter(status=User.StatusChoices.HOLD).count(),
            "approved": queryset.filter(status=User.StatusChoices.ACTIVE).count(),
            "rejected": queryset.filter(status=User.StatusChoices.REJECTED).count()
        }

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)

        return Response({
            "counts": counts,
            "data": self.paginator.get_paginated_response(serializer.data).data
        }, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            # Only admins can update the user
            if not request.user.is_authenticated or not request.user.is_staff:
                return Response({"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)

            action = request.data.get("action")

            if action == "approve":
                user.status = User.StatusChoices.ACTIVE
                self.send_status_change_email(user, "approved")
            elif action == "reject":
                user.status = User.StatusChoices.REJECTED
                self.send_status_change_email(user, "rejected")
            elif action == "hold":
                user.status = User.StatusChoices.HOLD
            else:
                return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

            user.status_updated_by = request.user
            user.status_updated_at = now()
            print("updated by",user.status_updated_by)
            user.save()
            return Response({"message": f"User {action}d successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def send_status_change_email(self, user, action):
        """Sends an email notification after user status change"""
        subject = ""
        message = ""

        if action == "approved":
            subject = "Your Account has been Approved"
            message = (
                f"Hello {user.first_name},\n\n"
                "Your account has been approved. You can now log in and start using our services.\n\n"
                "Thank you for your patience and welcome aboard!\n\n"
                "Best regards,\nThe Team"
            )
        elif action == "rejected":
            subject = "Your Account has been Rejected"
            message = (
                f"Hello {user.first_name},\n\n"
                "We regret to inform you that your account request was not approved.\n\n"
                "Best regards,\nThe Team"
            )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email_id],
                fail_silently=False
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")


class StatusUserView(AdminUserApprovalView):
    status_filter = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.status_filter:
            queryset = queryset.filter(status=self.status_filter)
        return queryset.order_by('-updated_at')

class ApprovedUsersView(StatusUserView):
    status_filter = User.StatusChoices.ACTIVE


class HoldUsersView(StatusUserView):
    status_filter = User.StatusChoices.HOLD


class RejectedUsersView(StatusUserView):
    status_filter = User.StatusChoices.REJECTED
