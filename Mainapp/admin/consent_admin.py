"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("id", "is_consent", "person", "document", "created_at")
    list_filter = ("is_consent", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    fieldsets = (
        ("Consent Details", {
            "fields": ("data", "document", "person", "is_consent")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by")
        }),
    )