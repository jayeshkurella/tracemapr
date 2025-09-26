
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from django.utils import timezone

import logging
import threading
from uuid import UUID
from dateutil import parser
from django.db.models import Q
from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from ..Emails import case_pending
from ..Emails.Case_submit import send_submission_email
from ..Emails.case_approval import send_case_approval_email
from ..Emails.case_hold import send_case_to_hold_email
from ..Emails.case_pending import send_case_back_to_pending_email
from ..Emails.case_suspend import send_case_to_suspend_email
from ..all_paginations.search_case import searchCase_Pagination
from ..models.fir import FIR
from ..access_permision import IsAdminUser
from Mainapp.all_paginations.pagination import CustomPagination
from ..Serializers.serializers import PersonSerializer, SearchSerializer
from ..models import Person, Address, Contact, AdditionalInfo, LastKnownDetails, Consent, PoliceStation, \
    Hospital, Document
from django.db import transaction, IntegrityError
from drf_yasg import openapi
from django.contrib.gis.geos import Point
import json
import traceback

logger = logging.getLogger(__name__)


class PersonViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]  # Require token authentication
    permission_classes = [IsAuthenticated]

    parser_classes = (MultiPartParser, FormParser,JSONParser)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        logger.debug("Getting queryset for Person objects")
        return Person.objects.all().order_by('-modified_at', '-id')

    def get_permissions(self):
        """
        Allow unrestricted access to specific public actions.
        Enforce authentication for other actions.
        """
        logger.debug(f"Getting permissions for action: {self.action}")
        if self.action in [
            "retrieve",
            "retrieve_by_case_id",
            "missing_persons",
            "unidentified_persons",
            "unidentified_bodies"
        ]:
            logger.info(f"Allowing public access for action: {self.action}")
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

        #  1. LIST all persons

    def list(self, request):
        logger.info(f"LIST request received from user: {request.user}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Request query params: {dict(request.query_params)}")
        try:
            # Get and order the queryset
            queryset = Person.objects.filter(_is_deleted=False,person_approve_status='approved').prefetch_related(
                'addresses', 'contacts', 'additional_info',
                'last_known_details', 'firs', 'consent'
            ).order_by('-created_at')

            logger.debug(f"Queryset count before pagination: {queryset.count()}")

            # Pagination
            paginator = CustomPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            if not paginated_queryset:
                logger.info("No persons found in the database")
                return Response({'message': 'No persons found'}, status=status.HTTP_200_OK)

            # Serialize and respond
            serializer = PersonSerializer(paginated_queryset, many=True)
            logger.info(f"Successfully retrieved {len(paginated_queryset)} persons")
            logger.debug(f"Serialized data: {serializer.data[:2]}")
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Error in LIST operation: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Better error handling and logging
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    #  2. RETRIEVE a person by ID
    def retrieve(self, request, pk=None):
        logger.info(f"RETRIEVE request for person ID: {pk} from user: {request.user}")
        try:
            person = Person.objects.filter(_is_deleted=False,person_approve_status='approved').prefetch_related(
                'addresses', 'contacts', 'additional_info', 'last_known_details', 'firs','consent').get(pk=pk)
            logger.debug(f"Found person: {person.full_name} (ID: {person.id})")
            serializer = PersonSerializer(person)
            logger.info(f"Successfully retrieved person ID: {pk}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found or not approved")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='retrieve-unfiltered', permission_classes=[IsAdminUser])
    def retrieve_unfiltered(self, request, pk=None):
        logger.info(f"RETRIEVE UNFILTERED request for person ID: {pk} from admin: {request.user}")

        try:
            person = Person.objects.filter(_is_deleted=False).prefetch_related(
                'addresses', 'contacts', 'additional_info', 'last_known_details', 'firs','consent').get(pk=pk)
            logger.debug(f"Found unfiltered person: {person.full_name} (Status: {person.person_approve_status})")

            serializer = PersonSerializer(person)
            logger.info(f"Successfully retrieved unfiltered person ID: {pk}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error retrieving unfiltered person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #  3. CREATE a new person
    def create(self, request):
        logger.info(f"CREATE request received from user: {request.user}")
        logger.debug(f"Request content-type: {request.content_type}")
        logger.debug(f"Request FILES keys: {list(request.FILES.keys()) if request.FILES else 'None'}")
        logger.debug(
            f"Request DATA keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'No data keys'}")
        # print("data comes", request.data)
        try:
            with transaction.atomic():
                # Step 1: Parse JSON from "payload"
                if request.content_type == 'application/json':
                    data = request.data
                    logger.debug("Processing JSON content-type request")
                elif request.content_type.startswith('multipart/form-data'):
                    logger.debug("Processing multipart/form-data request")
                    if 'payload' in request.FILES:
                        payload_file = request.FILES['payload']
                        try:
                            payload_str = payload_file.read().decode('utf-8')
                            data = json.loads(payload_str)
                            logger.debug(f"Incoming data from angular: {json.dumps(data, indent=2)}")
                            print("Incoming data from angular:", data)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {str(e)}")
                            return Response({'error': 'Invalid JSON in payload'},status=status.HTTP_400_BAD_REQUEST)
                    else:
                        logger.warning("Missing payload in multipart request")
                        return Response({'error': 'Missing payload in request'},    status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.warning(f"Unsupported media type: {request.content_type}")
                    return Response({'error': 'Unsupported media type'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

                logger.debug("Extracted JSON Data: %s", json.dumps(data, indent=4))
                data['photo_photo'] = request.FILES.get('photo_photo')
                logger.debug(f"Photo file: {'Present' if data['photo_photo'] else 'Not present'}")


                # Extract related data
                addresses_data = [addr for addr in data.get('addresses', []) if any(addr.values())]
                contacts_data = [contact for contact in data.get('contacts', []) if any(contact.values())]
                additional_info_data = [info for info in data.get('additional_info', []) if any(info.values())]
                last_known_details_data = [details for details in data.get('last_known_details', []) if
                                           any(details.values())]
                firs_data = [fir for fir in data.get('firs', []) if any(fir.values())]
                consents_data = [consent for consent in data.get('consent', []) if any(consent.values())]

                logger.debug("Filtered Addresses Data: %s", json.dumps(addresses_data, indent=4))
                logger.debug(f"Filtered Addresses Data count: {len(addresses_data)}")
                logger.debug(f"Contacts Data count: {len(contacts_data)}")
                logger.debug(f"Additional Info Data count: {len(additional_info_data)}")
                logger.debug(f"Last Known Details Data count: {len(last_known_details_data)}")
                logger.debug(f"FIRs Data count: {len(firs_data)}")
                logger.debug(f"Consents Data count: {len(consents_data)}")

                # Extract hospital instance (if any)
                hospital_id = data.get('hospital')
                hospital = None
                if hospital_id:
                    try:
                        hospital = Hospital.objects.get(id=hospital_id)
                        logger.debug(f"Associated hospital: {hospital.name}")
                    except Hospital.DoesNotExist:
                        logger.error(f"Hospital with ID {hospital_id} does not exist")
                        raise ValueError(f"Hospital with ID {hospital_id} does not exist")

                # Step 2: Create Person
                person_data = {
                    k: v for k, v in data.items()
                    if v not in [None, "", []] and k not in [
                        'addresses', 'contacts', 'additional_info', 'last_known_details', 'firs', 'consent', 'hospital'
                    ]
                }
                # print("Creating person with data:", person_data)
                logger.debug(f"Creating person with data: {person_data}")
                person = Person(**person_data, hospital=hospital,created_by=request.user)

                # Extract zero index address and store it directly in the person model
                if addresses_data:
                    first_address = addresses_data[0]
                    person.address_type = first_address.get('address_type', '')
                    person.appartment_name = first_address.get('appartment_name', '')
                    person.appartment_no = first_address.get('appartment_no', '')
                    person.street = first_address.get('street', '')
                    person.village = first_address.get('village', '')
                    person.landmark_details = first_address.get('landmark_details', '')
                    person.pincode = first_address.get('pincode', '')
                    person.city = first_address.get('city', '')
                    person.district = first_address.get('district', '')
                    person.state = first_address.get('state', '')
                    person.country = first_address.get('country', '')
                    location_data = first_address.get('location', {})
                    raw_lat = location_data.get('latitude')
                    raw_lon = location_data.get('longitude')

                    try:
                        lat = float(str(raw_lat).strip())
                        lon = float(str(raw_lon).strip())

                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            raise ValueError("Latitude must be between -90 and 90, and longitude between -180 and 180.")

                        person.location = Point(lon, lat)
                        logger.debug(f"Set location coordinates: lon={lon}, lat={lat}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid coordinates provided: {e}")
                        raise ValueError(f"Invalid coordinates provided: {e}")

                    person.save()
                    print("Person saved:", person.id)
                    logger.info(f"Person saved successfully with ID: {person.id}")
                    reporter_name = f"{request.user.first_name} {request.user.last_name}".strip()
                    logger.debug(f"Reporter name: {reporter_name}")


                # Create related objects
                self._create_addresses(person, addresses_data[1:])
                self._create_contacts(person, contacts_data)
                self._create_additional_info(person, additional_info_data)
                self._create_last_known_details(person, last_known_details_data,request)
                self._create_firs(person, firs_data,request)
                self._create_consents(person, consents_data)

                # Prepare response
                serializer = PersonSerializer(person)
                logger.info(f"Person created successfully: {person.full_name} (ID: {person.id})")
                response = Response(
                    {'message': 'Person created successfully', 'person_id': str(person.id), 'data': serializer.data},
                    status=status.HTTP_201_CREATED
                )
                # Send email in background
                threading.Thread(
                    target=send_submission_email,
                    kwargs={
                        'user_email': request.user,
                        'reporter_name': reporter_name,
                        'full_name': person.full_name,
                        'case_id': person.case_id,
                        'type': person.type,
                        'submitted_at': person.created_at.strftime("%d/%m/%Y, %I:%M:%S %p")
                    }
                ).start()

                logger.info("Email submission thread started")

                return response

        except ValueError as e:
            logger.error("Validation error: %s", str(e))
            return Response({'error': f'Validation error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Exception Occurred: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _create_addresses(self, person, addresses_data):
        logger.debug(f"Creating {len(addresses_data)} additional addresses")
        addresses = []
        for address in addresses_data:
            lat = address.get('location', {}).get('latitude')
            lon = address.get('location', {}).get('longitude')
            point = None
            if lat and lon:
                try:
                    lat = float(lat)
                    lon = float(lon)
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        raise ValueError("Latitude must be between -90 and 90, and longitude between -180 and 180.")
                    point = Point(lon, lat)
                    logger.debug(f"Address location: lon={lon}, lat={lat}")
                except ValueError as e:
                    logger.warning(f"Invalid location data: {e}")
                    raise ValueError(f"Invalid location data: {e}")

            address_obj = Address(
                person=person,
                location=point,
                **{k: v for k, v in address.items() if k not in ['location', 'person']}
            )
            addresses.append(address_obj)
        Address.objects.bulk_create(addresses)
        logger.info(f"Created {len(addresses)} additional addresses")

    def _create_contacts(self, person, contacts_data):
        logger.debug(f"Creating {len(contacts_data)} contacts")
        contacts = [
            Contact(person=person, **{k: v for k, v in contact.items() if k != 'person'})
            for contact in contacts_data
        ]
        Contact.objects.bulk_create(contacts)
        logger.info(f"Created {len(contacts)} contacts")

    def _create_additional_info(self, person, additional_info_data):
        logger.debug(f"Creating {len(additional_info_data)} additional info records")
        additional_info = [
            AdditionalInfo(person=person, **{k: v for k, v in info.items() if k != 'person'})
            for info in additional_info_data if isinstance(info, dict)
        ]
        AdditionalInfo.objects.bulk_create(additional_info)
        logger.info(f"Created {len(additional_info)} additional info records")

    def _create_last_known_details(self, person, last_known_details_data, request):
        logger.debug(f"Creating {len(last_known_details_data)} last known details")
        successful_details = []

        for detail_index, detail_data in enumerate(last_known_details_data):
            if not isinstance(detail_data, dict):
                logger.warning(f"Invalid detail data at index {detail_index}: Not a dictionary")
                continue
            try:
                # Create LastKnownDetails instance
                detail_instance = LastKnownDetails(
                    person=person,
                    missing_date=detail_data.get('missing_date'),
                    missing_time=detail_data.get('missing_time'),
                    last_seen_location=detail_data.get('last_seen_location'),
                    missing_location_details=detail_data.get('missing_location_details')
                )
                detail_instance.full_clean()
                print(f"Saving LastKnownDetails {detail_index}: {detail_data}")
                logger.debug(f"Saving LastKnownDetails {detail_index}: {detail_data}")
                detail_instance.save()

                # Process documents
                documents_meta = detail_data.get('documents', [])
                logger.debug(f"Processing {len(documents_meta)} documents for detail {detail_index}")

                for doc_index, doc_meta in enumerate(documents_meta):
                    # Get the file from request.FILES
                    file_key = f'documents[{detail_index}][{doc_index}][document]'
                    document_file = request.FILES.get(file_key)
                    description = doc_meta.get('description', '')
                    # Create and save Document instance immediately
                    document = Document(
                        last_known_detail=detail_instance,
                        person_type=doc_meta.get('person_type', ''),
                        description=description,
                        document_type=doc_meta.get('document_type', ''),
                        created_by=request.user
                    )

                    # Save the instance first to get an ID

                    document.save()
                    logger.debug(f"Created document {doc_index} for detail {detail_index}")

                    # Attach the file if it exists
                    if document_file:
                        document.document.save(document_file.name, document_file)
                        logger.debug(f"Attached file to document {doc_index}")
                successful_details.append(detail_instance)

            except Exception as e:
                logger.error(f"Failed at index {detail_index}: {str(e)}")
                continue

        logger.info(f"Successfully created {len(successful_details)} last known details")
        return successful_details

    def _create_firs(self, person, firs_data, request):
        """
        Create FIR records with associated documents.
        - Associates FIRs with a police station (if provided)
        - Handles file uploads from request.FILES
        - Processes documents individually to avoid bulk_create issues with files
        """

        logger.debug(f"Creating {len(firs_data)} FIR records")
        successful_firs = []

        for fir_index, fir in enumerate(firs_data):
            if not isinstance(fir, dict):
                logger.warning(f"Invalid FIR data at index {fir_index}: Not a dictionary")
                continue

            try:
                # Extract document metadata
                documents_meta = fir.pop('documents', [])
                logger.debug(f"FIR {fir_index} has {len(documents_meta)} documents")

                # Handle police station association
                police_station_id = fir.get('police_station')
                police_station = None
                if police_station_id:
                    try:
                        police_station = PoliceStation.objects.get(id=police_station_id)

                        logger.debug(f"Associated police station: {police_station.name}")
                    except PoliceStation.DoesNotExist:
                        logger.error(f"PoliceStation with ID {police_station_id} does not exist")
                        raise ValueError(f"PoliceStation with ID {police_station_id} does not exist")

                # Create FIR instance
                fir_obj = FIR(
                    person=person,
                    police_station=police_station,
                    **{k: v for k, v in fir.items()
                       if k not in ['police_station', 'person', 'document']}
                )
                fir_obj.full_clean()
                fir_obj.save()
                logger.debug(f"Created FIR {fir_index}")

                # Process documents individually
                for doc_index, doc_meta in enumerate(documents_meta):
                    # Get file from request.FILES
                    file_key = f'firs[{fir_index}][documents][{doc_index}][document]'
                    document_file = request.FILES.get(file_key)
                    description = doc_meta.get('description', '')

                    # Create Document instance
                    document = Document(
                        fir=fir_obj,
                        person_type=doc_meta.get('person_type', ''),
                        description=description,
                        document_type=doc_meta.get('document_type', ''),
                        created_by=request.user
                    )

                    document.save()

                    # Attach file if exists
                    if document_file:
                        document.document.save(document_file.name, document_file)
                        logger.debug(f"Attached file to FIR document {doc_index}")

                successful_firs.append(fir_obj)

            except Exception as e:
                logger.error(f"FIR creation failed at index {fir_index}: {str(e)}")
                continue

        logger.info(f"Successfully created {len(successful_firs)} FIR records")
        return successful_firs

    def _create_consents(self, person, consents_data):
        logger.debug(f"Creating {len(consents_data)} consent records")
        consents = [
            Consent(person=person, **{k: v for k, v in consent.items() if k != 'person'})
            for consent in consents_data
        ]
        Consent.objects.bulk_create(consents)
        logger.info(f"Created {len(consents)} consent records")


    # To update the records
    def update(self, request, pk=None):
        logger.info(f"UPDATE request for person ID: {pk} from user: {request.user}")
        logger.debug(f"Request data: {request.data}")
        logger.debug(f"Request FILES: {dict(request.FILES)}")

        print(request.data)

        try:
            with transaction.atomic():
                person = Person.objects.get(pk=pk)
                logger.debug(f"Found person to update: {person.full_name}")
                # Extract content from request

                if request.content_type == 'application/json':
                    data = request.data
                    logger.debug("Processing JSON content-type update request")
                elif request.content_type.startswith('multipart/form-data'):
                    logger.debug("Processing multipart/form-data update request")
                    if 'payload' in request.FILES:
                        payload_str = request.FILES['payload'].read().decode('utf-8')
                        data = json.loads(payload_str)
                    else:
                        logger.warning("Missing payload in multipart update request")
                        return Response({'error': 'Missing payload in request'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.warning(f"Unsupported media type for update: {request.content_type}")
                    return Response({'error': 'Unsupported media type'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

                    # Handle photo_photo field
                new_photo = request.FILES.get('photo_photo')
                if new_photo:
                    logger.debug("New photo uploaded for update")
                    # New photo uploaded - use it
                    data['photo_photo'] = new_photo
                elif hasattr(person, 'photo_photo') and person.photo_photo:
                    logger.debug("Keeping existing photo")
                    # Keep existing photo if no new one was uploaded
                    data['photo_photo'] = person.photo_photo.name  # This gives the proper media path
                else:
                    logger.debug("No photo provided")
                    # No photo at all - set to None
                    data['photo_photo'] = None

                addresses_data = data.get('addresses', [])
                contacts_data = data.get('contacts', [])
                additional_info_data = data.get('additional_info', [])
                last_known_details_data = data.get('last_known_details', [])
                firs_data = data.get('firs', [])
                consents_data = data.get('consent', [])
                logger.debug(f"Update data counts - Addresses: {len(addresses_data)}, Contacts: {len(contacts_data)}")

                hospital_data = data.get('hospital')
                hospital_id = hospital_data.get('id') if isinstance(hospital_data, dict) else hospital_data

                if hospital_data is None:
                    logger.debug("Clearing hospital association")
                    # If payload explicitly sent null → clear the hospital
                    person.hospital = None
                else:
                    # If payload has a hospital id → update it
                    if hospital_id:
                        if not person.hospital or str(person.hospital.id) != str(hospital_id):
                            try:
                                person.hospital = Hospital.objects.get(id=hospital_id)
                                logger.debug(f"Updated hospital to: {person.hospital.name}")
                            except Hospital.DoesNotExist:
                                logger.error(f"Hospital with ID {hospital_id} does not exist")
                                raise ValueError(f"Hospital with ID {hospital_id} does not exist")


                # Update top-level fields - exclude photo_photo if it wasn't in the original data
                person_data = {
                    k: v for k, v in data.items()
                    if k not in ['addresses', 'contacts', 'additional_info', 'last_known_details', 'firs', 'consent',
                                 'hospital']
                }

                for key, value in person_data.items():
                    # Only update fields that are actually in the payload or have new values
                    if value is not None or key in data:
                        setattr(person, key, value)
                        logger.debug(f"Updated person field: {key} = {value}")


                # Update top-level address info from first address
                if addresses_data:
                    addr = addresses_data[0]
                    person.address_type = addr.get('address_type', '')
                    person.appartment_name = addr.get('appartment_name', '')
                    person.appartment_no = addr.get('appartment_no', '')
                    person.street = addr.get('street', '')
                    person.village = addr.get('village', '')
                    person.landmark_details = addr.get('landmark_details', '')
                    person.pincode = addr.get('pincode', '')
                    person.city = addr.get('city', '')
                    person.district = addr.get('district', '')
                    person.state = addr.get('state', '')
                    person.country = addr.get('country', '')
                    location_data = addr.get('location', {})
                    try:
                        lat = float(str(location_data.get('latitude')).strip())
                        lon = float(str(location_data.get('longitude')).strip())
                        person.location = Point(lon, lat)
                        logger.debug(f"Updated location coordinates: lon={lon}, lat={lat}")
                    except:
                        logger.warning("Failed to update location coordinates")
                        pass

                person.save()
                logger.debug("Person saved with updated fields")

                # Update nested data
                self._update_addresses(person, addresses_data[1:])
                self._update_contacts(person, contacts_data)
                self._update_additional_info(person, additional_info_data)
                self._update_last_known_details(person, last_known_details_data)
                self._update_firs(person, firs_data)
                self._update_consents(person, consents_data)

                serializer = PersonSerializer(person)
                logger.info(f"Successfully updated person ID: {pk}")
                return Response({'message': 'Person updated successfully', 'data': serializer.data},
                                status=status.HTTP_200_OK)

        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for update")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(str(e))
            logger.error(f"Error updating person ID {pk}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _update_addresses(self, person, addresses_data):
        logger.debug(f"Updating {len(addresses_data)} addresses")
        for address in addresses_data:
            addr_id = address.get('id')
            location = address.get('location', {})
            point = None
            try:
                lat = float(location.get('latitude'))
                lon = float(location.get('longitude'))
                point = Point(lon, lat)
                logger.debug(f"Address location: lon={lon}, lat={lat}")
            except:
                logger.warning("Invalid address location data")
                pass

            address_data = {k: v for k, v in address.items() if k not in ['id', 'location', 'person']}
            address_data['location'] = point

            if addr_id:
                try:
                    addr_obj = Address.objects.get(id=addr_id, person=person)
                    for key, value in address_data.items():
                        setattr(addr_obj, key, value)
                    addr_obj.save()
                    logger.debug(f"Updated address ID: {addr_id}")
                except Address.DoesNotExist:
                    logger.warning(f"Address with ID {addr_id} not found")
                    continue
            else:
                Address.objects.create(person=person, **address_data)
                logger.debug("Created new address")

    def _update_contacts(self, person, contacts_data):
        logger.debug(f"Updating {len(contacts_data)} contacts")
        for contact in contacts_data:
            contact_id = contact.get('id')
            contact_data = {k: v for k, v in contact.items() if k != 'id' and k != 'person'}

            if contact_id:
                try:
                    contact_obj = Contact.objects.get(id=contact_id, person=person)
                    for key, value in contact_data.items():
                        setattr(contact_obj, key, value)
                    contact_obj.save()
                    logger.debug(f"Updated contact ID: {contact_id}")
                except Contact.DoesNotExist:
                    logger.warning(f"Contact with ID {contact_id} not found")
                    continue
            else:
                Contact.objects.create(person=person, **contact_data)
                logger.debug("Created new contact")

    def _update_additional_info(self, person, additional_info_data):
        logger.debug(f"Updating {len(additional_info_data)} additional info records")
        for info in additional_info_data:
            if not isinstance(info, dict):
                logger.warning("Invalid additional info data format")
                continue

            info_id = info.get('id')
            info_data = {k: v for k, v in info.items() if k != 'id' and k != 'person'}

            if info_id:
                try:
                    info_obj = AdditionalInfo.objects.get(id=info_id, person=person)
                    for key, value in info_data.items():
                        setattr(info_obj, key, value)
                    info_obj.save()
                    logger.debug(f"Updated additional info ID: {info_id}")
                except AdditionalInfo.DoesNotExist:
                    logger.warning(f"AdditionalInfo with ID {info_id} not found")
                    continue
            else:
                AdditionalInfo.objects.create(person=person, **info_data)
                logger.debug("Created new additional info")

    def _update_last_known_details(self, person, last_known_details_data):
        logger.debug(f"Updating {len(last_known_details_data)} last known details")

        for detail_idx, details in enumerate(last_known_details_data):
            detail_id = details.get('id')
            documents_data = details.pop('documents', [])
            detail_data = {k: v for k, v in details.items()
                           if k not in ['id', 'person', 'documents']}

            if detail_id:
                try:
                    detail_obj = LastKnownDetails.objects.get(id=detail_id, person=person)
                    # Update basic fields
                    for key, value in detail_data.items():
                        setattr(detail_obj, key, value)
                    detail_obj.save()
                    logger.debug(f"Updated last known detail ID: {detail_id}")

                    # Handle documents - process all documents data
                    existing_doc_ids = []
                    for doc_idx, doc_data in enumerate(documents_data):
                        doc_id = doc_data.get('id')

                        # Existing document - update metadata and/or file
                        if doc_id:
                            try:
                                doc_obj = Document.objects.get(id=doc_id, last_known_detail=detail_obj)

                                # Update document metadata if provided
                                if 'document_type' in doc_data:
                                    doc_obj.document_type = doc_data.get('document_type')
                                if 'description' in doc_data:
                                    doc_obj.description = doc_data.get('description')

                                # Handle file upload if provided
                                file_key = f"last_known_details[{detail_idx}][documents][{doc_idx}][document]"
                                if file_key in self.request.FILES:
                                    doc_file = self.request.FILES[file_key]
                                    doc_obj.document = doc_file

                                doc_obj.save()
                                existing_doc_ids.append(doc_id)
                                logger.debug(f"Updated document ID: {doc_id}")

                            except Document.DoesNotExist:
                                logger.warning(f"Document with ID {doc_id} not found")
                                continue

                        # New document upload (only create if file is provided)
                        else:
                            file_key = f"last_known_details[{detail_idx}][documents][{doc_idx}][document]"
                            if file_key in self.request.FILES:
                                doc_file = self.request.FILES[file_key]
                                doc = Document.objects.create(
                                    person_type="missing person",
                                    document_type=doc_data.get('document_type', 'other'),
                                    description=doc_data.get('description', ''),
                                    document=doc_file,
                                    last_known_detail=detail_obj,
                                    created_by=self.request.user
                                )
                                existing_doc_ids.append(doc.id)
                                logger.debug(f"Created new document ID: {doc.id}")

                            # If no file but metadata exists, don't create empty document
                            elif doc_data.get('document_type') or doc_data.get('description'):
                                # Optional: Create document without file if metadata exists
                                doc = Document.objects.create(
                                    person_type="missing person",
                                    document_type=doc_data.get('document_type', 'other'),
                                    description=doc_data.get('description', ''),
                                    last_known_detail=detail_obj,
                                    created_by=self.request.user
                                )
                                existing_doc_ids.append(doc.id)
                                logger.debug(f"Created new document without file ID: {doc.id}")

                    # Remove documents that are no longer in the list
                    detail_obj.documents.exclude(id__in=existing_doc_ids).delete()

                except LastKnownDetails.DoesNotExist:
                    logger.warning(f"LastKnownDetails with ID {detail_id} not found")
                    continue
            else:
                # Create new last known detail with documents
                detail_obj = LastKnownDetails.objects.create(person=person, **detail_data)
                logger.debug(f"Created new last known detail ID: {detail_obj.id}")

                # Handle document creation
                existing_doc_ids = []
                for doc_idx, doc_data in enumerate(documents_data):
                    file_key = f"last_known_details[{detail_idx}][documents][{doc_idx}][document]"
                    if file_key in self.request.FILES:
                        doc_file = self.request.FILES[file_key]
                        doc = Document.objects.create(
                            person_type="missing person",
                            document_type=doc_data.get('document_type', 'other'),
                            description=doc_data.get('description', ''),
                            document=doc_file,
                            last_known_detail=detail_obj,
                            created_by=self.request.user
                        )
                        existing_doc_ids.append(doc.id)
                        logger.debug(f"Created new document with file ID: {doc.id}")

                    # Create document without file if only metadata is provided
                    elif doc_data.get('document_type') or doc_data.get('description'):
                        doc = Document.objects.create(
                            person_type="missing person",
                            document_type=doc_data.get('document_type', 'other'),
                            description=doc_data.get('description', ''),
                            last_known_detail=detail_obj,
                            created_by=self.request.user
                        )
                        existing_doc_ids.append(doc.id)
                        logger.debug(f"Created new document without file ID: {doc.id}")

    def _update_firs(self, person, firs_data):
        logger.debug(f"Updating {len(firs_data)} FIR records")
        for fir_idx, fir in enumerate(firs_data):
            fir_id = fir.get('id')
            police_station_id = fir.get('police_station')
            police_station = None
            if police_station_id:
                try:
                    police_station = PoliceStation.objects.get(id=police_station_id)
                    logger.debug(f"Police station: {police_station.name}")
                except PoliceStation.DoesNotExist:
                    logger.error(f"PoliceStation with ID {police_station_id} does not exist")
                    raise ValueError(f"PoliceStation with ID {police_station_id} does not exist")

            documents_data = fir.pop('documents', [])
            fir_data = {
                k: v for k, v in fir.items()
                if k not in ['id', 'person', 'documents', 'police_station']
            }

            if fir_id:
                try:
                    fir_obj = FIR.objects.get(id=fir_id, person=person)
                    # Update basic fields
                    for key, value in fir_data.items():
                        setattr(fir_obj, key, value)
                    fir_obj.police_station = police_station
                    fir_obj.save()
                    logger.debug(f"Updated FIR ID: {fir_id}")

                    # Handle documents - process all documents data
                    existing_doc_ids = []
                    for doc_idx, doc_data in enumerate(documents_data):
                        doc_id = doc_data.get('id')

                        # Existing document - update metadata and/or file
                        if doc_id:
                            try:
                                doc_obj = Document.objects.get(id=doc_id, fir=fir_obj)

                                # Update document metadata if provided
                                if 'document_type' in doc_data:
                                    doc_obj.document_type = doc_data.get('document_type')
                                if 'description' in doc_data:
                                    doc_obj.description = doc_data.get('description')

                                # Handle file upload if provided
                                file_key = f"firs[{fir_idx}][documents][{doc_idx}][document]"
                                if file_key in self.request.FILES:
                                    doc_file = self.request.FILES[file_key]
                                    doc_obj.document = doc_file

                                doc_obj.save()
                                existing_doc_ids.append(doc_id)
                                logger.debug(f"Updated FIR document ID: {doc_id}")

                            except Document.DoesNotExist:
                                logger.warning(f"FIR Document with ID {doc_id} not found")
                                continue

                        # New document upload (only create if file is provided)
                        else:
                            file_key = f"firs[{fir_idx}][documents][{doc_idx}][document]"
                            if file_key in self.request.FILES:
                                doc_file = self.request.FILES[file_key]
                                doc = Document.objects.create(
                                    person_type="missing person",
                                    document_type=doc_data.get('document_type', 'fir_attachment'),
                                    description=doc_data.get('description', ''),
                                    document=doc_file,
                                    fir=fir_obj,
                                    created_by=self.request.user
                                )
                                existing_doc_ids.append(doc.id)
                                logger.debug(f"Created new FIR document ID: {doc.id}")
                            # If no file but metadata exists, don't create empty document
                            elif doc_data.get('document_type') or doc_data.get('description'):
                                # Optional: Create document without file if metadata exists
                                doc = Document.objects.create(
                                    person_type="missing person",
                                    document_type=doc_data.get('document_type', 'fir_attachment'),
                                    description=doc_data.get('description', ''),
                                    fir=fir_obj,
                                    created_by=self.request.user
                                )
                                existing_doc_ids.append(doc.id)
                                logger.debug(f"Created new FIR document without file ID: {doc.id}")

                    # Remove documents that are no longer in the list
                    fir_obj.documents.exclude(id__in=existing_doc_ids).delete()

                except FIR.DoesNotExist:
                    logger.warning(f"FIR with ID {fir_id} not found")
                    continue
            else:
                # Create new FIR with documents
                fir_obj = FIR.objects.create(person=person, police_station=police_station, **fir_data)
                logger.debug(f"Created new FIR ID: {fir_obj.id}")
                # Handle document creation
                existing_doc_ids = []
                for doc_idx, doc_data in enumerate(documents_data):
                    file_key = f"firs[{fir_idx}][documents][{doc_idx}][document]"
                    if file_key in self.request.FILES:
                        doc_file = self.request.FILES[file_key]
                        doc = Document.objects.create(
                            person_type="missing person",
                            document_type=doc_data.get('document_type', 'fir_attachment'),
                            description=doc_data.get('description', ''),
                            document=doc_file,
                            fir=fir_obj,
                            created_by=self.request.user
                        )
                        existing_doc_ids.append(doc.id)
                        logger.debug(f"Created new FIR document with file ID: {doc.id}")
                    # Create document without file if only metadata is provided
                    elif doc_data.get('document_type') or doc_data.get('description'):
                        doc = Document.objects.create(
                            person_type="missing person",
                            document_type=doc_data.get('document_type', 'fir_attachment'),
                            description=doc_data.get('description', ''),
                            fir=fir_obj,
                            created_by=self.request.user
                        )
                        existing_doc_ids.append(doc.id)
                        logger.debug(f"Created new FIR document without file ID: {doc.id}")

    def _update_consents(self, person, consents_data):
        logger.debug(f"Updating {len(consents_data)} consent records")
        for consent in consents_data:
            if not isinstance(consent, dict):
                logger.warning("Invalid consent data format")
                continue

            consent_id = consent.get('id')
            consent_data = {k: v for k, v in consent.items() if k != 'id' and k != 'person'}

            if consent_id:
                try:
                    consent_obj = Consent.objects.get(id=consent_id, person=person)
                    for key, value in consent_data.items():
                        setattr(consent_obj, key, value)
                    consent_obj.save()
                    logger.debug(f"Updated consent ID: {consent_id}")
                except Consent.DoesNotExist:
                    logger.warning(f"Consent with ID {consent_id} not found")
                    continue
            else:
                Consent.objects.create(person=person, **consent_data)
                logger.debug("Created new consent")

    #  5. PARTIAL UPDATE (PATCH)
    def partial_update(self, request, pk=None):
        logger.info(f"PARTIAL UPDATE request for person ID: {pk} from user: {request.user}")
        logger.debug(f"Request data: {request.data}")

        try:
            with transaction.atomic():
                person = Person.objects.get(pk=pk)
                logger.debug(f"Found person: {person.full_name}")
                data = request.data

                # Update Person fields
                for key, value in data.items():
                    if key not in ['addresses', 'contacts', 'additional_info', 'last_known_details', 'firs', 'consent']:
                        setattr(person, key, value)
                person.save()
                logger.debug("Person saved with partial updates")

                # Partially update related addresses
                if 'addresses' in data:
                    addresses_data = data.pop('addresses')
                    logger.debug(f"Updating {len(addresses_data)} addresses")
                    for address_data in addresses_data:
                        address_id = address_data.get('id')
                        if address_id:
                            address = Address.objects.get(id=address_id, person=person)
                            for key, value in address_data.items():
                                if key != 'person':  # Ensure we don't overwrite the person field
                                    setattr(address, key, value)
                            address.save()
                            logger.debug(f"Updated address ID: {address_id}")
                        else:
                            # Remove the 'person' key from address_data if it exists
                            address_data.pop('person', None)
                            # Create a new Address object with the correct person instance
                            Address.objects.create(person=person, **address_data)
                            logger.debug("Created new address")

                # Partially update related contacts
                if 'contacts' in data:
                    contacts_data = data.pop('contacts')
                    for contact_data in contacts_data:
                        contact_id = contact_data.get('id')
                        if contact_id:
                            contact = Contact.objects.get(id=contact_id, person=person)
                            for key, value in contact_data.items():
                                if key != 'person':  # Ensure we don't overwrite the person field
                                    setattr(contact, key, value)
                            contact.save()
                            logger.debug(f"Updated contact ID: {contact_id}")
                        else:
                            # Remove the 'person' key from contact_data if it exists
                            contact_data.pop('person', None)
                            # Create a new Contact object with the correct person instance
                            Contact.objects.create(person=person, **contact_data)
                            logger.debug("Created new contact")

                # Partially update related additional_info
                if 'additional_info' in data:
                    additional_info_data = data.pop('additional_info')
                    for info_data in additional_info_data:
                        info_id = info_data.get('id')
                        if info_id:
                            info = AdditionalInfo.objects.get(id=info_id, person=person)
                            for key, value in info_data.items():
                                if key != 'person':  # Ensure we don't overwrite the person field
                                    setattr(info, key, value)
                            info.save()
                            logger.debug(f"Updated info ID: {info_id}")
                        else:
                            # Remove the 'person' key from info_data if it exists
                            info_data.pop('person', None)
                            # Create a new AdditionalInfo object with the correct person instance
                            AdditionalInfo.objects.create(person=person, **info_data)
                            logger.debug("Created info data")

                # Partially update related last_known_details
                if 'last_known_details' in data:
                    last_known_details_data = data.pop('last_known_details')
                    for details_data in last_known_details_data:
                        details_id = details_data.get('id')
                        if details_id:
                            details = LastKnownDetails.objects.get(id=details_id, person=person)
                            for key, value in details_data.items():
                                if key != 'person':  # Ensure we don't overwrite the person field
                                    setattr(details, key, value)
                            details.save()
                            logger.debug(f"Updated detail ID: {details_id}")
                        else:
                            # Remove the 'person' key from details_data if it exists
                            details_data.pop('person', None)
                            # Create a new LastKnownDetails object with the correct person instance
                            LastKnownDetails.objects.create(person=person, **details_data)
                            logger.debug("Created details data")

                # Partially update related FIRs
                if 'firs' in data:
                    firs_data = data.pop('firs')
                    for fir_data in firs_data:
                        fir_id = fir_data.get('id')
                        if fir_id:
                            fir = FIR.objects.get(id=fir_id, person=person)
                            for key, value in fir_data.items():
                                if key != 'person':  # Ensure we don't overwrite the person field
                                    setattr(fir, key, value)
                            fir.save()
                            logger.debug(f"Updated fir ID: {fir_id}")
                        else:
                            # Remove the 'person' key from fir_data if it exists
                            fir_data.pop('person', None)
                            # Create a new FIR object with the correct person instance
                            FIR.objects.create(person=person, **fir_data)
                            logger.debug("Created fir data")

                # Update the consent field (Many-to-Many relationship)
                if 'consent' in data:
                    consent_data = data.pop('consent')
                    if isinstance(consent_data, list):
                        # Ensure consent_data contains only hashable values (e.g., primary keys)
                        consent_data = [item if isinstance(item, (str, int)) else item.get('id') for item in
                                        consent_data]
                        person.consent.set(consent_data)

                return Response(
                    {'message': 'Person and related data partially updated successfully'},
                    status=status.HTTP_200_OK
                )

        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for partial update")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in partial update for person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #  6. DELETE a person
    def destroy(self, request, pk=None):
        logger.info(f"DELETE request for person ID: {pk} from user: {request.user}")
        try:
            person = Person.objects.get(pk=pk)
            person.person_approve_status ='pending'
            person._is_deleted = True
            person.save()
            logger.info(f"Soft deleted person ID: {pk}")
            return Response({'message': 'Person deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for deletion")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #  7. SOFT DELETE all persons
    def destroy_All(self, request):
        logger.warning(f"DELETE ALL request from user: {request.user} - This is a dangerous operation!")
        try:
            updated_count = Person.objects.filter(_is_deleted=False).update(
                _is_deleted=True,
                person_approve_status='pending'
            )
            logger.warning(f"Soft deleted {updated_count} persons")
            return Response(
                {'message': f'{updated_count} persons deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in delete all operation: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        logger.info(f"RESTORE request for person ID: {pk} from user: {request.user}")
        try:
            person = Person.objects.get(pk=pk, _is_deleted=True)
            person._is_deleted = False
            person.person_approve_status = 'approved'
            person.save()
            logger.info(f"Restored and approved person ID: {pk}")
            return Response({'message': 'Person restored and approved successfully'}, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found or not deleted")
            return Response({'error': 'Person not found or not deleted'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error restoring person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='search/(?P<case_id>[^/.]+)')
    def retrieve_by_case_id(self, request, case_id=None):
        logger.info(f"SEARCH by case_id request: {case_id}")
        try:
            person = Person.objects.get(case_id=case_id, _is_deleted=False, person_approve_status='approved')
            logger.debug(f"Found person with case_id: {case_id}")
            serializer = PersonSerializer(person)
            logger.info(f"Successfully retrieved person by case_id: {case_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            logger.warning(f"Person with Case ID {case_id} not found or not approved")
            return Response({'error': f'Person with Case ID {case_id} not found or is not approved'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error searching by case_id {case_id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='missing-persons')
    def missing_persons(self, request):
        logger.info("MISSING PERSONS list request")
        return self.get_persons_by_type(request, 'Missing Person')

    @action(detail=False, methods=['get'], url_path='unidentified-persons')
    def unidentified_persons(self, request):
        logger.info("UNIDENTIFIED PERSONS list request")
        return self.get_persons_by_type(request, 'Unidentified Person')

    @action(detail=False, methods=['get'], url_path='unidentified-bodies')
    def unidentified_bodies(self, request):
        logger.info("UNIDENTIFIED BODIES list request")
        return self.get_persons_by_type(request, 'Unidentified Body')

    def get_persons_by_type(self, request, person_type):
        logger.info(f"Getting persons by type: {person_type}")
        logger.debug(f"Query parameters: {dict(request.query_params)}")
        """Return filtered persons based on request parameters"""
        try:
            filters = {}
            additional_info_filters = {}
            order_by = '-updated_at'

            age_range = request.query_params.get('age_range')
            age = request.query_params.get('age')

            for key, value in request.query_params.items():
                if not value or key in ['startDate', 'endDate', 'age_range', 'age', 'page', 'page_size']:
                    continue

                # Fields from related model 'additional_info'
                if key == 'caste':
                    additional_info_filters['additional_info__caste'] = value
                elif key == 'marital_status':
                    additional_info_filters['additional_info__marital_status'] = value
                elif key == 'height_range':
                    filters['height_range'] = value
                elif key == 'full_name':
                    filters['full_name__istartswith'] = value
                else:
                    filters[key] = value

            # Handle date filtering
            start_date = request.query_params.get('startDate')
            end_date = request.query_params.get('endDate')

            if start_date and start_date != "null":
                try:
                    filters['last_known_details__missing_date__gte'] = parser.parse(start_date).date()
                    logger.debug(f"Start date filter: {start_date}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid start date: {start_date}")
                    # pass

            if end_date and end_date != "null":
                try:
                    filters['last_known_details__missing_date__lte'] = parser.parse(end_date).date()
                    logger.debug(f"End date filter: {end_date}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid end date: {end_date}")
                    # pass

            # Handle age filtering logic safely
            if age_range and age_range.lower() != "null":
                try:
                    lower, upper = map(int, age_range.split('-'))
                    if 'missing' in person_type.lower():
                        filters['age__gte'] = lower
                        filters['age__lte'] = upper
                    else:
                        filters['age_range'] = age_range

                    logger.debug(f"Age range filter: {age_range}")
                except ValueError:
                    logger.warning(f"Invalid age range: {age_range}")
                    # pass

            if age and person_type == 'missing-persons':
                filters['age'] = age
                logger.debug(f"Age filter: {age}")

            persons = Person.objects.filter(
                type=person_type,
                person_approve_status='approved',
                _is_deleted=False,
                **filters,
                **additional_info_filters
            ).prefetch_related(
                'addresses', 'contacts', 'additional_info',
                'last_known_details', 'firs', 'consent'
            ).order_by(order_by).distinct()
            logger.debug(f"Filtered persons count: {persons.count()}")

            if not persons.exists():
                logger.info(f"No {person_type.lower()} found with given filters")
                return Response({'message': f'No {person_type.lower()} found'}, status=status.HTTP_200_OK)

            # Paginate the queryset (correct indentation - outside the if not exists block)
            paginator = searchCase_Pagination()
            page = paginator.paginate_queryset(persons, request)

            if page is not None:
                serializer = SearchSerializer(page, many=True)
                logger.info(f"Returning paginated {person_type.lower()} (page size: {len(page)})")
                return paginator.get_paginated_response(serializer.data)

            serializer = SearchSerializer(persons, many=True)
            logger.info(f"Returning all {person_type.lower()} (count: {len(persons)})")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting {person_type.lower()}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_or_rejected(self, request):
        logger.info(f"PENDING OR REJECTED request from admin: {request.user}")
        logger.debug(f"Query parameters: {dict(request.query_params)}")
        try:
            # Extract filter parameters from query string
            state = request.query_params.get('state')
            district = request.query_params.get('district')
            city = request.query_params.get('city')
            village = request.query_params.get('village')
            police_station = request.query_params.get('police_station')
            case_id = request.query_params.get('case_id')
            logger.debug(
                f"Filters - State: {state}, District: {district}, City: {city}, Village: {village}, Police Station: {police_station}, Case ID: {case_id}")


            # Build dynamic filters using Q
            filters = Q()
            if state:
                filters &= Q(state__iexact=state)
            if district:
                filters &= Q(district__iexact=district)
            if city:
                filters &= Q(city__iexact=city)
            if village:
                filters &= Q(village__iexact=village)
            if case_id:
                filters &= Q(case_id__iexact=case_id)
            if police_station:
                filters &= Q(firs__police_station__id=UUID(police_station))

            # Apply filters to the queryset
            persons = Person.objects.filter(filters).order_by('-created_at')
            logger.debug(f"Filtered persons count: {persons.count()}")
            serialized_data = PersonSerializer(persons, many=True).data

            # Group data by status fields
            summary = {
                'pending': [],
                'approved': [],
                'rejected': [],
                'on_hold': [],
                'suspended': []
            }

            for person in serialized_data:
                approve_status = person.get('person_approve_status')
                status_field = person.get('status')

                if approve_status == 'pending':
                    summary['pending'].append(person)
                elif approve_status == 'approved':
                    summary['approved'].append(person)
                elif approve_status == 'rejected':
                    summary['rejected'].append(person)
                elif approve_status == 'on_hold':
                    summary['on_hold'].append(person)
                elif approve_status == 'suspended':
                    summary['suspended'].append(person)

            logger.info(
                f"Status summary - Pending: {len(summary['pending'])}, Approved: {len(summary['approved'])}, Rejected: {len(summary['rejected'])}, On Hold: {len(summary['on_hold'])}, Suspended: {len(summary['suspended'])}")


            return Response({
                'pending_count': len(summary['pending']),
                'approved_count': len(summary['approved']),
                'rejected_count': len(summary['rejected']),
                'on_hold_count': len(summary['on_hold']),
                'suspended_count': len(summary['suspended']),
                'pending_data': summary['pending'],
                'approved_data': summary['approved'],
                'rejected_data': summary['rejected'],
                'on_hold_data': summary['on_hold'],
                'suspended_data': summary['suspended'],
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in pending_or_rejected: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': 'Something went wrong while fetching person data.', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve_person(self, request, pk=None):
        logger.info(f"APPROVE PERSON request for ID: {pk} from admin: {request.user}")
        try:
            person = Person.objects.get(pk=pk)
            logger.debug(f"Found person: {person.full_name} (Current status: {person.person_approve_status})")

            # Update approval details
            person.person_approve_status = 'approved'
            person.approved_by = request.user
            person.save()

            serializer = PersonSerializer(person)
            logger.info(f"Person ID {pk} approved successfully")

            # Extract reporter info (assuming created_by is the reporter)
            reporter = person.created_by
            reporter_name = f"{reporter.first_name} {reporter.last_name}".strip()
            reporter_email = reporter.email_id  # This must be the reporter's email field

            # Send approval email in the background
            threading.Thread(
                target=send_case_approval_email,
                kwargs={
                    'user_email': reporter_email,
                    'reporter_name': reporter_name,
                    'full_name': person.full_name,
                    'case_id': person.case_id,
                    'type': person.type,  # Missing person, unidentified body, etc.
                    'approved_at': timezone.localtime(person.updated_at).strftime("%d/%m/%Y, %I:%M:%S %p")
                }
            ).start()
            logger.info("Approval email thread started")

            return Response(
                {'message': 'Person approved successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )

        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for approval")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error approving person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject_person(self, request, pk=None):
        logger.info(f"REJECT PERSON request for ID: {pk} from admin: {request.user}")
        try:
            person = Person.objects.get(pk=pk)
            logger.debug(f"Found person: {person.full_name}")
            person.person_approve_status = 'rejected'
            person.approved_by = request.user
            person.save()
            serializer = PersonSerializer(person)
            logger.info(f"Person ID {pk} rejected successfully")
            return Response(
                {'message': 'Person rejected successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for rejection")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error rejecting person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reapprove_person(self, request, pk=None):
        logger.info(f"REAPPROVE PERSON request for ID: {pk} from admin: {request.user}")
        try:
            person = Person.objects.get(pk=pk)
            logger.debug(f"Found rejected person: {person.full_name}")

            person.person_approve_status = 'approved'
            person.approved_by = request.user
            person.save()

            serializer = PersonSerializer(person)
            logger.info(f"Rejected person ID {pk} re-approved successfully")
            return Response(
                {'message': 'Rejected person approved successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for re-approval")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error re-approving person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_from_approved(self, request, pk=None):
        logger.info(f"CHANGE FROM APPROVED request for ID: {pk} from admin: {request.user}")
        logger.debug(f"Request data: {request.data}")
        try:
            person = Person.objects.get(pk=pk)
            new_status = request.data.get('status')

            if not new_status:
                logger.warning("Status is required for change_from_approved")
                return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

            previous_status = person.person_approve_status
            person.person_approve_status = new_status
            person.approved_by = request.user
            person.save()

            serializer = PersonSerializer(person)
            logger.info(f"Person ID {pk} status changed from {previous_status} to {new_status}")
            reporter = person.created_by
            reporter_name = f"{reporter.first_name} {reporter.last_name}".strip()
            reporter_email = reporter.email_id

            # Send email only if moved to Pending
            if new_status.lower() == 'pending':
                reason = request.data.get(
                    'reason',
                    'The case has been moved back to pending review for further evaluation by the administration team.'
                )
                threading.Thread(
                    target=send_case_back_to_pending_email,
                    kwargs={
                        'user_email': reporter_email,
                        'reporter_name': reporter_name,
                        'case_id': person.case_id,
                        'previous_status': previous_status,
                        'reason': reason
                    }
                ).start()
                logger.info("Pending status email thread started")

            return Response(
                {'message': f'Person status changed to {new_status}', 'data': serializer.data},
                status=status.HTTP_200_OK
            )

        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for status change")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error changing status for person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def suspend_person(self, request, pk=None):
        logger.info(f"SUSPEND PERSON request for ID: {pk} from admin: {request.user}")
        logger.debug(f"Request data: {request.data}")
        try:
            person = Person.objects.get(pk=pk)
            reason = request.data.get('reason')

            if not reason:
                logger.warning("Reason is required to suspend a person")
                return Response(
                    {'error': 'Reason is required to suspend a person'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            person.person_approve_status = 'suspended'
            person.status_reason = reason
            person.approved_by = request.user
            person.save()
            serializer = PersonSerializer(person)
            logger.info(f"Person ID {pk} suspended with reason: {reason}")

            reporter = person.created_by
            reporter_name = f"{reporter.first_name} {reporter.last_name}".strip()
            reporter_email = reporter.email_id

            if person.person_approve_status.lower() == 'suspended':
                reason = request.data.get("reason")
                threading.Thread(
                    target=send_case_to_suspend_email,
                    kwargs={
                        "user_email":reporter_email,
                        "reporter_name":reporter_name,
                        "case_id":person.case_id,
                        "reason":reason
                    }
                ).start()
                logger.info("Suspension email thread started")
            return Response(
                {'message': 'Person suspended successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for suspension")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error suspending person ID {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def hold_person(self, request, pk=None):
        logger.info(f"HOLD PERSON request for ID: {pk} from admin: {request.user}")
        logger.debug(f"Request data: {request.data}")
        try:
            person = Person.objects.get(pk=pk)
            reason = request.data.get('reason')

            if not reason:
                logger.warning("Reason is required to put a person on hold")
                return Response(
                    {'error': 'Reason is required to put a person on hold'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            person.person_approve_status = 'on_hold'
            person.status_reason = reason
            person.approved_by = request.user
            person.save()

            serializer = PersonSerializer(person)
            logger.info(f"Person ID {pk} put on hold with reason: {reason}")
            reporter = person.created_by
            reporter_name = f"{reporter.first_name} {reporter.last_name}".strip()
            reporter_email = reporter.email_id

            if person.person_approve_status.lower() == 'on_hold':
                reason = request.data.get("reason")
                threading.Thread(
                    target=send_case_to_hold_email,
                    kwargs={
                        "user_email": reporter_email,
                        "reporter_name": reporter_name,
                        "case_id": person.case_id,
                        "reason": reason
                    }
                ).start()
                logger.info("Hold email thread started")
            return Response(
                {'message': 'Person put on hold successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Person.DoesNotExist:
            logger.warning(f"Person with ID {pk} not found for hold")
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error putting person ID {pk} on hold: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

