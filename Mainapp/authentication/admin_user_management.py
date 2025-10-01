"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status, generics
from django.db.models import Q
from django.utils.timezone import now

from django.core.mail import send_mail
from django.conf import settings

from Mainapp.all_paginations.users_pagination import AdminUserPagination
from Mainapp.authentication.auth_serializer import User, UserSerializer

from django.db.models import Q

import logging
logger = logging.getLogger(__name__)

class AdminUserApprovalView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = AdminUserPagination
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        logger.info(f"Admin user approval view accessed by user: {self.request.user}")
        queryset = User.objects.order_by('id')
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        email_id = self.request.query_params.get("email_id")
        phone_no = self.request.query_params.get("phone_no")
        user_type = self.request.query_params.get("user_type")
        search_query = self.request.query_params.get("search")
        logger.debug(f"Query parameters - first_name: {first_name}, last_name: {last_name}, "
                     f"email_id: {email_id}, phone_no: {phone_no}, user_type: {user_type}, "
                     f"search: {search_query}")

        if first_name:
            logger.debug(f"Filtered by first_name: {first_name}")
            queryset = queryset.filter(first_name__icontains=first_name)
        if last_name:
            logger.debug(f"Filtered by last_name: {last_name}")
            queryset = queryset.filter(last_name__icontains=last_name)
        if email_id:
            logger.debug(f"Filtered by email_id: {email_id}")
            queryset = queryset.filter(email_id__icontains=email_id)
        if phone_no:
            logger.debug(f"Filtered by phone_no: {phone_no}")
            queryset = queryset.filter(phone_no__icontains=phone_no)
        if user_type:
            logger.debug(f"Filtered by user_type: {user_type}")
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
            logger.debug(f"Applied general search filter: {search_query}")
        logger.info(f"Final queryset count: {queryset.count()}")
        return queryset

    def list(self, request, *args, **kwargs):
        logger.info(f"List method called by user: {request.user}")
        queryset = self.filter_queryset(self.get_queryset())

        # Count for each status (respects all filters)
        counts = {
            "hold": queryset.filter(status=User.StatusChoices.HOLD).count(),
            "approved": queryset.filter(status=User.StatusChoices.ACTIVE).count(),
            "rejected": queryset.filter(status=User.StatusChoices.REJECTED).count()
        }
        logger.debug(
            f"Status counts - Hold: {counts['hold']}, Approved: {counts['approved']}, Rejected: {counts['rejected']}")

        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)
        logger.info("Successfully prepared response with paginated data")

        return Response({
            "counts": counts,
            "data": self.paginator.get_paginated_response(serializer.data).data
        }, status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        logger.info(f"PATCH request for user ID: {user_id} by user: {request.user}")
        try:
            user = User.objects.get(id=user_id)
            logger.debug(f"Found user: {user.email_id} (ID: {user.id})")
            # Only admins can update the user
            if not request.user.is_authenticated or not request.user.is_staff:
                logger.warning(f"Unauthorized access attempt by user: {request.user}")
                return Response({"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)

            action = request.data.get("action")
            logger.debug(f"Action requested: {action}")

            if action == "approve":
                user.status = User.StatusChoices.ACTIVE
                logger.info(f"Approving user: {user.email_id}")
                self.send_status_change_email(user, "approved")
            elif action == "reject":
                user.status = User.StatusChoices.REJECTED
                logger.info(f"Rejecting user: {user.email_id}")
                self.send_status_change_email(user, "rejected")
            elif action == "hold":
                logger.info(f"Putting user on hold: {user.email_id}")
                user.status = User.StatusChoices.HOLD
            else:
                logger.warning(f"Invalid action requested: {action}")
                return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

            user.status_updated_by = request.user
            user.status_updated_at = now()
            logger.debug(f"Status updated by: {user.status_updated_by}, at: {user.status_updated_at}")
            print("updated by",user.status_updated_by)
            user.save()
            logger.info(f"User {action} successfully: {user.email_id}")
            return Response({"message": f"User {action}d successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Unexpected error in PATCH method: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def send_status_change_email(self, user, action):
        logger.info(f"Preparing to send {action} email to user: {user.email_id}")
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
            logger.debug(f"Sending {action} email to: {user.email_id}")
            result =send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email_id],
                fail_silently=False
            )
            logger.info(f"Status change email sent successfully to {user.email_id}. Result: {result}")

        except Exception as e:
            logger.error(f"Error sending email to {user.email_id}: {str(e)}")
            print(f"Error sending email: {str(e)}")


class StatusUserView(AdminUserApprovalView):
    status_filter = None

    def get_queryset(self):
        logger.info(f"StatusUserView accessed for status: {self.status_filter}")
        queryset = super().get_queryset()
        if self.status_filter:
            queryset = queryset.filter(status=self.status_filter)
            logger.debug(f"Filtered by status: {self.status_filter}, count: {queryset.count()}")
        return queryset.order_by('-updated_at')

class ApprovedUsersView(StatusUserView):
    status_filter = User.StatusChoices.ACTIVE


class HoldUsersView(StatusUserView):
    status_filter = User.StatusChoices.HOLD


class RejectedUsersView(StatusUserView):
    status_filter = User.StatusChoices.REJECTED