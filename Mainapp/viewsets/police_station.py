"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""


from django.contrib.gis.geos import Point
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.parsers import FormParser,JSONParser
from rest_framework.response import Response
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from ..Serializers.serializers import AddressSerializer, PoliceStationSerializer, ContactSerializer, \
    PoliceStationIdNameSerializer
from ..models import PoliceStation, Contact
from Mainapp.all_paginations.pagination import CustomPagination
from django.core.cache import cache
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry, GEOSException, Point


import json


from rest_framework.permissions import AllowAny, IsAuthenticated  # ✅ Imports




class PoliceStationViewSet(viewsets.ModelViewSet):
    """
    API Endpoints for Police Station Management
    """
    serializer_class = PoliceStationSerializer
    pagination_class = PageNumberPagination
    queryset = PoliceStation.objects.all()
    parser_classes = (MultiPartParser, FormParser,JSONParser)

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]  # Public access for safe methods
        return [IsAuthenticated()]


        #  1. LIST Police Stations with Pagination
    def list(self, request):
        try:
            # Extract query parameters
            name = request.query_params.get('name', '').strip()
            city = request.query_params.get('city', '').strip()
            district = request.query_params.get('district', '').strip()
            state = request.query_params.get('state', '').strip()

            # Build the filter conditions dynamically
            filters = Q()
            if name:
                filters &= Q(name__istartswith=name)
            if city:
                filters &= Q(address__city__icontains=city)
            if district:
                filters &= Q(address__district__icontains=district)
            if state:
                filters &= Q(address__state__icontains=state)

            # Apply filters to the queryset
            queryset = PoliceStation.objects.select_related('address').prefetch_related('police_contact').filter(
                filters).order_by('name')

            # Paginate the filtered queryset
            paginator = CustomPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = PoliceStationSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            police_station = PoliceStation.objects.select_related('address').prefetch_related('police_contact').get(
                pk=pk)
            serializer = self.get_serializer(police_station)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PoliceStation.DoesNotExist:
            return Response({'error': 'Police station not found'}, status=status.HTTP_404_NOT_FOUND)

    #  2. RETRIEVE Police Station by ID
    # def retrieve(self, request, pk=None):
    #     try:
    #         police_station = cache.get(f'police_station_{pk}')
    #
    #         if not police_station:
    #             police_station = PoliceStation.objects.select_related('address').prefetch_related('police_contact').get(pk=pk)
    #             cache.set(f'police_station_{pk}', police_station, timeout=300)
    #
    #         serializer = self.get_serializer(police_station)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except PoliceStation.DoesNotExist:
    #         return Response({'error': 'Police station not found'}, status=status.HTTP_404_NOT_FOUND)

    #  3. CREATE a new Police Station

    def create(self, request, *args, **kwargs):
        try:
            print("\n🔹 Received API Request Data:", request.data)  # Log incoming data

            with transaction.atomic():
                station_photo = request.FILES.get("station_photo")
                address_data = request.data.get("address")
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


                #  Validate and create address
                address_serializer = AddressSerializer(data=address_data)
                if not address_serializer.is_valid():
                    return Response({"address": address_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                address = address_serializer.save()

                # 🔹 Prepare police station data
                police_station_data = request.data.copy()
                police_station_data["address"] = address.id
                police_station_data["station_photo"] = station_photo

                #  Convert JSON string for `police_contact`
                contacts_data = request.data.get("police_contact", "[]")
                if isinstance(contacts_data, str):
                    contacts_data = json.loads(contacts_data)

                #  Create police station
                police_station_serializer = self.get_serializer(data=police_station_data)
                if not police_station_serializer.is_valid():
                    return Response(police_station_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                police_station = police_station_serializer.save()

                #  Corrected Contact Creation Logic
                contact_objects = []
                for contact in contacts_data:
                    contact["police_station"] = police_station

                    #  Ensure `person` is always `None`
                    contact["person"] = None

                    contact_objects.append(Contact(**contact))

                #  Bulk create contacts properly
                Contact.objects.bulk_create(contact_objects)

                # Return response with contacts
                response_data = self.get_serializer(police_station).data
                response_data['police_contact'] = ContactSerializer(police_station.police_contact.all(), many=True).data

                print("\n Final Response Data:", response_data)
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("\n API Error:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    #  4. FULL UPDATE (PUT)
    def update(self, request, pk=None):
        return self._update_police_station(request, pk, partial=False)

    #  5. PARTIAL UPDATE (PATCH)
    def partial_update(self, request, pk=None):
        return self._update_police_station(request, pk, partial=True)

    def _update_police_station(self, request, pk, partial):
        try:
            with transaction.atomic():
                police_station = get_object_or_404(PoliceStation, pk=pk)

                # 1. Extract address (accept both 'address' and 'address_details')
                address_data = request.data.pop("address", None) or request.data.pop("address_details", None)

                # 2. Update address if provided
                if address_data:
                    location = address_data.get("location")
                    if isinstance(location, dict) and "latitude" in location and "longitude" in location:
                        latitude = location["latitude"]
                        longitude = location["longitude"]
                        try:
                            address_data["location"] = Point(float(longitude), float(latitude), srid=4326)
                        except (ValueError, TypeError):
                            return Response(
                                {"error": "Invalid location format. Latitude and Longitude must be valid numbers."},
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

                    address_serializer = AddressSerializer(police_station.address, data=address_data, partial=partial)
                    if address_serializer.is_valid():
                        address_serializer.save()
                        request.data["address"] = str(police_station.address.id)  # Set FK reference for serializer
                    else:
                        return Response({"address": address_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                # 3. Extract contacts
                contacts_data = request.data.pop("police_contact", [])

                # 4. Update police station
                serializer = self.get_serializer(police_station, data=request.data, partial=partial)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # 5. Handle contacts
                existing_contacts = {str(contact.id): contact for contact in police_station.police_contact.all()}
                new_contacts = []

                for contact_data in contacts_data:
                    contact_id = str(contact_data.get("id", ""))
                    if contact_id and contact_id in existing_contacts:
                        contact = existing_contacts[contact_id]
                        for key, value in contact_data.items():
                            if key != 'id':
                                setattr(contact, key, value)
                        contact.save()
                    else:
                        clean_data = contact_data.copy()
                        clean_data.pop('id', None)
                        new_contacts.append(Contact(police_station=police_station, **clean_data))

                if new_contacts:
                    Contact.objects.bulk_create(new_contacts)

                # 6. Return response
                response_data = serializer.data
                response_data['police_contact'] = ContactSerializer(
                    police_station.police_contact.all(), many=True
                ).data

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # 6. DELETE Police Station
    def destroy(self, request, pk=None):
        try:
            police_station = get_object_or_404(PoliceStation, pk=pk)
            station_name = police_station.name
            police_station.delete()
            return Response({"message": f"Police station '{station_name}' is deleted successfully"}, status=status.HTTP_200_OK)
        except PoliceStation.DoesNotExist:
            return Response({"error": "Police station not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class PoliceStationListView(generics.ListAPIView):
    queryset = PoliceStation.objects.all().order_by("id")
    serializer_class = PoliceStationIdNameSerializer
    filterset_fields = ['id']


@api_view(['GET'])
def police_station_search(request):
    search_term = request.GET.get('search', '').strip()

    # Only search if at least 4 characters provided
    if len(search_term) >= 4:
        stations = PoliceStation.objects.filter(
            name__icontains=search_term
        ).order_by('name')
    else:
        stations = PoliceStation.objects.none()  # Return empty if <4 chars

    data = [{"id": station.id, "name": station.name} for station in stations]
    return Response(data)