"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from Mainapp.models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "person_type",
        "document_type",
        "get_fir_identifier",
        "get_last_known_detail_identifier",
        "created_at",
        "updated_at"
    )
    list_filter = ("person_type", "document_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Document Details", {
            "fields": ("person_type", "document_type", "document", "fir", "last_known_detail")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at", "created_by", "updated_by")
        }),
    )

    # Custom display method for FIR
    def get_fir_identifier(self, obj):
        return str(obj.fir) if obj.fir else "-"
    get_fir_identifier.short_description = "FIR"

    # Custom display method for LastKnownDetails
    def get_last_known_detail_identifier(self, obj):
        return str(obj.last_known_detail) if obj.last_known_detail else "-"
    get_last_known_detail_identifier.short_description = "Last Known Detail"
