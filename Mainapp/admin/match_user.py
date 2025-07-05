"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import Match

from django.contrib import admin



class MatchAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('id', 'person', 'match_person','score', 'status', 'match_with','created_at', 'updated_at', 'created_by', 'updated_by')

    # Fields to include in the detail view (when editing a match)
    fields = ('person', 'match_person', 'score','status','match_with', 'created_by', 'updated_by')

    # Fields that are read-only in the detail view
    readonly_fields = ('id', 'created_at', 'updated_at')

    # Enable filtering by status in the list view
    list_filter = ('status',)

    # Enable searching by person and match_person in the list view
    search_fields = ('person__full_name', 'match_person__full_name')


# Register the Match model with the custom MatchAdmin class
admin.site.register(Match, MatchAdmin)