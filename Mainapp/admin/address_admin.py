"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import Address
from leaflet.admin import LeafletGeoAdmin


@admin.register(Address)
class AddressAdmin(LeafletGeoAdmin):
    list_display = ('sr_no', 'address_type','village', 'city','district', 'state', 'pincode', 'country', 'pincode','landmark_details','location','is_active',"get_hospital_names","get_policestation_names" ,'created_at', 'updated_at')
    list_filter = ('address_type', 'state', 'country', 'is_active', 'created_at')
    search_fields = ('street', 'appartment_no', 'appartment_name', 'village', 'city', 'district', 'state', 'pincode', 'country')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {'fields': ('address_type', 'is_active')}),
        ('Location Details', {'fields': ('street', 'appartment_no', 'appartment_name', 'village', 'city', 'district', 'state', 'pincode', 'country', 'landmark_details', 'location')}),
        ('Related Entities', {'fields': ('user', 'person','volunteer', 'created_by', 'updated_by')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def get_hospital_names(self, obj):
        return ", ".join([hospital.name for hospital in obj.hospitals.all()]) or "-"

    get_hospital_names.short_description = 'Hospitals'

    def get_policestation_names(self, obj):
        return ", ".join([station.name for station in obj.police_stations.all()]) or "-"

    get_policestation_names.short_description = 'police_stations'

    def sr_no(self, obj):
        queryset = Address.objects.order_by('created_at')
        return list(queryset).index(obj) + 1  # Auto-increment SR No
    sr_no.short_description = "SR No"

    readonly_fields = ('created_at', 'updated_at')

