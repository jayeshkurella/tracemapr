"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from django.db import models

class Caste(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class educational_tag(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class occupation_tags(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name
