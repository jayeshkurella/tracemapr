"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .person import Person

from .document import Document
from .user import User

class Consent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.TextField(blank=True, null=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE,blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL,related_name="consent", null=True, blank=True)
    is_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    def __str__(self):
        return f"{self.is_consent}"
