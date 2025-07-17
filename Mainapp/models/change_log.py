"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from django.db import models

class ChangeLog(models.Model):
    date = models.DateField()
    version = models.CharField(max_length=50)
    added = models.JSONField(default=list, blank=True)
    modified = models.JSONField(default=list, blank=True)
    tested = models.JSONField(default=list, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Indexed for sorting

    def __str__(self):
        return f"{self.date} - {self.version}"
