#
# """
# Created By : Sanket Lodhe
# Created Date : Feb 2025
# """
#
#
# from django.db.models import Q
# from rest_framework import viewsets
# from rest_framework.response import Response
# from rest_framework.decorators import action
#
# from ..models import Person, Address
#
# from rest_framework.permissions import AllowAny
#
#
# class filter_Address_ViewSet(viewsets.ViewSet):
#     permission_classes = [AllowAny]
#
#     def normalize(self, queryset):
#         # Remove None/empty, convert to title case, deduplicate
#         return sorted(set(s.strip().title() for s in queryset if s and s.strip()))
#
#     @action(detail=False, methods=['GET'])
#     def states(self, request):
#         person_states = Person.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)
#         address_states = Address.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)
#
#         states = self.normalize(person_states) + self.normalize(address_states)
#         return Response(sorted(set(states)))
#
#     @action(detail=False, methods=['GET'])
#     def districts(self, request):
#         state = request.query_params.get('state')
#         if not state:
#             return Response({"error": "Please select a state to view districts."}, status=400)
#
#         person_districts = Person.objects.filter(state__iexact=state).exclude(district__isnull=True).exclude(district__exact='').values_list('district', flat=True)
#         address_districts = Address.objects.filter(state__iexact=state).exclude(district__isnull=True).exclude(district__exact='').values_list('district', flat=True)
#
#         districts = self.normalize(person_districts) + self.normalize(address_districts)
#         return Response(sorted(set(districts)))
#
#     @action(detail=False, methods=['GET'])
#     def cities(self, request):
#         district = request.query_params.get('district')
#         if not district:
#             return Response({"error": "Please select a district to view cities."}, status=400)
#
#         person_cities = Person.objects.filter(district__iexact=district).exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True)
#         address_cities = Address.objects.filter(district__iexact=district).exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True)
#
#         cities = self.normalize(person_cities) + self.normalize(address_cities)
#         return Response(sorted(set(cities)))
#
#     @action(detail=False, methods=['GET'])
#     def villages(self, request):
#         city = request.query_params.get('city')
#         if not city:
#             return Response({"error": "Please select a city to view villages."}, status=400)
#
#         person_villages = Person.objects.filter(city__iexact=city).exclude(village__isnull=True).exclude(village__exact='').values_list('village', flat=True)
#         address_villages = Address.objects.filter(city__iexact=city).exclude(village__isnull=True).exclude(village__exact='').values_list('village', flat=True)
#
#         villages = self.normalize(person_villages) + self.normalize(address_villages)
#         return Response(sorted(set(villages)))

"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

import logging
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from ..models import Person, Address

logger = logging.getLogger(__name__)


