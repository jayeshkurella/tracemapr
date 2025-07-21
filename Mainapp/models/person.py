"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
import uuid
from django.conf import settings
from django.contrib.gis.db import models
from django.db import transaction

from .hospital import Hospital
from django.utils.timezone import now
from datetime import date

from .user import User

class Person(models.Model):
    class TypeChoices(models.TextChoices):
        MISSING = 'Missing Person', 'Missing Person'
        Unidentified_Person = 'Unidentified Person', 'Unidentified Person'
        Unidnetified_Body = 'Unidentified Body', 'Unidentified Body'

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    AGE_RANGE_CHOICES = [
        ("0-5", "0 - 5"),
        ("6-12", "6 - 12"),
        ("13-17", "13 - 17"),
        ("18-24", "18 - 24"),
        ("25-34", "25 - 34"),
        ("35-44", "35 - 44"),
        ("45-54", "45 - 54"),
        ("55-64", "55 - 64"),
        ("65-74", "65 - 74"),
        ("75-84", "75 - 84"),
        ("85-100", "85+"),
    ]

    HEIGHT_RANGE_CHOICES = [
        ("<150", "Less than 150 cm"),
        ("150-160", "150 - 160 cm"),
        ("161-170", "161 - 170 cm"),
        ("171-180", "171 - 180 cm"),
        ("181-190", "181 - 190 cm"),
        (">190", "More than 190 cm"),
    ]
    class ComplexionChoices(models.TextChoices):
        DARK = 'dark', 'Dark'
        MEDIUM = 'medium', 'Medium'
        LIGHT = 'light', 'Light'
        FAIR = 'fair', 'Fair'
        DUSKY = 'dusky', 'Dusky'
        WHEATISH = 'wheatish', 'Wheatish'

    class Hair_colorChoices(models.TextChoices):
        BLACK = 'black', 'Black'
        BLUE = 'blue', 'Blue'
        BROWN = 'brown', 'Brown'
        GRAY = 'gray', 'Gray'
        GREEN = 'green', 'Green'
        PURPLE = 'purple', 'Purple'
        RED = 'red', 'Red'
        WHITE = 'white', 'White'
        YELLOW = 'yellow', 'Yellow'

    class Hair_typeChoices(models.TextChoices):
        STRAIGHT =  'straight','STRAIGHT'
        DASHED =  'dashed','DASHED'
        DOTTED =  'dotted','DOTTED'
        LONG = 'long','LONG',
        BROAD = 'broad','BROAD'
        SHORT = 'short','SHORT'
        WAVY = 'wavy','WAVY'

    class Eye_colorChoices(models.TextChoices):
        blue = 'blue', 'Blue'
        brown = 'brown', 'Brown'
        green = 'green', 'Green'
        hazel = 'hazel', 'Hazel'
        red = 'red', 'Red'
        black = 'black', 'Black'
        gray = 'gray', 'Gray'
        yellow = 'yellow', 'Yellow'
        violet = 'violet', 'Violet'

    class BloodGroupChoices(models.TextChoices):
        O_POS = 'O+', 'O+'
        O_NEG = 'O-', 'O-'
        A_POS = 'A+', 'A+'
        A_NEG = 'A-', 'A-'
        B_POS = 'B+', 'B+'
        B_NEG = 'B-', 'B-'
        AB_POS = 'AB+', 'AB+'
        AB_NEG = 'AB-', 'AB-'

    class ConditionChoices(models.TextChoices):
        MEMORY_LOSS = 'memory_loss', 'Memory Loss'
        ANXIETY = 'anxiety', 'Anxiety'
        SHOCK = 'shock', 'Shock'
        DEPRESSION = 'depression', 'Depression'
        FATIGUE = 'fatigue', 'Fatigue'
        HEADACHE = 'headache', 'Headache'
        DIZZINESS = 'dizziness', 'Dizzy'
        NAUSEARCH = 'nausea', 'Nausea'
        CHEST_PAIN = 'chest_pain', 'Chest Pain'

    class BodyconditionChoices(models.TextChoices):
        DECOMPOSED = 'decomposed', 'Decomposed'
        INTACT = 'intact', 'Intact'
        SKELETAL = 'skeletal', 'Skeletal'
        BURNT = 'burnt', 'Burnt'
        FRESH = 'fresh', 'Fresh'
        NORMAL = 'normal', 'Normal'
        UNSTABLE = 'unstable', 'Unstable'
        STABLE = 'stable', 'Stable'
        EXCESS = 'excess', 'Excess'
        UNDERWEIGHT = 'underweight', 'Underweight'
        OVERWEIGHT = 'overweight', 'Overweight'
        OBESE = 'obese', 'Obese'

    DEATH_TYPE_CHOICES = [
        ('natural', 'Natural Causes'),
        ('accident', 'Accident'),
        ('homicide', 'Homicide'),
        ('suicide', 'Suicide'),
        ('unknown', 'Unknown'),
        ('other', 'Other'),
        ('disease', 'Disease'),
        ('poisoning', 'Poisoning'),
        ('drowning', 'Drowning'),
        ('burn', 'Burn'),
        ('starvation', 'Starvation'),
        ('hypothermia', 'Hypothermia'),
        ('heatstroke', 'Heatstroke'),
        ('medical_error', 'Medical Error'),
        ('war', 'War'),
        ('execution', 'Execution'),
        ('complication', 'Complication'),
        ('drug_overdose', 'Drug Overdose'),
        ('asphyxiation', 'Asphyxiation'),
    ]
    class AddressTypeChoices(models.TextChoices):
        MISSING_ADDRESS = 'missing_address', 'MISSING ADDRESS'
        BODY_FOUND = 'body_found', 'BODY FOUND'
        LAST_FOUND = 'last_found', 'LAST FOUND'
        PERMANENT = 'permanent', 'PERMANENT'
        CURRENT = 'current', 'CURRENT'
        OLD = 'old', 'OLD'
        HOME = 'home', 'HOME'
        OFFICE = 'office', 'OFFICE'
        TEMPORARY = 'temporary', 'TEMPORARY'
        BILLING = 'billing', 'BILLING'
        SHIPPING = 'shipping', 'SHIPPING'
        REGISTERED = 'registered', 'REGISTERED'
        MAILING = 'mailing', 'MAILING'
        VACATION = 'vacation', 'VACATION'
        RENTAL = 'rental', 'RENTAL'
        STUDENT = 'student', 'STUDENT'
        FAMILY = 'family', 'FAMILY'
        OTHER = 'other', 'OTHER'

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
        DELHI = 'Delhi', 'Delhi'

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

    Person_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
        ('on_hold', 'On Hold'),
        ('archived', 'Archived'),
    ]
    DNA_MATCH_CHOICES = [
        ('match_found', 'Match Found'),
        ('no_match', 'No Match'),
        ('not_available', 'Not Available'),
        ('pending', 'Pending'),
    ]

    case_id = models.CharField(max_length=30, unique=True, editable=True,blank=True, null=True, db_index=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=TypeChoices.choices,db_index=True)
    full_name = models.CharField(max_length=100,blank=True, null=True,db_index=True)
    birth_date = models.DateField(blank=True, null=True,db_index=True)
    age = models.IntegerField(blank=True, null=True,db_index=True)
    age_range = models.CharField(choices=AGE_RANGE_CHOICES,blank=True, null=True,db_index=True)
    birthtime = models.TimeField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,blank=True, null=True,db_index=True)
    birthplace = models.CharField(max_length=255, null=True, blank=True,db_index=True)
    height = models.IntegerField(help_text="Height in CM",blank=True, null=True,db_index=True)
    height_range = models.CharField(
        max_length=20,
        choices=HEIGHT_RANGE_CHOICES,
        blank=True,
        null=True,
        db_index=True
    )
    weight = models.IntegerField(help_text="Weight in GMS",blank=True, null=True,db_index=True)
    blood_group = models.CharField(max_length=5, choices=BloodGroupChoices.choices,blank=True, null=True,db_index=True)
    complexion = models.CharField(max_length=50, choices=ComplexionChoices.choices,blank=True, null=True,db_index=True)
    hair_color = models.CharField(max_length=50, choices=Hair_colorChoices.choices, blank=True, null=True,db_index=True)
    hair_type = models.CharField(max_length=10, choices=Hair_typeChoices.choices, blank=True, null=True,db_index=True)
    eye_color = models.CharField(max_length=50, choices=Eye_colorChoices.choices, blank=True, null=True,db_index=True)
    condition = models.CharField(max_length=20, choices=ConditionChoices.choices, blank=True, null=True,db_index=True)
    Body_Condition = models.CharField(max_length=50, blank=True, null=True,choices=BodyconditionChoices.choices,db_index=True)
    bodies_condition =models.JSONField(default=list, blank=True)
    up_condition = models.JSONField(default=list, blank=True)
    birth_mark = models.CharField(max_length=100, blank=True, null=True)
    distinctive_mark = models.CharField(max_length=100, blank=True, null=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    document_ids = models.TextField(blank=True, null=True, help_text="Comma-separated document IDs")
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name="created_%(class)s_set",db_index=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_%(class)s_set",db_index=True)
    _is_deleted = models.BooleanField(default=False,db_index=True)
    _is_confirmed = models.BooleanField(default=False,db_index=True)
    photo_photo = models.ImageField(blank=True, null=True,upload_to='All_Photos')
    death_type = models.CharField(
        max_length=20,
        choices=DEATH_TYPE_CHOICES,
        blank=True,
        null=True,

    )
    date_reported = models.DateField(default=date.today)
    case_status = models.CharField(
        max_length=10,
        choices=[
            ('resolved', 'Resolved'),
            ('pending', 'Pending'),
            ('matched', 'Matched')
        ],
        default='pending',
        db_index=True
    )

    address_type = models.CharField(max_length=50, choices=AddressTypeChoices.choices, db_index=True, blank=True,
                                    null=True)

    # Address Details
    street = models.CharField(max_length=50, blank=True, null=True)
    appartment_no = models.CharField(max_length=50, blank=True, null=True)
    appartment_name = models.CharField(max_length=50, blank=True, null=True)
    village = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    district = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=50, choices=StateChoices.choices, db_index=True, blank=True, null=True)
    pincode = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    country = models.CharField(max_length=50, help_text="Country code or ID", choices=CountryChoices.choices,
                               default="India", db_index=True, blank=True, null=True)
    landmark_details = models.CharField(max_length=200, blank=True, null=True)
    location = models.PointField(srid=4326, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    country_code = models.CharField(max_length=10, db_index=True, null=True, blank=True)
    reported_date = models.DateField(default=date.today)
    person_approve_status = models.CharField(max_length=10, choices=Person_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_persons')
    modified_at = models.DateTimeField(auto_now=True)
    status_reason = models.TextField(blank=True, null=True, help_text="Reason for suspension or hold")

    match_entity_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="ID of the matched entity (Missing/Unidentified Person/Body)"
    )

    match_with= models.CharField(
        max_length=20,
        choices=[
            ('Missing Person', 'missing person'),
            ('Unidentified Person', 'unidentified person'),
            ('Unidentified Body', 'unidentified body'),
        ],
        blank=True,
        null=True,
        help_text="The type of the matched entity"
    )
    matched_person_id = models.UUIDField(null=True, blank=True, help_text="UUID of the matched person")
    # below fields for the DNA and mental
    disappearance_type = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    category = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    specific_reason = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    chronic_illness = models.CharField(max_length=255, null=True, blank=True)
    chronic_illnesss = models.JSONField(default=list, blank=True, null=True)
    surgery_implants = models.JSONField(default=list, blank=True, null=True)
    prosthetics_amputation = models.JSONField(default=list, blank=True, null=True)
    healed_fractures = models.JSONField(default=list, blank=True, null=True)
    medical_anomalies = models.JSONField(default=list, blank=True, null=True)
    substance_use = models.JSONField(default=list, blank=True, null=True)
    dental_condition = models.JSONField(default=list, blank=True, null=True)
    lung_bone_pathology = models.JSONField(default=list, blank=True, null=True)

    dna_match = models.CharField(
        max_length=20,
        choices=DNA_MATCH_CHOICES,
        default='pending',
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.case_id:
            self.case_id = self.generate_case_id()
        super().save(*args, **kwargs)

    def generate_case_id(self):
        from django.utils.crypto import get_random_string

        case_type_map = {
            'Missing Person': 'MP',
            'Unidentified Person': 'UP',
            'Unidentified Body': 'UB',
        }

        case_type_code = case_type_map.get(self.type, 'XX')
        report_date = self.reported_date or date.today()
        year_month = report_date.strftime("%Y%m")

        # Normalize city
        normalized_city = self.city.strip() if self.city and self.city.strip() else None
        location_code = (normalized_city[:4].upper() if normalized_city else 'XXX')

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            with transaction.atomic():
                count = Person.objects.filter(
                    type=self.type,
                    city=normalized_city,
                    reported_date__year=report_date.year,
                    reported_date__month=report_date.month
                ).select_for_update().count() + 1

                new_id = f"{case_type_code}-{year_month}-{location_code}-{count:03d}"

                if not Person.objects.filter(case_id=new_id).exists():
                    return new_id

        # Final fallback with random suffix
        random_suffix = get_random_string(4).upper()
        fallback_id = f"{case_type_code}-{year_month}-{location_code}-{random_suffix}"
        return fallback_id

    def __str__(self):
        return f"{self.full_name} ({self.type})"

    class Meta:
        indexes = [
            models.Index(fields=["type","full_name","birth_date","age","gender"]),
            models.Index(fields=["height","weight","blood_group","complexion"]),
            models.Index(fields=["eye_color","hair_type","hair_color","condition"]),
            models.Index(fields=["distinctive_mark","birth_mark","Body_Condition"]),
            models.Index(fields=["hospital","document_ids"]),
            models.Index(fields=["created_by","updated_by"]),
            models.Index(fields=["_is_deleted","_is_confirmed"]),
            models.Index(fields=["match_entity_id"]),
        ]


