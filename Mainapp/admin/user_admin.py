"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from ..models import User
from django.contrib import admin


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ( 'email_id', 'is_staff', 'is_superuser',"registered_at")
    search_fields = ('email_id',)
    list_filter = ('is_staff', 'is_superuser')