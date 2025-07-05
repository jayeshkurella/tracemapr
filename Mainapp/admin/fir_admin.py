"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import FIR


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    list_display = ("fir_number", "case_status", "investigation_officer_name","investigation_officer_contact", "police_station", "created_at")
    list_filter = ("case_status", "police_station", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    fieldsets = (
        ("FIR Details", {
            "fields": ("fir_number", "case_status", "police_station", "person")
        }),
        ("Investigation Details", {
            "fields": ("investigation_officer_name", "investigation_officer_contact","investigation_officer_contacts")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by")
        }),
    )

