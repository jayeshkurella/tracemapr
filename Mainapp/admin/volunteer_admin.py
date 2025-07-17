"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import Volunteer


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'dob', 'gender', 'volunteer_group',
        'assigned_region', 'search_start_date', 'is_active'
    )

    list_filter = (
        'gender', 'volunteer_group', 'assigned_region',
        'search_start_date', 'search_end_date', 'is_active'
    )

    search_fields = ('full_name', 'assigned_region', 'emergency_contact_name')

    ordering = ('-search_start_date',)



    fieldsets = (
        ("Personal Details", {
            'fields': ('full_name', 'dob', 'Age', 'gender', 'photo_upload', 'is_active')
        }),
        ("Assignment Info", {
            'fields': ('volunteer_group', 'assigned_region', 'search_start_date',
                       'search_end_date', 'search_timing', 'mode_of_search', 'gps_tracker_enabled')
        }),
        ("Health & Emergency", {
            'fields': ('blood_group', 'known_allergies', 'pre_existing_medical_conditions',
                       'emergency_contact_name', 'emergency_contact_number', 'relationship_with_volunteer')
        }),
        ("Feedback", {
            'fields': ('feedback_after_search', 'issues_faced_during_search', 'additional_suggestions')
        }),
    )

    list_per_page = 20  # Pagination for large datasets

    def has_delete_permission(self, request, obj=None):
        return True  # Prevent deletion from admin panel

    def has_add_permission(self, request):
        return True  # Allow adding new volunteers

