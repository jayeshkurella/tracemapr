"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.contrib import admin
from ..models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("person",'phone_no', 'email_id', 'type','company_name','person_name', 'user','volunteer', 'hospital', 'police_station', 'is_primary', 'created_at')
    list_filter = ('type', 'is_primary', 'created_at')
    search_fields = ('phone_no', 'email_id', 'company_name')
    ordering = ('-created_at',)
