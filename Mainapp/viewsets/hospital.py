
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""


import hashlib
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from ..Serializers.hospital_Serializer import HospitalIdNameSerializer
from ..Serializers.serializers import AddressSerializer, HospitalSerializer, ContactSerializer
from ..models import Hospital, Contact
from Mainapp.all_paginations.pagination import CustomPagination
from django.core.cache import cache
from rest_framework import generics
import json
from django.contrib.gis.geos import Point
from rest_framework.permissions import AllowAny, IsAuthenticated

class HospitalViewSet(viewsets.ModelViewSet):
    """
    API Endpoints for Hospital Management
    """
    serializer_class = HospitalSerializer
    pagination_class = CustomPagination
    queryset = Hospital.objects.all()

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated()]

    # 1. LIST Hospitals with Pagination

    def list(self, request):
        try:
            name = request.query_params.get('name', '').strip()
            city = request.query_params.get('city', '').strip()
            district = request.query_params.get('district', '').strip()
            state = request.query_params.get('state', '').strip()
            hospital_type = request.query_params.get('type', '').strip()
            status_filter = request.query_params.get('status', '').strip()

            filters = Q()
            if name:
                filters &= Q(name__istartswith=name)
            if city:
                filters &= Q(address__city__icontains=city)
            if district:
                filters &= Q(address__district__icontains=district)
            if state:
                filters &= Q(address__state__icontains=state)
            if hospital_type:
                filters &= Q(type__iexact=hospital_type)
            if status_filter:
                filters &= Q(activ_Status__iexact=status_filter)

            queryset = Hospital.objects.select_related('address').prefetch_related('hospital_contact').filter(filters).order_by('name')

            paginator = CustomPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = HospitalSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    # def list(self, request):
    #     try:
    #         name = request.query_params.get('name', '').strip()
    #         city = request.query_params.get('city', '').strip()
    #         district = request.query_params.get('district', '').strip()
    #         state = request.query_params.get('state', '').strip()
    #         hospital_type = request.query_params.get('type', '').strip()
    #         status_filter = request.query_params.get('status', '').strip()
    #         page = request.query_params.get('page', '1')
    #
    #         # Log filters
    #         print(
    #             f"[DEBUG] Filters => Name: '{name}', City: '{city}', District: '{district}', State: '{state}', Type: '{hospital_type}', Status: '{status_filter}', Page: {page}")
    #
    #         # Construct a hash-based cache key
    #         cache_key_raw = f"{name}_{city}_{district}_{state}_{hospital_type}_{status_filter}_{page}"
    #         cache_key = "hospital_list_" + hashlib.md5(cache_key_raw.encode()).hexdigest()
    #         print(f"[DEBUG] Cache Key: {cache_key}")
    #
    #         # Try fetching from Redis
    #         cached_response = cache.get(cache_key)
    #         if cached_response:
    #             print("[DEBUG] Data loaded from Redis cache ")
    #             return Response(json.loads(cached_response), status=status.HTTP_200_OK)
    #
    #         print("Cache miss. Querying database...")
    #
    #         # Build filters
    #         filters = Q()
    #         if name:
    #             filters &= Q(name__istartswith=name)
    #         if city:
    #             filters &= Q(address__city__icontains=city)
    #         if district:
    #             filters &= Q(address__district__icontains=district)
    #         if state:
    #             filters &= Q(address__state__icontains=state)
    #         if hospital_type:
    #             filters &= Q(type__iexact=hospital_type)
    #         if status_filter:
    #             filters &= Q(activ_Status__iexact=status_filter)
    #
    #         # Query and sort hospitals
    #         queryset = (
    #             Hospital.objects
    #             .select_related('address')
    #             .prefetch_related('hospital_contact')
    #             .filter(filters)
    #             .order_by('name')
    #         )
    #         print(f"[DEBUG] Total DB results before pagination: {queryset.count()}")
    #
    #         # Paginate
    #         paginator = CustomPagination()
    #         paginated_queryset = paginator.paginate_queryset(queryset, request)
    #         print(f"[DEBUG] Paginated results count: {len(paginated_queryset)}")
    #
    #         # Serialize
    #         serializer = HospitalSerializer(paginated_queryset, many=True)
    #         response_data = paginator.get_paginated_response(serializer.data)
    #
    #         # Cache the final response
    #         cache.set(cache_key, json.dumps(response_data.data, cls=DjangoJSONEncoder), timeout=300)
    #         print("[DEBUG] Response cached in Redis ")
    #
    #         return response_data
    #
    #     except Exception as e:
    #         print(f"[ERROR] Exception occurred: {str(e)}")
    #         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # 2. RETRIEVE Hospital by ID
    # def retrieve(self, request, pk=None):
    #     try:
    #         cache_key = f'hospital_{pk}'
    #         cached_data = cache.get(cache_key)
    #
    #         if cached_data:
    #             # Load cached JSON and return
    #             data = json.loads(cached_data)
    #             return Response(data, status=status.HTTP_200_OK)
    #         # Fetch from DB
    #         hospital = Hospital.objects.select_related('address').prefetch_related('hospital_contact').get(pk=pk)
    #         # Serialize data
    #         serializer = self.get_serializer(hospital)
    #         serialized_data = serializer.data
    #         # Store serialized JSON in Redis
    #         cache.set(cache_key, json.dumps(serialized_data, cls=DjangoJSONEncoder), timeout=300)
    #         return Response(serialized_data, status=status.HTTP_200_OK)
    #     except Hospital.DoesNotExist:
    #         return Response({'error': 'Hospital not found'}, status=status.HTTP_404_NOT_FOUND)
    def retrieve(self, request, pk=None):
        try:
            # Directly fetch from the database without using cache
            hospital = Hospital.objects.select_related('address').prefetch_related('hospital_contact').get(pk=pk)

            # Serialize the data
            serializer = self.get_serializer(hospital)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Hospital.DoesNotExist:
            return Response({'error': 'Hospital not found'}, status=status.HTTP_404_NOT_FOUND)

    #  3. CREATE a new Hospital
    def create(self, request, *args, **kwargs):
        try:
            print("\n Received API Request Data:", request.data)

            with transaction.atomic():
                # if not request.data.get("name"):
                #     return Response({"error": "Hospital name is required and cannot be blank."},
                #                     status=status.HTTP_400_BAD_REQUEST)

                hospital_photo = request.FILES.get("hospital_photo")
                # if not hospital_photo:
                #     return Response(
                #         {"error": "Invalid hospital photo. Ensure you're sending a valid file."},
                #         status=status.HTTP_400_BAD_REQUEST
                #     )

                address_data = request.data.get("address")
                if not address_data:
                    return Response({"error": "Address is required"}, status=status.HTTP_400_BAD_REQUEST)

                if isinstance(address_data, str):
                    address_data = json.loads(address_data)

                location_data = address_data.get("location")
                if isinstance(location_data, dict):
                    latitude = location_data.get("latitude")
                    longitude = location_data.get("longitude")
                    if latitude and longitude:
                        try:
                            address_data["location"] = Point(float(longitude), float(latitude))
                        except (ValueError, TypeError):
                            return Response(
                                {"error": "Invalid location format. Latitude and Longitude must be valid numbers."},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        return Response(
                            {"error": "Latitude and Longitude cannot be empty."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                address_serializer = AddressSerializer(data=address_data)
                if not address_serializer.is_valid():
                    return Response({"address": address_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                address = address_serializer.save()

                hospital_data = request.data.copy()
                hospital_data["address"] = address.id
                hospital_data["hospital_photo"] = hospital_photo
                hospital_data["created_by"] = request.user.id
                # hospital_data["updated_by"] = request.user.id

                contacts_data = request.data.get("hospital_contact", "[]")
                if isinstance(contacts_data, str):
                    contacts_data = json.loads(contacts_data)

                hospital_serializer = self.get_serializer(data=hospital_data)
                if not hospital_serializer.is_valid():
                    return Response(hospital_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                hospital = hospital_serializer.save()

                contact_objects = []
                for contact in contacts_data:
                    contact["hospital"] = hospital
                    contact["person"] = None
                    contact_objects.append(Contact(**contact))

                Contact.objects.bulk_create(contact_objects)

                response_data = self.get_serializer(hospital).data
                response_data['hospital_contact'] = ContactSerializer(hospital.hospital_contact.all(), many=True).data

                print("\n Final Response Data:", response_data)
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # 4. FULL UPDATE (PUT)
    def update(self, request, pk=None):
        return self._update_hospital(request, pk, partial=False)

    # 5. PARTIAL UPDATE (PATCH)
    def partial_update(self, request, pk=None):
        return self._update_hospital(request, pk, partial=True)

    def _update_hospital(self, request, pk, partial):
        print(request.data)
        try:
            with transaction.atomic():
                hospital = get_object_or_404(Hospital, pk=pk)
                data = request.data.copy()

                # Handle file upload scenarios
                if 'hospital_photo' in request.FILES:
                    data['hospital_photo'] = request.FILES['hospital_photo']
                elif 'hospital_photo' in data:
                    if data['hospital_photo'] in ['', 'null', None]:
                        data['hospital_photo'] = None
                    elif isinstance(data['hospital_photo'], str) and data['hospital_photo'].startswith('http'):
                        data.pop('hospital_photo', None)

                # Parse address and hospital_contact from JSON strings if needed
                json_fields = ['address', 'hospital_contact']
                for field in json_fields:
                    if field in data:
                        if isinstance(data[field], str):
                            try:
                                data[field] = json.loads(data[field])
                            except json.JSONDecodeError:
                                try:
                                    data[field] = ast.literal_eval(data[field])
                                except Exception as e:
                                    return Response(
                                        {"error": f"Invalid {field} format: {str(e)}"},
                                        status=status.HTTP_400_BAD_REQUEST
                                    )

                # Now extract address dict
                address_data = data.get("address") or data.get("address_details")
                if isinstance(address_data, dict):
                    location = address_data.get("location")
                    if isinstance(location, dict):
                        try:
                            address_data["location"] = Point(
                                float(location["longitude"]),
                                float(location["latitude"]),
                                srid=4326
                            )
                        except (ValueError, TypeError, KeyError):
                            return Response(
                                {"error": "Invalid location coordinates"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    elif isinstance(location, str) and location.startswith("POINT"):
                        try:
                            address_data["location"] = GEOSGeometry(location)
                        except (GEOSException, ValueError) as e:
                            return Response(
                                {"error": f"Invalid WKT format: {str(e)}"},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                    address_serializer = AddressSerializer(
                        hospital.address,
                        data=address_data,
                        partial=partial
                    )
                    if not address_serializer.is_valid():
                        return Response(
                            {"address": address_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    address_serializer.save()
                    data["address"] = hospital.address.pk

                # Main serializer
                serializer = self.get_serializer(hospital, data=data, partial=partial)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                instance = serializer.save()

                if 'hospital_photo' in data and data['hospital_photo'] is None:
                    instance.hospital_photo = None
                    instance.save()

                # Contacts
                contacts_data = data.get("hospital_contact", [])
                if isinstance(contacts_data, list):
                    existing_contacts = {str(c.id): c for c in hospital.hospital_contact.all()}
                    new_contacts = []

                    for contact_data in contacts_data:
                        if not isinstance(contact_data, dict):
                            continue

                        contact_id = str(contact_data.get("id", ""))
                        if contact_id in existing_contacts:
                            contact = existing_contacts[contact_id]
                            for field, value in contact_data.items():
                                if field != 'id' and hasattr(contact, field):
                                    setattr(contact, field, value)
                            contact.save()
                        else:
                            clean_data = {
                                k: v for k, v in contact_data.items()
                                if k not in ['id', 'hospital']
                            }
                            new_contacts.append(Contact(hospital=instance, **clean_data))

                    if new_contacts:
                        Contact.objects.bulk_create(new_contacts)

                # Final response
                response_data = serializer.data
                response_data['hospital_contact'] = ContactSerializer(
                    instance.hospital_contact.all(), many=True
                ).data

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #  6. DELETE Hospital
    def destroy(self, request, pk=None):
        try:
            hospital = get_object_or_404(Hospital, pk=pk)
            hospital_name = hospital.name
            hospital.delete()
            return Response({"message": f"Hospital '{hospital_name}' is deleted successfully"}, status=status.HTTP_200_OK)
        except Hospital.DoesNotExist:
            return Response({"error": "Hospital not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# To Get all Hospitals
class HospitalListView(generics.ListAPIView):
    queryset = Hospital.objects.all().order_by("id")
    serializer_class = HospitalIdNameSerializer


# To filter only govt hospitals
class GovtHospitalListView(generics.ListAPIView):
    queryset = Hospital.objects.all().filter(type='govt').order_by("id")
    serializer_class = HospitalIdNameSerializer
