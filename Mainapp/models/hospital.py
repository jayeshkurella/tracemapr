"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.conf import settings
from django.db import models
import uuid

from .address import Address


class Hospital(models.Model):
    ACTIVE = 'Active'
    INACTIVE = 'Non-Active'

    class HospitalTypeChoices(models.TextChoices):
        GOVERNMENT = 'govt', 'Government'
        SEMI_GOVERNMENT = 'semi_govt', 'Semi-Government'
        NON_GOVERNMENT = 'private', 'Private'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Non-Active'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital_photo =models.ImageField(upload_to='Hospitals_photos/', blank=True, null=True)
    name = models.CharField(max_length=255,blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE,null=True, blank=True,related_name='hospitals')
    type = models.CharField(max_length=10, choices=HospitalTypeChoices.choices,blank=True, null=True)
    activ_Status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ACTIVE,blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")

    def __str__(self):
        return self.name