

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from Mainapp.models import Missing_match_with_body


@admin.register(Missing_match_with_body)
class Missing_match_with_bodyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_viewed',
        'match_id',
        'missing_person',
        'unidentified_bodies',
        'score',
        'match_type',
        'created_by',
        'updated_by',
        'created_at',
    )
    list_filter = ('match_type', 'created_at',)
    search_fields = ('missing_person__full_name', 'unidentified_bodies__full_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')







