from django.contrib import admin

# Register your models here.
# user_management/admin.py

from django.contrib import admin
from .models import Feature, RoleFeatureAccess


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "description")
    search_fields = ("code", "name")


@admin.register(RoleFeatureAccess)
class RoleFeatureAccessAdmin(admin.ModelAdmin):
    list_display = ("role", "feature", "is_allowed")
    list_filter = ("role", "is_allowed")
    search_fields = ("role", "feature__code")