class filter_Address_ViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def normalize(self, queryset):
        """Normalize and clean the queryset data"""
        logger.debug(f"Normalizing queryset with {len(queryset)} items")
        # Remove None/empty, convert to title case, deduplicate
        normalized = sorted(set(s.strip().title() for s in queryset if s and s.strip()))
        logger.debug(f"Normalized to {len(normalized)} unique items")
        return normalized

    @action(detail=False, methods=['GET'])
    def states(self, request):
        """Get all unique states from Person and Address models"""
        logger.info(f"STATES request received from client: {request.META.get('REMOTE_ADDR')}")
        logger.debug(f"Request query params: {dict(request.query_params)}")

        try:
            # Get states from Person model
            person_states = Person.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)
            logger.debug(f"Found {person_states.count()} states from Person model")

            # Get states from Address model
            address_states = Address.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)
            logger.debug(f"Found {address_states.count()} states from Address model")

            # Normalize and combine
            states = self.normalize(person_states) + self.normalize(address_states)
            unique_states = sorted(set(states))

            logger.info(f"Returning {len(unique_states)} unique states")
            logger.debug(f"States data: {unique_states}")

            return Response(unique_states)

        except Exception as e:
            logger.error(f"Error fetching states: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({"error": "Failed to fetch states"}, status=500)

    @action(detail=False, methods=['GET'])
    def districts(self, request):
        """Get districts for a specific state"""
        logger.info(f"DISTRICTS request received from client: {request.META.get('REMOTE_ADDR')}")
        logger.debug(f"Request query params: {dict(request.query_params)}")

        state = request.query_params.get('state')
        if not state:
            logger.warning("District request missing 'state' parameter")
            return Response({"error": "Please select a state to view districts."}, status=400)

        logger.debug(f"Fetching districts for state: {state}")

        try:
            # Get districts from Person model for the given state
            person_districts = Person.objects.filter(state__iexact=state).exclude(
                district__isnull=True).exclude(district__exact='').values_list('district', flat=True)
            logger.debug(f"Found {person_districts.count()} districts from Person model for state: {state}")

            # Get districts from Address model for the given state
            address_districts = Address.objects.filter(state__iexact=state).exclude(
                district__isnull=True).exclude(district__exact='').values_list('district', flat=True)
            logger.debug(f"Found {address_districts.count()} districts from Address model for state: {state}")

            # Normalize and combine
            districts = self.normalize(person_districts) + self.normalize(address_districts)
            unique_districts = sorted(set(districts))

            logger.info(f"Returning {len(unique_districts)} unique districts for state: {state}")
            logger.debug(f"Districts data for {state}: {unique_districts}")

            return Response(unique_districts)

        except Exception as e:
            logger.error(f"Error fetching districts for state {state}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({"error": f"Failed to fetch districts for state: {state}"}, status=500)

    @action(detail=False, methods=['GET'])
    def cities(self, request):
        """Get cities for a specific district"""
        logger.info(f"CITIES request received from client: {request.META.get('REMOTE_ADDR')}")
        logger.debug(f"Request query params: {dict(request.query_params)}")

        district = request.query_params.get('district')
        if not district:
            logger.warning("City request missing 'district' parameter")
            return Response({"error": "Please select a district to view cities."}, status=400)

        logger.debug(f"Fetching cities for district: {district}")

        try:
            # Get cities from Person model for the given district
            person_cities = Person.objects.filter(district__iexact=district).exclude(
                city__isnull=True).exclude(city__exact='').values_list('city', flat=True)
            logger.debug(f"Found {person_cities.count()} cities from Person model for district: {district}")

            # Get cities from Address model for the given district
            address_cities = Address.objects.filter(district__iexact=district).exclude(
                city__isnull=True).exclude(city__exact='').values_list('city', flat=True)
            logger.debug(f"Found {address_cities.count()} cities from Address model for district: {district}")

            # Normalize and combine
            cities = self.normalize(person_cities) + self.normalize(address_cities)
            unique_cities = sorted(set(cities))

            logger.info(f"Returning {len(unique_cities)} unique cities for district: {district}")
            logger.debug(f"Cities data for {district}: {unique_cities}")

            return Response(unique_cities)

        except Exception as e:
            logger.error(f"Error fetching cities for district {district}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({"error": f"Failed to fetch cities for district: {district}"}, status=500)

    @action(detail=False, methods=['GET'])
    def villages(self, request):
        """Get villages for a specific city"""
        logger.info(f"VILLAGES request received from client: {request.META.get('REMOTE_ADDR')}")
        logger.debug(f"Request query params: {dict(request.query_params)}")

        city = request.query_params.get('city')
        if not city:
            logger.warning("Village request missing 'city' parameter")
            return Response({"error": "Please select a city to view villages."}, status=400)

        logger.debug(f"Fetching villages for city: {city}")

        try:
            # Get villages from Person model for the given city
            person_villages = Person.objects.filter(city__iexact=city).exclude(
                village__isnull=True).exclude(village__exact='').values_list('village', flat=True)
            logger.debug(f"Found {person_villages.count()} villages from Person model for city: {city}")

            # Get villages from Address model for the given city
            address_villages = Address.objects.filter(city__iexact=city).exclude(
                village__isnull=True).exclude(village__exact='').values_list('village', flat=True)
            logger.debug(f"Found {address_villages.count()} villages from Address model for city: {city}")

            # Normalize and combine
            villages = self.normalize(person_villages) + self.normalize(address_villages)
            unique_villages = sorted(set(villages))

            logger.info(f"Returning {len(unique_villages)} unique villages for city: {city}")
            logger.debug(f"Villages data for {city}: {unique_villages}")

            return Response(unique_villages)

        except Exception as e:
            logger.error(f"Error fetching villages for city {city}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({"error": f"Failed to fetch villages for city: {city}"}, status=500)