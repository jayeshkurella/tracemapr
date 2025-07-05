

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework import serializers

from ..models.change_log import ChangeLog


class ChangeLogSerializer(serializers.ModelSerializer):
    added = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    modified = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    # tested = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    class Meta:
        model = ChangeLog
        fields = '__all__'
