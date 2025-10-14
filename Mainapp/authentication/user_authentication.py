import threading
import uuid
from random import randint

from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail

from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth_serializer import UserSerializer, UserProfileUpdateSerializer
from django.conf import settings

from .utils import get_client_info
from ..Emails.user_registration import send_welcome_email
from ..models import User

from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
import logging
from user_management.models import Feature, UserFeatureAccess
logger = logging.getLogger(__name__)



class UserListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Only logged-in users can view

    def get(self, request, *args, **kwargs):
        users = User.objects.all().order_by("-id")   # latest users first
        serializer = UserSerializer(users, many=True)
        return Response({"users": serializer.data})

class AuthAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_user_data(self, user):
        """Return serialized user data"""
        return UserSerializer(user).data

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    # def get(self, request, reset_token=None):
    #     if reset_token:
    #         user = User.objects.filter(reset_token=reset_token).first()
    #         if not user or not user.is_reset_token_valid():
    #             return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)
    #         return Response({"message": "Valid token. Proceed with password reset."}, status=status.HTTP_200_OK)
    #     return Response({"error": "Reset token required"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        return self.update_profile(request)

    def post(self, request, reset_token=None):
        action = request.data.get("action")

        if action == "register":
            return self.register_user(request)
        elif action == "login":
            return self.login_user(request)
        elif action == "guest_login":
            return self.guest_login(request)
        elif action == "logout":
            return self.logout_user(request)
        elif action == "forgot-password":
            return self.forgot_password(request)
        elif action == "reset-password":
            return self.reset_password(request)
        elif action == "change-password":
            return self.change_password(request)
        elif action == "delete_profile":
            return self.delete_profile(request)
        elif action == "google_login":
            return self.google_login(request)
        elif action == "get_profile":
            return self.get_profile(request)
        elif action == "update_role":
            return self.update_role(request)

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    # =================== AUTH FUNCTIONS =================== #

    def register_user(self, request):
        required_fields = ["email_id", "phone_no", "password", "password2", "first_name", "last_name"]
        if not all(request.data.get(field) for field in required_fields):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        email_id = request.data["email_id"].lower()
        phone_no = request.data["phone_no"]
        password = request.data["password"]
        password2 = request.data["password2"]
        first_name = request.data["first_name"]
        last_name = request.data["last_name"]
        country_code = request.data.get("country_code", "")
        user_type = request.data.get("user_type", "")
        sub_user_type = request.data.get("sub_user_type", "")
        is_consent = request.data.get("is_consent", False)

        if password != password2:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email_id=email_id).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(phone_no=phone_no).exists():
            return Response({"error": "Phone number already used"}, status=status.HTTP_400_BAD_REQUEST)

        ip, user_agent = get_client_info(request)
        user = User.objects.create(
            email_id=email_id,
            phone_no=phone_no,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            country_code=country_code,
            user_type=user_type,
            sub_user_type=sub_user_type,
            status=User.StatusChoices.HOLD,
            is_consent=is_consent,
            last_login_ip=ip,
            last_login_user_agent=user_agent
        )
        full_name = f"{first_name} {last_name}".strip()
        threading.Thread(target=send_welcome_email, args=(full_name, email_id), daemon=True).start()

        return Response({
            "message": "User registered successfully. Awaiting admin approval.",
            "user": self.get_user_data(user)
        }, status=status.HTTP_201_CREATED)

    def login_user(self, request):
        email_id = request.data.get("email_id", "").strip().lower()
        password = request.data.get("password")
        logger.info(f"Login attempt for email: {email_id}")
        logger.info(f"Login attempt for password: {password}")

        if not (email_id and password):
            logger.warning("Login failed: Email and password are required")
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email_id=email_id).first()
        if not user:
            logger.warning(f"No user found with email: {email_id}")
            return Response({"error": "No account found with this email."}, status=status.HTTP_400_BAD_REQUEST)
        logger.debug(f"User found: {user.id}, Status: {user.status}")
        if user.status != User.StatusChoices.ACTIVE:
            logger.warning(f"Login rejected for user {user.id}: Account not approved. Status: {user.status}")
            return Response({"error": "Your account is not approved yet."}, status=status.HTTP_403_FORBIDDEN)

        if check_password(password, user.password):
            ip, user_agent = get_client_info(request)
            user.last_login_ip = ip
            user.last_login_user_agent = user_agent
            user.save(update_fields=['last_login_ip', 'last_login_user_agent'])

            tokens = self.get_tokens_for_user(user)
            logger.info(f"Login successful for user: {user.id}")
            logger.debug(f"Generated tokens for user: {user.id}")

            return Response({
                "message": "Login successful",
                "tokens": tokens,
                "user": self.get_user_data(user)
            }, status=status.HTTP_200_OK)
        logger.warning(f"Login failed: Incorrect password for user: {user.id}")
        return Response({"error": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

    def google_login(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            id_info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)

            google_id = id_info["sub"]
            email = id_info.get("email", "")
            name = id_info.get("name", "")
            picture = id_info.get("picture", "")

            user = User.objects.filter(google_id=google_id).first()
            if not user and email:
                user = User.objects.filter(email_id=email).first()

            if not user:
                user = User.objects.create(
                    google_id=google_id,
                    email_id=email,
                    first_name=name.split()[0] if name else "",
                    last_name=" ".join(name.split()[1:]) if name else "",
                    user_type=request.data.get("user_type", User.UserTypeChoices.REPORTING),
                    sub_user_type=request.data.get("sub_user_type", ""),
                    picture=picture,
                    status=User.StatusChoices.HOLD,
                )

            if user.status != User.StatusChoices.ACTIVE:
                return Response({"error": "Account pending admin approval."}, status=status.HTTP_403_FORBIDDEN)

            tokens = self.get_tokens_for_user(user)
            return Response({
                "message": "Google login successful",
                "tokens": tokens,
                "user": self.get_user_data(user)
            }, status=200)

        except Exception as e:
            return Response({"error": f"Google login failed: {str(e)}"}, status=400)

    def generate_dummy_phone(self):
        while True:
            phone = f"9{randint(100000000, 999999999)}"
            if not User.objects.filter(phone_no=phone).exists():
                return phone

    def guest_login(self, request):
        guest_user_id = request.session.get('guest_user_id')
        if guest_user_id:
            # Convert string back to UUID when querying
            from uuid import UUID
            user = User.objects.filter(id=UUID(guest_user_id), user_type='anonymous').first()
            if user:
                tokens = self.get_tokens_for_user(user)
                return Response({
                    "message": "Guest login successful",
                    "tokens": tokens,
                    "user": self.get_user_data(user)
                }, status=200)

        random_str = get_random_string(8)
        username = f"guest_{random_str}"
        email = f"{username}@example.com"
        password = get_random_string(12)
        dummy_phone = self.generate_dummy_phone()  # make sure phone is unique
        ip, user_agent = get_client_info(request)

        guest_user = User.objects.create(
            email_id=email,
            phone_no=dummy_phone,
            password=make_password(password),
            first_name="Guest",
            last_name=f"User_{random_str}",
            user_type="anonymous",
            status=User.StatusChoices.ACTIVE,
            last_login_ip=ip,
            last_login_user_agent=user_agent
        )

        # **Convert UUID to string for session**
        request.session['guest_user_id'] = str(guest_user.id)

        tokens = self.get_tokens_for_user(guest_user)

        return Response({
            "message": "Guest login successful",
            "tokens": tokens,
            "user": self.get_user_data(guest_user)
        }, status=200)

    def logout_user(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def forgot_password(self, request):
        email_id = request.data.get("email_id")
        user = User.objects.filter(email_id=email_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.reset_token_created_at = timezone.now()
        user.save()

        # reset_url = f"https://beta.tracemapr.com/authentication/reset-password/{reset_token}"
        reset_url = f"https://tracemapr.com/authentication/reset-password/{reset_token}"
        # reset_url = f"https://http://127.0.0.1:8000/reset-password/{reset_token}"
        send_mail("Password Reset Request",
                  f"Click the link to reset your password: {reset_url}",
                  settings.DEFAULT_FROM_EMAIL, [email_id])

        return Response({"message": "Password reset link sent.", "reset_token": reset_token}, status=200)

    def reset_password(self, request):
        reset_token = request.data.get("token")
        new_password = request.data.get("new_password")

        user = User.objects.filter(reset_token=reset_token).first()
        if not user or not user.is_reset_token_valid():
            return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_created_at = None
        user.save()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

    def change_password(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not check_password(old_password, request.user.password):
            return Response({"error": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)



    def get_profile(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        pk = request.data.get("pk")
        if not pk:
            return Response({"error": "User ID required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileUpdateSerializer(user)
        return Response({"message": "Profile fetched", "user": serializer.data}, status=200)

    def update_profile(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        data = request.data.copy()

        remove_image = request.data.get('remove_image') == 'true'
        if remove_image and user.profile_image_upload:
            user.profile_image_upload.delete(save=False)
            user.profile_image_upload = None
            user.save(update_fields=['profile_image_upload'])
        elif 'profile_image' in request.FILES:
            if user.profile_image_upload:
                user.profile_image_upload.delete(save=False)
            data['profile_image_upload'] = request.FILES['profile_image']

        new_email = request.data.get('email_id')
        new_phone_no = request.data.get('phone_no')
        if new_email and new_email != user.email_id and User.objects.filter(email_id=new_email).exists():
            return Response({"error": "Email already in use"}, status=400)
        if new_phone_no and new_phone_no != user.phone_no and User.objects.filter(phone_no=new_phone_no).exists():
            return Response({"error": "Phone number already in use"}, status=400)

        restricted_fields = ["status", "password", "is_superuser", "is_staff", "is_consent", "google_id"]
        attempted_changes = [f for f in restricted_fields if f in request.data]
        if attempted_changes:
            return Response({"error": f"Cannot update fields: {', '.join(attempted_changes)}"}, status=403)

        serializer = UserProfileUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = {"message": "Profile updated", "user": serializer.data}
            if remove_image:
                response_data["user"]["profile_image_upload"] = None
            return Response(response_data, status=200)
        return Response({"error": serializer.errors}, status=400)

    def delete_profile(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        password = request.data.get("password")
        if password and not check_password(password, request.user.password):
            return Response({"error": "Incorrect password"}, status=400)

        user = request.user
        email = user.email_id
        full_name = f"{user.first_name} {user.last_name}".strip()
        user.delete()

        try:
            send_mail(
                "Account Deletion Confirmation",
                f"Hello {full_name or 'User'}, your account has been deleted.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
        except Exception:
            pass

        return Response({"message": "Account deleted"}, status=200)

    def update_role(self, request):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response(
                {"error": "Admin privileges required"},
                status=status.HTTP_403_FORBIDDEN
            )

        pk = request.data.get("pk")
        user_type = request.data.get("user_type")
        sub_user_type = request.data.get("sub_user_type", "")
        status_value = request.data.get("status")  # active/inactive/hold/rejected
        features_data = request.data.get("features", [])  # [{ "feature_id": 1, "is_allowed": true }]

        if not pk:
            return Response({"error": "User ID required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update role/subrole/status
        if user_type:
            user.user_type = user_type
        if sub_user_type:
            user.sub_user_type = sub_user_type
        if status_value:
            user.status = status_value
        user.save()

        # ✅ Update feature access (per-user overrides)
        if isinstance(features_data, list):
            for f in features_data:
                feature_id = f.get("feature_id")
                is_allowed = f.get("is_allowed", False)
                try:
                    feature = Feature.objects.get(id=feature_id)
                    UserFeatureAccess.objects.update_or_create(
                        user=user,
                        feature=feature,
                        defaults={"is_allowed": is_allowed}
                    )
                except Feature.DoesNotExist:
                    continue

        return Response({
            "message": "User role/status/features updated successfully",
            "user": self.get_user_data(user)
        }, status=status.HTTP_200_OK)


