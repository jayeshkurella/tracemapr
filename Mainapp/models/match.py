"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .person import Person
from .user import User

class Match(models.Model):
    class StatusChoices(models.TextChoices):
        MATCHED = "Matched", "matched"

    class MatchWithChoices(models.TextChoices):
        MISSING_PERSON = "Missing Person", "Missing Person"
        UNIDENTIFIED_PERSON = "Unidentified Person", "Unidentified Person"
        UNIDENTIFIED_BODY = "Unidentified Body", "Unidentified Body"


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='matches_initiated')
    match_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='matches_received')
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.MATCHED)
    match_with = models.CharField(
        max_length=20,
        choices=MatchWithChoices.choices,
        blank=True,
        null=True,
        help_text="The type of the matched entity"
    )
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    class Meta:
        unique_together = ('person', 'match_person')  # Prevents duplicate match entries

    def __str__(self):
        return f"Match: {self.person.full_name}  ({self.status})"
