"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework import serializers

from Mainapp.Additional_info_Tags.tags_model import Caste, educational_tag, occupation_tags


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ['id', 'name']

    def validate_name(self, value):
        # Capitalize first letter but keep rest as is
        name = value[0].upper() + value[1:] if value else value

        # Check for case-insensitive uniqueness
        if Caste.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError("This caste name already exists.")

        return name


class educationalSerializer(serializers.ModelSerializer):
    class Meta:
        model = educational_tag
        fields = ['id', 'name']

    def validate_name(self, value):
        # Capitalize first letter but keep rest as is
        name = value[0].upper() + value[1:] if value else value

        # Check for case-insensitive uniqueness
        if Caste.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError("This caste name already exists.")

        return name


class occupationSerializer(serializers.ModelSerializer):
    class Meta:
        model = occupation_tags
        fields = ['id', 'name']

    def validate_name(self, value):
        # Capitalize first letter but keep rest as is
        name = value[0].upper() + value[1:] if value else value

        # Check for case-insensitive uniqueness
        if Caste.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError("This caste name already exists.")

        return name