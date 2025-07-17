"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.db import models

from .user import User
from .fir import  FIR
from .last_known_details import LastKnownDetails
from django.core.validators import FileExtensionValidator
class Document(models.Model):
    PERSON_TYPE_CHOICES = [
        ('missing person', 'Missing Person'),
        ('unidentified person', 'Unidentified Person'),
        ('unidentified body', 'Unidentified Body'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        # FIR-related
        ('fir_scan', 'FIR Scan'),
        ('fir_attachment', 'FIR Attachment'),
        ('incident_report', 'Incident Report'),

        # CCTV and scene
        ('cctv', 'CCTV Footage'),
        ('scene_photo', 'Scene Photo'),

        # Witness and last known
        ('witness_statement', 'Witness Statement'),
        ('last_known_photo', 'Last Known Photo'),
        ('last_known_location_note', 'Last Known Location Note'),
        ('last_known_description', 'Last Known Description'),

        # Belongings (specific types)
        ('belonging_bag', 'Belonging - Bag'),
        ('belonging_watch', 'Belonging - Watch'),
        ('belonging_pocket', 'Belonging - Pocket Items'),
        ('belonging_wallet', 'Belonging - Wallet'),
        ('belonging_mobile', 'Belonging - Mobile Phone'),
        ('belonging_clothing', 'Belonging - Clothing'),

        # Other
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES,blank=True, null=True )
    document_type  = models.CharField(max_length=90, choices=DOCUMENT_TYPE_CHOICES,blank=True, null=True)
    description = models.TextField(null=True,blank=True)
    document = models.FileField( blank=True, null=True, upload_to='documents/', validators=[
            FileExtensionValidator([
                # Images
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
                # Documents
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'rtf',
                # Audio/Video
                'mp3', 'wav', 'ogg', 'mp4', 'mov', 'avi', 'mkv',
                # Archives
                'zip', 'rar'
            ])
        ])
    fir = models.ForeignKey(FIR,on_delete=models.CASCADE,  null=True, blank=True, related_name='documents')
    last_known_detail = models.ForeignKey( LastKnownDetails, on_delete=models.CASCADE, null=True,blank=True, related_name='documents')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_type} - {self.person_type}"