"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
import logging
logger = logging.getLogger(__name__)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    status_updated_by = serializers.StringRelatedField(read_only=True)
    profile_image_upload = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = [
            "id",
            "user_type",
            "sub_user_type",
            "first_name",
            "last_name",
            "email_id",
            "phone_no",
            "country_code",
            "profile_image_upload",
            "is_consent",
            "status",
            "status_updated_by",
            "registered_at",
            "created_at",
            "updated_at","google_id", "name", "email_by_google", "picture"
        ]
        extra_kwargs = {'password': {'write_only': True},
                        'status': {'read_only': True}
                        }

    def get_profile_image_upload(self, obj):
        """
        Returns the appropriate profile image URL based on:
        1. Google picture (if available)
        2. Uploaded profile image (if available)
        3. Default avatar (fallback)
        """
        logger.debug(f"Getting profile image for user ID: {obj.id}")

        if obj.picture:
            logger.debug(f"Using Google picture for user {obj.id}: {obj.picture}")
            return obj.picture  # Google users' picture

        if obj.profile_image_upload:
            request = self.context.get('request')
            if request:
                url = request.build_absolute_uri(obj.profile_image_upload.url)
                logger.debug(f"Using uploaded profile image with absolute URL for user {obj.id}: {url}")
                return url
            else:
                url = obj.profile_image_upload.url
                logger.debug(f"Using uploaded profile image for user {obj.id}: {url}")
                return url  # Form users with uploaded image

        logger.debug(f"Using default avatar for user {obj.id}")
        return '/static/images/default-avatar.png'  # Default fallback


class AuthSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['register', 'login', 'logout', 'forgot_password', 'reset_password', 'change_password',
                 'update_profile','delete_account'])

    email_id = serializers.EmailField(required=False)
    phone_no = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    user_type = serializers.CharField(required=False)
    sub_user_type = serializers.CharField(required=False, allow_blank=True)

    password = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    new_password2 = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        """Validate password and confirm password match."""
        action = data.get('action')

        logger.debug(f"Validating AuthSerializer for action: {action}")

        if action == 'register' or action == 'reset_password':
            password = data.get('password')
            password2 = data.get('password2')

            if password and password2 and password != password2:
                logger.warning(f"Password validation failed for action {action}: passwords do not match")
                raise serializers.ValidationError({'password2': "Passwords do not match."})

        if action == 'change_password':
            new_password = data.get('new_password')
            new_password2 = data.get('new_password2')

            if new_password and new_password2 and new_password != new_password2:
                logger.warning("New password validation failed: passwords do not match")
                raise serializers.ValidationError({'new_password2': "New passwords do not match."})
        logger.debug("AuthSerializer validation completed successfully")
        return data




class UserProfileUpdateSerializer(serializers.ModelSerializer):
    status_updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "user_type",
            "sub_user_type",
            "first_name",
            "last_name",
            "email_id",
            "phone_no",
            "country_code",
            "profile_image_upload",
            "is_consent",
            "status",
            "status_updated_by",
            "registered_at",
            "created_at",
            "updated_at", "name", "email_by_google", "picture"
        ]
        extra_kwargs = {
            'email_id': {'validators': []},  # Bypass unique check as we handle it in view
            'phone_no': {'validators': []},
            'profile_image_upload': {'required': False},
        }

