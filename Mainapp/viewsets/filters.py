
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""


from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from ..models import Person, Address

from rest_framework.permissions import AllowAny

class filter_Address_ViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def normalize(self, queryset):
        # Remove None/empty, convert to title case, deduplicate
        return sorted(set(s.strip().title() for s in queryset if s and s.strip()))

    @action(detail=False, methods=['GET'])
    def states(self, request):
        person_states = Person.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)
        address_states = Address.objects.filter(~Q(state=None), ~Q(state='')).values_list('state', flat=True)

        states = self.normalize(person_states) + self.normalize(address_states)
        return Response(sorted(set(states)))

    @action(detail=False, methods=['GET'])
    def districts(self, request):
        state = request.query_params.get('state')
        if not state:
            return Response({"error": "Please select a state to view districts."}, status=400)

        person_districts = Person.objects.filter(state__iexact=state).exclude(district__isnull=True).exclude(district__exact='').values_list('district', flat=True)
        address_districts = Address.objects.filter(state__iexact=state).exclude(district__isnull=True).exclude(district__exact='').values_list('district', flat=True)

        districts = self.normalize(person_districts) + self.normalize(address_districts)
        return Response(sorted(set(districts)))

    @action(detail=False, methods=['GET'])
    def cities(self, request):
        district = request.query_params.get('district')
        if not district:
            return Response({"error": "Please select a district to view cities."}, status=400)

        person_cities = Person.objects.filter(district__iexact=district).exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True)
        address_cities = Address.objects.filter(district__iexact=district).exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True)

        cities = self.normalize(person_cities) + self.normalize(address_cities)
        return Response(sorted(set(cities)))

    @action(detail=False, methods=['GET'])
    def villages(self, request):
        city = request.query_params.get('city')
        if not city:
            return Response({"error": "Please select a city to view villages."}, status=400)

        person_villages = Person.objects.filter(city__iexact=city).exclude(village__isnull=True).exclude(village__exact='').values_list('village', flat=True)
        address_villages = Address.objects.filter(city__iexact=city).exclude(village__isnull=True).exclude(village__exact='').values_list('village', flat=True)

        villages = self.normalize(person_villages) + self.normalize(address_villages)
        return Response(sorted(set(villages)))