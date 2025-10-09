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
