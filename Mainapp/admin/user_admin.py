"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from ..models import User
from django.contrib import admin


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ( 'email_id', "user_type","sub_user_type",'is_staff', 'is_superuser',"registered_at","last_login_ip")
    search_fields = ('email_id',)
    list_filter = ('is_staff', 'is_superuser')