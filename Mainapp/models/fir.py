"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .person import Person

from .contact import Contact

from .police_station import PoliceStation
from .user import User

class FIR(models.Model):

    class CaseStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"
        IN_PROGRESS = "In Progress", "In Progress"
        RESOLVED = "Resolved", "Resolved"
        PENDING = "Pending", "Pending"


    fir_photo = models.FileField(upload_to='fir_photos/', null=True, blank=True)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fir_number  = models.CharField(max_length=50,  help_text="Unique FIR number",blank=True, null=True)
    case_status = models.CharField(max_length=50, blank=True, null=True,choices=CaseStatus.choices, default=CaseStatus.OPEN)
    investigation_officer_name = models.CharField(max_length=50, help_text="Name of the investigation officer",blank=True, null=True)
    investigation_officer_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    investigation_officer_contacts = models.CharField(null=True, blank=True)
    police_station = models.ForeignKey(PoliceStation, on_delete=models.CASCADE,null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL,null=True, blank=True,related_name="firs",)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")


    def __str__(self):
        return f"FIR {self.fir_number} - {self.case_status}"
