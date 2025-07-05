"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import Hospital

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'activ_Status', 'created_at', 'updated_at')
    list_filter = ('type', 'activ_Status', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    # Optional: If address model has __str__ method, this will show related address nicely
    raw_id_fields = ('address', 'created_by', 'updated_by')