"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from Mainapp.models import Person
from .user import User
import random
import string
from django.utils.timezone import now

def generate_custom_match_id():
    date_str = now().strftime("%Y%m%d")  # Only date
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"MATCH-{date_str}-{suffix}"

class Missing_match_with_body(models.Model):

    MATCH_TYPE_CHOICES = [
        ('potential', 'Potential Match'),
        ('matched', 'Matched'),
        ('rejected', 'Rejected'),
        ('confirmed', 'Confirmed')
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    match_id = models.CharField(
        max_length=30,
        default=generate_custom_match_id,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )
    missing_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='missing_body_matches')
    unidentified_bodies = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='ub_matches')
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES)
    score = models.IntegerField(null=True, blank=True)  # Add this field
    match_parameters = models.JSONField(default=dict, help_text="Detailed matching parameters")
    reject_reason = models.TextField(null=True, blank=True)
    unreject_reason = models.TextField(null=True, blank=True)
    confirmation_note = models.TextField(null=True, blank=True)
    unconfirm_reason = models.TextField(null=True, blank=True)
    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="updated_%(class)s_set")

