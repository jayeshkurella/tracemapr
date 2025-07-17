

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""


from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction
from django.contrib.gis.geos import Point

from ..Serializers.serializers import VolunteerSerializer
from ..models import  Volunteer, Address, Contact

import json
import traceback

class VolunteerViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_permissions(self):
        """Allow unrestricted access to `retrieve`, enforce auth on others."""
        if self.action == "retrieve":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def list(self, request):
        try:
            volunteers = Volunteer.objects.prefetch_related('volunteer_Address', 'volunteer_contact').order_by('-created_at')
            serializer = VolunteerSerializer(volunteers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #RETRIEVE a volunteer by ID

    def retrieve(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.prefetch_related('volunteer_Address', 'volunteer_contact').get(pk=pk)
            serializer = VolunteerSerializer(volunteer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)

    #CREATE a new volunteer
    def create(self, request):
        try:
            with transaction.atomic():
                data = self._extract_data(request)
                # Extract related data
                addresses_data = data.pop("volunteer_Address", [])
                contacts_data = data.pop("volunteer_contact", [])

                # Create Volunteer instance
                volunteer = Volunteer.objects.create(**data)

                # Correctly create related models
                self._create_addresses(volunteer, addresses_data)
                self._create_contacts(volunteer, contacts_data)

                serializer = VolunteerSerializer(volunteer)
                return Response({"message": "Volunteer created successfully", "data": serializer.data},
                                status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # UPDATE a volunteer (full update)
    def update(self, request, pk=None):
        try:
            with transaction.atomic():
                volunteer = Volunteer.objects.get(pk=pk)
                data = self._extract_data(request)

                # Update Volunteer fields
                for key, value in data.items():
                    setattr(volunteer, key, value)
                volunteer.save()

                # Update related addresses
                if 'volunteer_Address' in data:
                    volunteer.addresses.all().delete()
                    self._create_addresses(volunteer, data['volunteer_Address'])

                # Update related contacts
                if 'contacts' in data:
                    volunteer.contacts.all().delete()
                    self._create_contacts(volunteer, data['contacts'])

                serializer = VolunteerSerializer(volunteer)
                return Response({'message': 'Volunteer updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # PARTIAL UPDATE a volunteer
    def partial_update(self, request, pk=None):
        try:
            with transaction.atomic():
                volunteer = Volunteer.objects.get(pk=pk)
                data = self._extract_data(request)

                # Partially update Volunteer fields
                for key, value in data.items():
                    if key not in ['volunteer_Address', 'volunteer_contact']:  # Skip related fields
                        setattr(volunteer, key, value)
                volunteer.save()

                # Partially update related addresses
                if 'volunteer_Address' in data:
                    self._update_or_create_addresses(volunteer, data['volunteer_Address'])

                # Partially update related contacts
                if 'volunteer_contact' in data:
                    self._update_or_create_contacts(volunteer, data['volunteer_contact'])

                serializer = VolunteerSerializer(volunteer)
                return Response({'message': 'Volunteer partially updated successfully', 'data': serializer.data},
                                status=status.HTTP_200_OK)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # DELETE a volunteer (soft delete)

    def destroy(self, request, pk=None):
        try:
            volunteer = Volunteer.objects.get(pk=pk)
            volunteer.delete()
            return Response({'message': 'Volunteer deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Volunteer.DoesNotExist:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Helper Methods
    def _extract_data(self, request):
        """Extracts JSON data, supporting multipart/form-data"""
        if request.content_type == "application/json":
            return request.data
        elif request.content_type.startswith("multipart/form-data"):
            payload_str = request.POST.get("payload", "{}")
            return json.loads(payload_str)
        elif request.content_type == "application/x-www-form-urlencoded":
            return request.POST.dict()  # Convert form data to dictionary
        else:
            raise ParseError("Unsupported media type")

    def _create_addresses(self, volunteer, addresses_data):
        """Creates addresses related to a volunteer with location handling"""
        addresses = []
        for addr in addresses_data:
            if addr:
                # Extract location if present
                location_data = addr.pop("location", None)

                if location_data and "latitude" in location_data and "longitude" in location_data:
                    latitude = location_data["latitude"]
                    longitude = location_data["longitude"]
                    addr["location"] = Point(float(longitude), float(latitude))  # Longitude first!

                addresses.append(Address(volunteer=volunteer, **addr))

        Address.objects.bulk_create(addresses)

    def _create_contacts(self, volunteer, contacts_data):
        """Creates contacts related to a volunteer"""
        contacts = [Contact(volunteer=volunteer, **contact) for contact in contacts_data if contact]
        Contact.objects.bulk_create(contacts)

    def _update_or_create_addresses(self, volunteer, addresses_data):
        """Updates existing addresses or creates new ones"""
        address_instances = []

        for address_data in addresses_data:
            address_id = address_data.get("id")

            # Handle location data
            location_data = address_data.pop("location", None)
            if location_data:
                address_data["location"] = Point(float(location_data["longitude"]), float(location_data["latitude"]))

            if address_id:
                # Update existing address
                address = Address.objects.filter(id=address_id, volunteer=volunteer).first()
                if address:
                    for key, value in address_data.items():
                        setattr(address, key, value)
                    address.save()
                    address_instances.append(address)
            else:
                # Create new address
                address = Address.objects.create(volunteer=volunteer, **address_data)
                address_instances.append(address)

        # Get all existing addresses for this volunteer
        existing_addresses = volunteer.volunteer_Address.all()

        # Delete addresses that weren't included in the update
        addresses_to_delete = existing_addresses.exclude(id__in=[addr.id for addr in address_instances if addr.id])
        addresses_to_delete.delete()

    def _update_or_create_contacts(self, volunteer, contacts_data):
        """Updates existing contacts or creates new ones"""
        contact_instances = []

        for contact_data in contacts_data:
            contact_id = contact_data.get('id')

            if contact_id:
                # Update existing contact
                contact = Contact.objects.filter(id=contact_id, volunteer=volunteer).first()
                if contact:
                    for key, value in contact_data.items():
                        setattr(contact, key, value)
                    contact.save()
                    contact_instances.append(contact)
            else:
                # Create new contact
                contact = Contact.objects.create(volunteer=volunteer, **contact_data)
                contact_instances.append(contact)

        # Get all existing contacts for this volunteer
        existing_contacts = volunteer.volunteer_contact.all()

        # Delete contacts that weren't included in the update
        contacts_to_delete = existing_contacts.exclude(
            id__in=[contact.id for contact in contact_instances if contact.id])
        contacts_to_delete.delete()