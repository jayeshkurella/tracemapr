"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from ..models import User
from django.contrib import admin


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ( 'email_id', 'is_staff', 'is_superuser',"registered_at")
=======
    list_display = ( 'email_id', "user_type","sub_user_type",'is_staff', 'is_superuser',"registered_at","last_login_ip")
>>>>>>> 69f7355bdf0f26b2138b83f227520f994175b8e0
    search_fields = ('email_id',)
    list_filter = ('is_staff', 'is_superuser')