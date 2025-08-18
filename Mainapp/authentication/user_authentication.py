"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.utils.timezone import now
from django.utils import timezone

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .auth_serializer import AuthSerializer, UserSerializer, UserProfileUpdateSerializer
from django.contrib.auth import logout
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import random
from rest_framework import status
from django.db.utils import IntegrityError



from django.core.mail import send_mail  # For email functionality (optional)
from django.conf import settings

from ..models import User

class AuthAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    def get_user_data(self, user):
        """Return serialized user data"""
        return UserSerializer(user).data

    def get(self, request, reset_token=None):
        """Handle GET request when user clicks on the reset link"""
        if reset_token:
            user = User.objects.filter(reset_token=reset_token).first()
            if not user or not user.is_reset_token_valid():
                return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Valid token. Proceed with password reset."}, status=status.HTTP_200_OK)
        return Response({"error": "Reset token required"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """Handle PUT requests for profile updates"""
        return self.update_profile(request)

    def post(self, request, reset_token=None):
        action = request.data.get("action")

        #  REGISTER USER
        if action == "register":
            return self.register_user(request)

        # LOGIN USER
        elif action == "login":
            return self.login_user(request)

        #  LOGOUT USER
        elif action == "logout":
            return self.logout_user(request)

        #  FORGOT PASSWORD
        elif action == "forgot-password":
            return self.forgot_password(request)

        #  RESET PASSWORD
        elif action == "reset-password":
            return self.reset_password(request)

        # CHANGE PASSWORD
        elif action == "change-password":
            return self.change_password(request)

        elif action == "delete_profile":
            return self.delete_profile(request)

        elif action == "google_login":
            return self.google_login(request)

        elif action == "get_profile":
            return self.get_profile(request)



        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    # =================== HELPER FUNCTIONS =================== #

    def register_user(self, request):
        """Handles user registration"""
        required_fields = ["email_id", "phone_no", "password", "password2", "first_name", "last_name"]
        if not all(request.data.get(field) for field in required_fields):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        email_id = request.data["email_id"]
        phone_no = request.data["phone_no"]
        password = request.data["password"]
        password2 = request.data["password2"]
        first_name = request.data["first_name"]
        last_name = request.data["last_name"]
        country_code = request.data.get("country_code", "")
        user_type = request.data.get("user_type", "")
        sub_user_type = request.data.get("sub_user_type", "")
        is_consent = request.data.get("is_consent", False)

        # ✅ Check if passwords match
        if password != password2:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check for existing email and phone number
        if User.objects.filter(email_id=email_id).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone_no=phone_no).exists():
            return Response({"error": "Phone number already used"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Create user with status 'hold' (admin approval required)
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
            is_consent=is_consent
        )
        # ✅ Send email notification
        try:
            subject = "Welcome to Our Platform"
            message = (
                f"Hi {first_name},\n\n"
                "Thank you for registering with us.\n"
                "Your account is currently under review and will be activated once approved by the admin.\n\n"
                "Regards,\nSupport Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email_id],
                fail_silently=False
            )
        except Exception as e:
            return Response({
                "message": "User registered successfully, but email sending failed.",
                "error": str(e),
                "user": self.get_user_data(user)
            }, status=status.HTTP_201_CREATED)

        return Response({
            "message": "User registered successfully. Awaiting admin approval.",
            "user": self.get_user_data(user)
        }, status=status.HTTP_201_CREATED)

    def login_user(self, request):
        """Handles user login"""
        email_id = request.data.get("email_id", "").strip().lower()
        password = request.data.get("password")

        if not (email_id and password):
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email_id=email_id).first()
        if not user:
            return Response({"error": "No account found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        if user.status != User.StatusChoices.ACTIVE:
            return Response({"error": "Your account is not approved yet. Please wait for admin approval."}, status=status.HTTP_403_FORBIDDEN)

        if check_password(password, user.password):
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key,
                "user": self.get_user_data(user)
            }, status=status.HTTP_200_OK)

        return Response({"error": "Incorrect password. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

    def google_login(self, request):
        """Handles Google login with ID token"""
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            id_info = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )

            google_id = id_info["sub"]
            email = id_info.get("email", "")
            name = id_info.get("name", "")
            picture = id_info.get("picture", "")
            user_type = request.data.get("user_type")
            sub_user_type = request.data.get("sub_user_type")

            # Check if user exists by Google ID or email
            user = User.objects.filter(google_id=google_id).first()
            if not user and email:
                user = User.objects.filter(email_id=email).first()

            # If user doesn't exist, create a new one
            if not user:
                user = User.objects.create(
                    google_id=google_id,
                    email_id=email,
                    first_name=name.split()[0] if name else "",
                    last_name=" ".join(name.split()[1:]) if name else "",
                    user_type=user_type or User.UserTypeChoices.REPORTING,
                    sub_user_type=sub_user_type or "",
                    picture=picture,
                    status=User.StatusChoices.HOLD,
                    phone_no=None,  # Explicitly set to None instead of empty string
                )

                # Send email notification upon registration (if the account is on hold)
                send_mail(
                    "Account Registration Pending Approval",
                    "Your account has been registered successfully. It is now pending admin approval",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email_id],
                    fail_silently=False,
                )

            else:
                # Update user details if missing
                updated = False
                if not user.google_id:
                    user.google_id = google_id
                    updated = True
                if not user.email_id and email:
                    user.email_id = email
                    updated = True
                if updated:
                    user.save()

            # Check if account is approved
            if user.status != User.StatusChoices.ACTIVE:
                return Response({
                    "error": "User registered successfully.Your account is not approved yet. Please wait for admin approval."
                }, status=status.HTTP_403_FORBIDDEN)

            # Send email notification upon successful approval
            if user.status == User.StatusChoices.ACTIVE:
                send_mail(
                    "Account Approved",
                    "Your account has been successfully approved and activated. You may now log in and access your dashboard.",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email_id],
                    fail_silently=False,
                )

            # Generate or get token
            token_obj, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Google login successful",
                "token": token_obj.key,
                "user": self.get_user_data(user)
            }, status=200)

        except Exception as e:
            return Response({"error": f"Google login failed: {str(e)}"}, status=400)

    def logout_user(self, request):
        """Handles user logout"""
        if request.user.is_authenticated:
            request.user.auth_token.delete()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    def forgot_password(self, request):
        """Handles forgot password functionality"""
        email_id = request.data.get("email_id")
        user = User.objects.filter(email_id=email_id).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.reset_token_created_at = timezone.now()
        user.save()

        # local
        # reset_url = f"http://localhost:4200/authentication/reset-password/{reset_token}"

        # production
        # reset_url = f"https://tracemapr.com/authentication/reset-password/{reset_token}"

        # Testing(beta)
        reset_url = f"https://beta.tracemapr.com/authentication/reset-password/{reset_token}"
        try:
            send_mail(
                "Password Reset Request",
                f"Click the link below to reset your password:\n{reset_url}\nThis link will expire in 05 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [email_id],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                "message": "Token generated but email sending failed.",
                "reset_token": reset_token,
                "error": str(e)
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Password reset link sent to your email.",
            "reset_token": reset_token
        }, status=status.HTTP_200_OK)

    def reset_password(self, request):
        """Handles password reset"""
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
        """Handles password change for authenticated users"""
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
        """Fetch user profile by primary key (pk)"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        pk = request.data.get("pk")
        if not pk:
            return Response({"error": "User ID (pk) is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileUpdateSerializer(user)
        return Response({
            "message": "User profile fetched successfully",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def update_profile(self, request):
        """Handles profile update"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user  # Current user instance
        data = request.data.copy()

        # Handle file upload separately if using multipart/form-data
        if 'profile_image' in request.FILES:
            # Clear old image if exists
            if user.profile_image_upload:
                user.profile_image_upload.delete(save=False)
            # Assign new image
            data['profile_image_upload'] = request.FILES['profile_image']

        #  Validate email and phone uniqueness before updating
        new_email = request.data.get('email_id')
        new_phone_no = request.data.get('phone_no')

        if new_email and new_email != user.email_id and User.objects.filter(email_id=new_email).exists():
            return Response({"error": "Email is already registered with another account"},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_phone_no and new_phone_no != user.phone_no and User.objects.filter(phone_no=new_phone_no).exists():
            return Response({"error": "Phone number is already in use"}, status=status.HTTP_400_BAD_REQUEST)

        #  Prevent users from changing sensitive fields (Return Error)
        restricted_fields = [
            "status", "password",
            "is_superuser", "is_staff", "is_consent", "google_id"
        ]

        attempted_changes = [field for field in restricted_fields if field in request.data]
        if attempted_changes:
            return Response(
                {"error": f"You are not allowed to update the following fields: {', '.join(attempted_changes)}"},
                status=status.HTTP_403_FORBIDDEN
            )

        #  Use Serializer for updating user profile safely
        serializer = UserProfileUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully", "user": serializer.data},
                            status=status.HTTP_200_OK)

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        #  DELETE ACCOUNT

    def delete_profile(self, request):
        """Handles user account deletion with optional password confirmation and email notification"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        #  Optional password confirmation before deletion
        password = request.data.get("password")
        if password and not check_password(password, request.user.password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        #  Retrieve user data before deletion (for response and email)
        user = request.user
        email = user.email_id
        full_name = f"{user.first_name} {user.last_name}".strip()

        # Delete the user account
        user.delete()

        # Send confirmation email after deletion
        try:
            send_mail(
                subject="Account Deletion Confirmation",
                message=f"Hello {full_name or 'User'},\n\nYour account has been successfully deleted. "
                        "If this was not done by you, please contact our support team immediately.\n\n"
                        "Regards,\nThe Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send deletion email: {str(e)}")

        return Response({
            "message": "Account deleted successfully",
        }, status=status.HTTP_200_OK)



"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import threading
import uuid
from django.utils.timezone import now
from django.utils import timezone

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .auth_serializer import AuthSerializer, UserSerializer, UserProfileUpdateSerializer
from django.contrib.auth import logout
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import random
from rest_framework import status
from django.db.utils import IntegrityError



from django.core.mail import send_mail  # For email functionality (optional)
from django.conf import settings

from .utils import get_client_info
from ..Emails.user_registration import send_welcome_email
from ..models import User

class AuthAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    def get_user_data(self, user):
        """Return serialized user data"""
        return UserSerializer(user).data

    def get(self, request, reset_token=None):
        """Handle GET request when user clicks on the reset link"""
        if reset_token:
            user = User.objects.filter(reset_token=reset_token).first()
            if not user or not user.is_reset_token_valid():
                return Response({"error": "Invalid or expired reset token"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Valid token. Proceed with password reset."}, status=status.HTTP_200_OK)
        return Response({"error": "Reset token required"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """Handle PUT requests for profile updates"""
        return self.update_profile(request)

    def post(self, request, reset_token=None):
        action = request.data.get("action")

        #  REGISTER USER
        if action == "register":
            return self.register_user(request)

        # LOGIN USER
        elif action == "login":
            return self.login_user(request)

        #  LOGOUT USER
        elif action == "logout":
            return self.logout_user(request)

        #  FORGOT PASSWORD
        elif action == "forgot-password":
            return self.forgot_password(request)

        #  RESET PASSWORD
        elif action == "reset-password":
            return self.reset_password(request)

        # CHANGE PASSWORD
        elif action == "change-password":
            return self.change_password(request)

        elif action == "delete_profile":
            return self.delete_profile(request)

        elif action == "google_login":
            return self.google_login(request)

        elif action == "get_profile":
            return self.get_profile(request)

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    # =================== HELPER FUNCTIONS =================== #

    def register_user(self, request):
        """Handles user registration"""
        required_fields = ["email_id", "phone_no", "password", "password2", "first_name", "last_name"]
        if not all(request.data.get(field) for field in required_fields):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        email_id = request.data["email_id"]
        phone_no = request.data["phone_no"]
        password = request.data["password"]
        password2 = request.data["password2"]
        first_name = request.data["first_name"]
        last_name = request.data["last_name"]
        country_code = request.data.get("country_code", "")
        user_type = request.data.get("user_type", "")
        sub_user_type = request.data.get("sub_user_type", "")
        is_consent = request.data.get("is_consent", False)

        # Check if passwords match
        if password != password2:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing email and phone number
        if User.objects.filter(email_id=email_id).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone_no=phone_no).exists():
            return Response({"error": "Phone number already used"}, status=status.HTTP_400_BAD_REQUEST)

        #  Create user with status 'hold' (admin approval required)
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
        # Send email notification
        full_name = f"{first_name} {last_name}".strip()
        threading.Thread(
            target=send_welcome_email,
            args=(full_name, email_id), daemon=True
        ).start()

        return Response({
            "message": "User registered successfully. Awaiting admin approval.",
            "user": self.get_user_data(user)
        }, status=status.HTTP_201_CREATED)

    def login_user(self, request):
        """Handles user login"""
        email_id = request.data.get("email_id", "").strip().lower()
        password = request.data.get("password")

        if not (email_id and password):
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email_id=email_id).first()
        if not user:
            return Response({"error": "No account found with this email."}, status=status.HTTP_400_BAD_REQUEST)

        if user.status != User.StatusChoices.ACTIVE:
            return Response({"error": "Your account is not approved yet. Please wait for admin approval."}, status=status.HTTP_403_FORBIDDEN)

        if check_password(password, user.password):
            token, created = Token.objects.get_or_create(user=user)
            ip, user_agent = get_client_info(request)
            user.last_login_ip = ip
            user.last_login_user_agent = user_agent
            user.save(update_fields=['last_login_ip', 'last_login_user_agent'])
            return Response({
                "message": "Login successful",
                "token": token.key,
                "user": self.get_user_data(user)
            }, status=status.HTTP_200_OK)

        return Response({"error": "Incorrect password. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

    def google_login(self, request):
        """Handles Google login with ID token"""
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            id_info = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )

            google_id = id_info["sub"]
            email = id_info.get("email", "")
            name = id_info.get("name", "")
            picture = id_info.get("picture", "")
            user_type = request.data.get("user_type")
            sub_user_type = request.data.get("sub_user_type")

            # Check if user exists by Google ID or email
            user = User.objects.filter(google_id=google_id).first()
            if not user and email:
                user = User.objects.filter(email_id=email).first()

            # If user doesn't exist, create a new one
            if not user:
                user = User.objects.create(
                    google_id=google_id,
                    email_id=email,
                    first_name=name.split()[0] if name else "",
                    last_name=" ".join(name.split()[1:]) if name else "",
                    user_type=user_type or User.UserTypeChoices.REPORTING,
                    sub_user_type=sub_user_type or "",
                    picture=picture,
                    status=User.StatusChoices.HOLD,
                    phone_no=None,
                )

                # Send email notification upon registration (if the account is on hold)
                threading.Thread(
                    target=send_mail,
                    args=(
                        "Account Registration Pending Approval",
                        "Your account has been registered successfully. It is now pending admin approval",
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email_id],
                    ),
                    kwargs={'fail_silently': False}
                ).start()


            else:
                # Update user details if missing
                updated = False
                if not user.google_id:
                    user.google_id = google_id
                    updated = True
                if not user.email_id and email:
                    user.email_id = email
                    updated = True
                if updated:
                    user.save()

            # Check if account is approved
            if user.status != User.StatusChoices.ACTIVE:
                return Response({
                    "error": "User registered successfully.Your account is not approved yet. Please wait for admin approval."
                }, status=status.HTTP_403_FORBIDDEN)

            # Send email notification upon successful approval
            if user.status == User.StatusChoices.ACTIVE:
                threading.Thread(
                    target=send_mail,
                    args=(
                        "Account Approved",
                        "Your account has been successfully approved and activated. You may now log in and access your dashboard.",
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email_id],
                    ),
                    kwargs={'fail_silently': False}
                ).start()

            # Generate or get token
            token_obj, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Google login successful",
                "token": token_obj.key,
                "user": self.get_user_data(user)
            }, status=200)

        except Exception as e:
            return Response({"error": f"Google login failed: {str(e)}"}, status=400)

    def logout_user(self, request):
        """Handles user logout"""
        if request.user.is_authenticated:
            request.user.auth_token.delete()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    def forgot_password(self, request):
        """Handles forgot password functionality"""
        email_id = request.data.get("email_id")
        user = User.objects.filter(email_id=email_id).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.reset_token_created_at = timezone.now()
        user.save()

        # local
        # reset_url = f"http://localhost:4200/authentication/reset-password/{reset_token}"

        # production
        # reset_url = f"https://tracemapr.com/authentication/reset-password/{reset_token}"

        # Testing(beta)
        reset_url = f"https://beta.tracemapr.com/authentication/reset-password/{reset_token}"
        try:
            send_mail(
                "Password Reset Request",
                f"Click the link below to reset your password:\n{reset_url}\nThis link will expire in 05 minutes.",
                settings.DEFAULT_FROM_EMAIL,
                [email_id],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                "message": "Token generated but email sending failed.",
                "reset_token": reset_token,
                "error": str(e)
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Password reset link sent to your email.",
            "reset_token": reset_token
        }, status=status.HTTP_200_OK)

    def reset_password(self, request):
        """Handles password reset"""
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
        """Handles password change for authenticated users"""
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
        """Fetch user profile by primary key (pk)"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        pk = request.data.get("pk")
        if not pk:
            return Response({"error": "User ID (pk) is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileUpdateSerializer(user)
        return Response({
            "message": "User profile fetched successfully",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def update_profile(self, request):
        """Handles profile update"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user  # Current user instance
        data = request.data.copy()

        # Handle file upload separately if using multipart/form-data
        if 'profile_image' in request.FILES:
            # Clear old image if exists
            if user.profile_image_upload:
                user.profile_image_upload.delete(save=False)
            # Assign new image
            data['profile_image_upload'] = request.FILES['profile_image']

        #  Validate email and phone uniqueness before updating
        new_email = request.data.get('email_id')
        new_phone_no = request.data.get('phone_no')

        if new_email and new_email != user.email_id and User.objects.filter(email_id=new_email).exists():
            return Response({"error": "Email is already registered with another account"},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_phone_no and new_phone_no != user.phone_no and User.objects.filter(phone_no=new_phone_no).exists():
            return Response({"error": "Phone number is already in use"}, status=status.HTTP_400_BAD_REQUEST)

        #  Prevent users from changing sensitive fields (Return Error)
        restricted_fields = [
            "status", "password",
            "is_superuser", "is_staff", "is_consent", "google_id"
        ]

        attempted_changes = [field for field in restricted_fields if field in request.data]
        if attempted_changes:
            return Response(
                {"error": f"You are not allowed to update the following fields: {', '.join(attempted_changes)}"},
                status=status.HTTP_403_FORBIDDEN
            )

        #  Use Serializer for updating user profile safely
        serializer = UserProfileUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully", "user": serializer.data},
                            status=status.HTTP_200_OK)

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        #  DELETE ACCOUNT

    def delete_profile(self, request):
        """Handles user account deletion with optional password confirmation and email notification"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        #  Optional password confirmation before deletion
        password = request.data.get("password")
        if password and not check_password(password, request.user.password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_400_BAD_REQUEST)

        #  Retrieve user data before deletion (for response and email)
        user = request.user
        email = user.email_id
        full_name = f"{user.first_name} {user.last_name}".strip()

        # Delete the user account
        user.delete()

        # Send confirmation email after deletion
        try:
            send_mail(
                subject="Account Deletion Confirmation",
                message=f"Hello {full_name or 'User'},\n\nYour account has been successfully deleted. "
                        "If this was not done by you, please contact our support team immediately.\n\n"
                        "Regards,\nThe Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send deletion email: {str(e)}")

        return Response({
            "message": "Account deleted successfully",
        }, status=status.HTTP_200_OK)


