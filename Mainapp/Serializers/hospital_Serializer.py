
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework import serializers

from ..models import Hospital


class HospitalIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name']