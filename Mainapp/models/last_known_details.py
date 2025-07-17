"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .address import Address
from .person import Person
from .user import User

class LastKnownDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person_photo = models.ImageField(blank=True, null=True, help_text="URL or Base64 encoded photo of the person",upload_to='All_Photos')
    reference_photo = models.ImageField(blank=True, null=True, help_text="URL or Base64 encoded reference photo",upload_to='All_Photos')
    missing_time = models.TimeField(blank=True, null=True)
    missing_date = models.DateField(help_text="Date the person went missing",blank=True, null=True)
    last_seen_location = models.TextField(null=True, blank=True, db_index=True)
    missing_location_details = models.TextField(null=True, blank=True, db_index=True)


    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL,null=True, blank=True,related_name="last_known_details",)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    def __str__(self):
        return f"Last Known Details - {self.missing_date}"
