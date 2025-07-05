"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .address import Address
from .contact import Contact
from .user import User

class AdminUser(models.Model):
    class AdminTypeChoices(models.TextChoices):
        ADMIN = "admin", "Admin"
        SUB_ADMIN = "subadmin", "Sub-Admin"
        BACKEND_USER = "backend_user", "Backend User"
        SURVEYOR = "surveyor", "Surveyor"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=AdminTypeChoices.choices)
    permission = models.JSONField(help_text="Stores role-based permissions in JSON format")

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateTimeField()

    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.type})"
