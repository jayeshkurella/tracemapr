from rest_framework import serializers
from .models import Feature, RoleFeatureAccess

from .models import UserFeatureAccess

class UserFeatureAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeatureAccess
        fields = "__all__"


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "code", "name", "description"]


class RoleFeatureAccessSerializer(serializers.ModelSerializer):
    feature_detail = FeatureSerializer(source="feature", read_only=True)

    class Meta:
        model = RoleFeatureAccess
        fields = ["id", "role", "feature", "feature_detail", "is_allowed"]


from rest_framework import serializers
from .models import UserActivityLog
class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = UserActivityLog
        fields = [
            'id', 'user_name', 'user_role', 'action',
            'description', 'case_id', 'created_at', 'time_ago'
        ]

    def get_user_name(self, obj):
        if obj.user_name:
            return obj.user_name
        if obj.user:
            # fallback to user fields
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.name or obj.user.email_id
        return "Unknown"

    def get_user_role(self, obj):
        if obj.user_role:
            return obj.user_role
        if obj.user:
            return getattr(obj.user, 'user_type', 'Unknown')
        return "Unknown"

    def get_time_ago(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince

        if obj.created_at:
            now = timezone.now()
            return timesince(obj.created_at, now) + ' ago'
        return ''

#
# class ActivityLogSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.get_full_name', read_only=True)
#     user_role = serializers.CharField(source='user.user_type', read_only=True)
#     time_ago = serializers.SerializerMethodField()
#
#     class Meta:
#         model = UserActivityLog
#         fields = [
#             'id', 'user_name', 'user_role', 'action',
#             'description', 'case_id', 'created_at', 'time_ago'
#         ]
#
#     def get_time_ago(self, obj):
#         from django.utils import timezone
#         from django.utils.timesince import timesince
#
#         if obj.created_at:
#             now = timezone.now()
#             return timesince(obj.created_at, now) + ' ago'
#         return ''