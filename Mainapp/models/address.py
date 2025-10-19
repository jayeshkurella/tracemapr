"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

import uuid
# from django.db import models
from django.contrib.gis.db import models

from .volunteer import Volunteer
from .police_station import PoliceStation
from .user import User

class Address(models.Model):
    class AddressTypeChoices(models.TextChoices):
        PERMANENT = 'permanent', 'PERMANENT'  # Long-term residence
        CURRENT = 'current', 'CURRENT'  # Current address
        OLD = 'old', 'OLD'  # Previous address
        HOME = 'home', 'HOME'  # Home address
        OFFICE = 'office', 'OFFICE'  # Office or workplace
        TEMPORARY = 'temporary', 'TEMPORARY'  # Temporary residence
        BILLING = 'billing', 'BILLING'  # Billing address
        SHIPPING = 'shipping', 'SHIPPING'  # Shipping address
        REGISTERED = 'registered', 'REGISTERED'  # Official registered address
        MAILING = 'mailing', 'MAILING'  # Mailing address (PO Box etc.)
        VACATION = 'vacation', 'VACATION'  # Vacation or secondary home
        RENTAL = 'rental', 'RENTAL'  # Rented address
        STUDENT = 'student', 'STUDENT'  # Address for students (e.g., hostel, dormitory)
        FAMILY = 'family', 'FAMILY'  # Family address
        OTHER = 'other', 'OTHER'  # Any other unspecified address

    class StateChoices(models.TextChoices):
        ANDHRA_PRADESH = 'Andhra Pradesh', 'Andhra Pradesh'
        ARUNACHAL_PRADESH = 'Arunachal Pradesh', 'Arunachal Pradesh'
        ASSAM = 'Assam', 'Assam'
        BIHAR = 'Bihar', 'Bihar'
        CHHATTISGARH = 'Chhattisgarh', 'Chhattisgarh'
        GOA = 'Goa', 'Goa'
        GUJARAT = 'Gujarat', 'Gujarat'
        HARYANA = 'Haryana', 'Haryana'
        HIMACHAL_PRADESH = 'Himachal Pradesh', 'Himachal Pradesh'
        JHARKHAND = 'Jharkhand', 'Jharkhand'
        KARNATAKA = 'Karnataka', 'Karnataka'
        KERALA = 'Kerala', 'Kerala'
        MADHYA_PRADESH = 'Madhya Pradesh', 'Madhya Pradesh'
        MAHARASHTRA = 'Maharashtra', 'Maharashtra'
        MANIPUR = 'Manipur', 'Manipur'
        MEGHALAYA = 'Meghalaya', 'Meghalaya'
        MIZORAM = 'Mizoram', 'Mizoram'
        NAGALAND = 'Nagaland', 'Nagaland'
        ODISHA = 'Odisha', 'Odisha'
        PUNJAB = 'Punjab', 'Punjab'
        RAJASTHAN = 'Rajasthan', 'Rajasthan'
        SIKKIM = 'Sikkim', 'Sikkim'
        TAMIL_NADU = 'Tamil Nadu', 'Tamil Nadu'
        TELANGANA = 'Telangana', 'Telangana'
        TRIPURA = 'Tripura', 'Tripura'
        UTTAR_PRADESH = 'Uttar Pradesh', 'Uttar Pradesh'
        UTTARAKHAND = 'Uttarakhand', 'Uttarakhand'
        WEST_BENGAL = 'West Bengal', 'West Bengal'

    class CountryChoices(models.TextChoices):
        INDIA = 'India', 'India'
        USA = 'United States of America', 'United States of America'
        CHINA = 'China', 'China'
        JAPAN = 'Japan', 'Japan'
        GERMANY = 'Germany', 'Germany'
        UK = 'United Kingdom', 'United Kingdom'
        FRANCE = 'France', 'France'
        BRAZIL = 'Brazil', 'Brazil'
        AUSTRALIA = 'Australia', 'Australia'
        CANADA = 'Canada', 'Canada'
        RUSSIA = 'Russia', 'Russia'
        ITALY = 'Italy', 'Italy'
        SOUTH_KOREA = 'South Korea', 'South Korea'
        MEXICO = 'Mexico', 'Mexico'
        SOUTH_AFRICA = 'South Africa', 'South Africa'
        INDONESIA = 'Indonesia', 'Indonesia'
        SAUDI_ARABIA = 'Saudi Arabia', 'Saudi Arabia'
        TURKEY = 'Turkey', 'Turkey'
        SPAIN = 'Spain', 'Spain'
        NETHERLANDS = 'Netherlands', 'Netherlands'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address_type = models.CharField(max_length=50, choices=AddressTypeChoices.choices, db_index=True,blank=True, null=True)

    # Address Details
    street = models.CharField(max_length=50, blank=True, null=True)
    appartment_no = models.CharField(max_length=50, blank=True, null=True)
    appartment_name = models.CharField(max_length=50, blank=True, null=True)
    village = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    district = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=50, choices=StateChoices.choices, db_index=True,blank=True, null=True)
    pincode = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    country = models.CharField(max_length=50, help_text="Country code or ID", choices=CountryChoices.choices,
                               default="India", db_index=True,blank=True, null=True)
    landmark_details = models.CharField(max_length=200, blank=True, null=True)

    # Geolocation
    location = models.PointField(srid=4326, blank=True, null=True, db_index=True)

    # Status and Ownership
    is_active = models.BooleanField(default=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    person = models.ForeignKey('Person', on_delete=models.SET_NULL, related_name="addresses", null=True, blank=True,db_index=True)
    volunteer = models.ForeignKey('Volunteer', on_delete=models.SET_NULL, related_name="volunteer_Address", null=True, blank=True,db_index=True)
    country_code = models.CharField(max_length=10, db_index=True, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Created & Updated By
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="created_%(class)s_set", db_index=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="updated_%(class)s_set", db_index=True)

    def save(self, *args, **kwargs):
        if self.city:
            self.city = self.city.capitalize()
        if self.district:
            self.district = self.district.capitalize()
        if self.village:
            self.village = self.village.capitalize()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["address_type", "city", "state", "pincode"]),
            models.Index(fields=["country", "district"]),
            models.Index(fields=["person", "user"]),
            models.Index(fields=["created_at", "updated_at"]),
            models.Index(fields=["location"]),
        ]

    def __str__(self):
        return f"{self.address_type} - {self.city}, {self.state} ({self.pincode})"


