

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from datetime import datetime, date

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ..models import Person, Address, Contact, FIR, AdditionalInfo, AdminUser, User, Consent, Document, Hospital, \
    LastKnownDetails, Match, PersonUser, PoliceStation, Volunteer

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        ordering = ['-created_at']
        fields = '__all__'

    
class PersonUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonUser
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

class LastKnownDetailsSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    class Meta:
        model = LastKnownDetails
        fields = '__all__'





class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = '__all__'

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = '__all__'


class AdditionalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalInfo
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class PoliceStationIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliceStation
        fields = ['id', 'name']

class FIRSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    police_station =serializers.StringRelatedField(read_only=True)
    class Meta:
        model = FIR
        fields = '__all__'
        
class HospitalSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(),write_only=True)
    address_details = AddressSerializer(source='address', read_only=True)
    hospital_contact = ContactSerializer(many=True, read_only=True)
    class Meta:
        model = Hospital
        fields = '__all__'





class PoliceStationSerializer(serializers.ModelSerializer):
    station_photo = serializers.ImageField(required=False, allow_null=True)
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(),write_only=True)
    address_details = AddressSerializer(source='address', read_only=True)
    police_contact = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = PoliceStation
        fields = '__all__'

class PersonSerializer(serializers.ModelSerializer):
    birthtime = serializers.TimeField(input_formats=['%I:%M %p', '%H:%M'])
    bodies_condition = serializers.ListField(
        child=serializers.ChoiceField(choices=Person.BodyconditionChoices.choices),
        required=False
    )
    up_condition = serializers.ListField(
        child=serializers.ChoiceField(choices=Person.ConditionChoices.choices),
        required=False
    )
    add_chronic_illness = serializers.ListField(child=serializers.CharField(), required=False)
    surgery_implants = serializers.ListField(child=serializers.CharField(), required=False)
    prosthetics_amputation = serializers.ListField(child=serializers.CharField(), required=False)
    healed_fractures = serializers.ListField(child=serializers.CharField(), required=False)
    medical_anomalies = serializers.ListField(child=serializers.CharField(), required=False)
    substance_use = serializers.ListField(child=serializers.CharField(), required=False)
    dental_condition = serializers.ListField(child=serializers.CharField(), required=False)
    lung_bone_pathology = serializers.ListField(child=serializers.CharField(), required=False)
    category = serializers.SerializerMethodField()
    specific_reason = serializers.SerializerMethodField()

    # to add arrays in persons json
    addresses = AddressSerializer(many=True)
    contacts = ContactSerializer(many=True)
    additional_info = AdditionalInfoSerializer(many=True)
    last_known_details = LastKnownDetailsSerializer(many=True)
    firs = FIRSerializer(many=True)
    consent = ConsentSerializer(many=True)
    # to send particular hospitals entire data
    hospital = HospitalSerializer()
    
    class Meta:
        model = Person
        ordering = ['-created_at']
        fields = '__all__'
        read_only_fields = ['created_by']

    def update(self, instance, validated_data):
        # Prevent clearing created_by
        validated_data.pop('created_by', None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # strip leading/trailing spaces for specific fields
        for field in ["village", "city", "district"]:
            if data.get(field):
                data[field] = data[field].strip()

        return data

    def get_category(self, obj):
        if not obj.category:
            return []
        # If it's already a list, return it directly
        if isinstance(obj.category, list):
            return obj.category
        # If it's a string, try to parse it
        try:
            import ast
            return ast.literal_eval(obj.category)
        except (ValueError, SyntaxError):
            return [x.strip(" '\"") for x in obj.category.split(',') if x.strip()]

    def get_specific_reason(self, obj):
        if not obj.specific_reason:
            return []
        if isinstance(obj.specific_reason, list):
            return obj.specific_reason
        try:
            import ast
            return ast.literal_eval(obj.specific_reason)
        except (ValueError, SyntaxError):
            return [x.strip(" '\"") for x in obj.specific_reason.split(',') if x.strip()]


# short data for search section component
class SearchSerializer(serializers.ModelSerializer):
    missing_date = serializers.SerializerMethodField()

    class Meta:
        model = Person
        ordering = ['-created_at']
        fields = [
            'type', 'case_status', 'id', 'full_name', 'age', 'age_range',
            'city', 'village', 'state', 'gender', 'photo_photo',
            'date_reported', 'missing_date','matched_person_id','confirmed_from'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in ["village", "city", "district"]:
            if data.get(field):
                data[field] = data[field].strip()
        return data

    def get_missing_date(self, obj):
        last_known = obj.last_known_details.first()
        return last_known.missing_date if last_known else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in ["village", "city", "district"]:
            if data.get(field):
                data[field] = data[field].strip()
        return data


class ApprovePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        ordering = ['-created_at']
        fields = ['case_id','id','full_name','type', 'city', 'village', 'state', 'person_approve_status','status_reason','modified_at']


class VolunteerSerializer(serializers.ModelSerializer):
    volunteer_Address = AddressSerializer(many=True)
    volunteer_contact = ContactSerializer(many=True)
    class Meta:
        model = Volunteer
        fields = '__all__'