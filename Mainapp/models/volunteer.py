
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid

from django.db import models


class Volunteer(models.Model):

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Transgender', 'Transgender'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    SEARCH_GROUP_CHOICES = [
        ('Group A', 'Group A'),
        ('Group B', 'Group B'),
        ('Group C', 'Group C'),
    ]

    MODE_OF_SEARCH_CHOICES = [
        ('On Foot', 'On Foot'),
        ('Vehicle', 'Vehicle'),
        ('Drone', 'Drone'),
    ]

    # Personal Details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.CharField(max_length=255, db_index=True)
    dob = models.DateField(help_text="Date of Birth", db_index=True, null=True, blank=True)
    photo_upload = models.ImageField(upload_to='Volunteer/', null=True, blank=True, db_index=True)

    Age = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, db_index=True, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Assignment Info
    volunteer_group = models.CharField(max_length=50, choices=SEARCH_GROUP_CHOICES, db_index=True, null=True, blank=True)
    assigned_region = models.CharField(max_length=100, help_text="Region assigned to the volunteer", db_index=True, null=True, blank=True)
    search_start_date = models.DateField(db_index=True, null=True, blank=True)
    search_end_date = models.DateField(blank=True, null=True, db_index=True,)
    search_timing = models.TimeField(help_text="Timing for the volunteer's search", db_index=True, null=True, blank=True)
    gps_tracker_enabled = models.BooleanField(default=False, help_text="Does the volunteer have GPS tracking?", db_index=True)
    mode_of_search = models.CharField(max_length=50, choices=MODE_OF_SEARCH_CHOICES, db_index=True, null=True, blank=True)
    other_equipment_issued = models.TextField(max_length=100, blank=True, null=True, db_index=True)

    # Health and Emergency Details
    blood_group = models.CharField(max_length=20, choices=BLOOD_GROUP_CHOICES, db_index=True, null=True, blank=True)
    known_allergies = models.TextField(max_length=100, blank=True, null=True, db_index=True)
    pre_existing_medical_conditions = models.TextField(max_length=200, blank=True, null=True, db_index=True)
    emergency_contact_name = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=15, db_index=True, null=True, blank=True)
    relationship_with_volunteer = models.CharField(max_length=50, help_text="Relationship with the volunteer (e.g., Father, Mother, Spouse)", db_index=True, null=True, blank=True)

    # Feedback
    feedback_after_search = models.TextField(max_length=200, blank=True, null=True, db_index=True)
    issues_faced_during_search = models.TextField(max_length=200, blank=True, null=True, db_index=True)
    additional_suggestions = models.TextField(max_length=200, blank=True, null=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)  # Add this field
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.full_name

    class Meta:
        indexes = [
            models.Index(fields=['full_name', 'dob', 'gender' ,'photo_upload' ,'is_active']),
            models.Index
                (fields=['volunteer_group', 'assigned_region', 'search_start_date', 'search_end_date', 'search_timing']),
            models.Index(fields=['gps_tracker_enabled', 'mode_of_search', 'other_equipment_issued']),
            models.Index(fields=['blood_group', 'known_allergies', 'pre_existing_medical_conditions']),
            models.Index(fields=['emergency_contact_name', 'emergency_contact_number', 'relationship_with_volunteer']),
            models.Index(fields=['feedback_after_search', 'issues_faced_during_search', 'additional_suggestions']),
            models.Index(fields=['is_deleted']),
        ]
