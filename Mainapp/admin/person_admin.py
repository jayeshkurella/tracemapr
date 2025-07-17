"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin
from ..models.person import Person
from leaflet.admin import LeafletGeoAdmin

@admin.register(Person)
class PersonAdmin(LeafletGeoAdmin):
    list_display = (
       "case_id", "person_approve_status","reported_date","sr_no", "full_name", "type", "gender", "age", "age_range","birth_date","birthtime",
        "height","height_range", "weight", "blood_group", "complexion","photo_photo","bodies_condition","up_condition",
        "eye_color", "hair_type", "hair_color","death_type",
        'address_type','street', 'appartment_no', 'appartment_name', 'village', 'city', 'district', 'state', 'pincode', 'country',
        "hospital", "_is_confirmed", "_is_deleted", "case_status", "created_at","match_with",
    )

    list_filter = (
       "person_approve_status", "type", "gender", "blood_group", "complexion",
        "eye_color", "hair_type", "hair_color", "Body_Condition",
        "_is_confirmed", "_is_deleted", "hospital",
        "condition", "state", "country", "address_type", "case_status"
    )

    search_fields = (
       "case_id", "full_name", "distinctive_mark", "birth_mark", "document_ids",
        "city", "district", "village", "street", "landmark_details"
    )

    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("case_id","full_name", "type", "gender", "birth_date", "age","age_range", "birthplace","birthtime")
        }),
        ("Physical Characteristics", {
            "fields": ("height","height_range", "weight", "complexion", "eye_color", "hair_color", "hair_type", "blood_group","photo_photo")
        }),
        ("Medical & Identification", {
            "fields": ("condition", "Body_Condition", "birth_mark", "distinctive_mark","bodies_condition","up_condition","death_type")
        }),
        ("Address Information", {
            "fields": (
                "address_type", "street", "appartment_no", "appartment_name",
                "village", "city", "district", "state", "pincode",
                "country", "landmark_details", "location"
            )
        }),
        ("Case Management", {
            "fields": ("case_status",)
        }),
        ("Additional Details", {
            "fields": ("hospital", "document_ids")
        }),
        ("System Information", {
            "fields": ("created_by", "updated_by", "created_at", "updated_at", "_is_confirmed", "_is_deleted","match_with","person_approve_status","reported_date")
        }),
    )

    def sr_no(self, obj):
        """Generate serial number dynamically"""
        return list(self.get_queryset(None)).index(obj) + 1

    sr_no.short_description = "Sr. No."

    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    def delete_model(self, request, obj):
        obj._is_deleted = True
        obj.save()

    @admin.action(description='Soft delete selected persons')
    def soft_delete_selected(self, request, queryset):
        queryset.update(_is_deleted=True)

    actions = [soft_delete_selected]
