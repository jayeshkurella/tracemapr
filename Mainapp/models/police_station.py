"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models
# from .address import Address
from .user import User

class PoliceStation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, help_text="Name of the police station", blank=True, null=True)
    phone_no = models.CharField(max_length=50, blank=True, null=True, help_text="Contact number of the police station")
    station_photo = models.ImageField(upload_to='police_station_photos/', blank=True, null=True)
    address = models.ForeignKey('Address', on_delete=models.CASCADE,blank=True, null=True, related_name='police_stations')
    activ_Status =models.CharField(max_length=10, blank=True, null=True,default='Active',choices=(('Active','Active'),('Inactive','Inactive')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    def __str__(self):
        return self.name
