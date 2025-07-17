"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""


from ..models import PoliceStation
from django.contrib import admin


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    search_fields = ['name', 'phone_no', 'address__area_name']
