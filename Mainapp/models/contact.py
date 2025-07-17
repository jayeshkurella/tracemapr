"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models




class Contact(models.Model):
    class ContactTypeChoices(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        OFFICE = 'office', 'Office'
        HOME = 'home', 'Home'
        REFERRAL = 'referral', 'Referral'  # New Referral contact type
        EMERGENCY = 'emergency', 'Emergency'  # Emergency contact
        WORK = 'work', 'Work'  # Work-related contact
        FAMILY = 'family', 'Family'  # Family contact
        FRIEND = 'friend', 'Friend'  # Friend contact
        MEDICAL = 'medical', 'Medical'  # Medical contact
        SCHOOL = 'school', 'School'  # School or educational institution contact
        LEGAL = 'legal', 'Legal'  # Legal representative or lawyer contact
        OTHER = 'other', 'Other'  # Any other unspecified contact type

    class SocialMediaChoices(models.TextChoices):
        FACEBOOK = 'fb', 'Facebook'
        INSTAGRAM = 'insta', 'Instagram'
        X = 'x', 'X (Twitter)'
        THREADS = 'thread', 'Threads'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_no = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    country_cd = models.CharField(max_length=5, help_text="Country Code", blank=True, null=True, db_index=True)
    email_id = models.EmailField(max_length=150, blank=True, null=True, db_index=True)
    type = models.CharField(max_length=10, choices=ContactTypeChoices.choices)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    person_name = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=50, blank=True, null=True)
    website_url = models.TextField(blank=True, null=True)
    social_media_availability = models.CharField(max_length=10, choices=SocialMediaChoices.choices, blank=True, null=True)
    social_media_url = models.CharField(blank=True, null=True)
    additional_details = models.TextField(blank=True, null=True)
    is_primary = models.BooleanField(default=False, db_index=True)

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='contacts', null=True, blank=True, db_index=True)
    hospital = models.ForeignKey('Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='hospital_contact', db_index=True)
    police_station = models.ForeignKey('PoliceStation', on_delete=models.SET_NULL, null=True, blank=True, related_name="police_contact", db_index=True)
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, related_name="contacts", null=True, blank=True, db_index=True)
    volunteer = models.ForeignKey('Volunteer', on_delete=models.SET_NULL, related_name="volunteer_contact", null=True, blank=True,db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Indexed for sorting
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  # Indexed for sorting
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set", db_index=True)
    updated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set", db_index=True)

    def __str__(self):
        return f"{self.phone_no} ({self.type})"

    class Meta:
        indexes = [
            models.Index(fields=['phone_no']),  # Composite index
            models.Index(fields=['email_id']),
            models.Index(fields=['country_cd']),

        ]