"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .person import Person
from .user import User

class PersonUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    class Meta:
        unique_together = ('person', 'user')  # Ensures a unique mapping per person-user

    def __str__(self):
        return f"{self.user.first_name} "
