"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import LastKnownDetails


@admin.register(LastKnownDetails)
class LastKnownDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'missing_date','missing_time', 'last_seen_location', 'missing_location_details',
                     'created_at', 'updated_at')
    list_filter = ('missing_date', 'created_at')
    search_fields = ('last_seen_location', 'missing_location_details', )
    ordering = ('-created_at',)

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Person Details', {
            'fields': ('person',)
        }),
        ('Missing Details', {
            'fields': (
            'missing_date','missing_time', 'last_seen_location', 'missing_location_details',
            'address')
        }),
        ('Photos', {
            'fields': ('person_photo', 'reference_photo')
        }),
        ('Meta Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
