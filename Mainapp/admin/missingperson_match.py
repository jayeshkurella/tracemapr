"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from Mainapp.models import PersonMatchHistory


@admin.register(PersonMatchHistory)
class PersonMatchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_viewed',
        'match_id',
        'missing_person',
        'unidentified_person',
        'score',
        'match_type',
        'created_by',
        'updated_by',
        'created_at',
    )
    list_filter = ('match_type', 'created_at',)
    search_fields = ('missing_person__full_name', 'unidentified_person__full_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
