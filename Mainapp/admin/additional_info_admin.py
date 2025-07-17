"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin

from ..models import AdditionalInfo


@admin.register(AdditionalInfo)
class AdditionalInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'caste', 'subcaste', 'marital_status', 'religion', 'mother_tongue',  'education_details', 'occupation_details',"id_type",'id_no', 'created_at', 'updated_at')
    list_filter = ('caste', 'marital_status', 'created_at')
    search_fields = ('person__full_name', 'subcaste', 'religion', )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Details', {
            'fields': ('person', 'caste', 'subcaste', 'marital_status', 'religion', 'mother_tongue', 'other_known_languages')
        }),
        ('Professional Details', {
            'fields': ('education_details', 'occupation_details',"id_type",'id_no')
        }),
        ('Meta Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
