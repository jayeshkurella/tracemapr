
"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Q
from uuid import UUID

from Mainapp.Serializers.serializers import ApprovePersonSerializer, PersonSerializer
from Mainapp.models import Person
from Mainapp.all_paginations.approve_cases_pagination import StatusPagination

import logging
logger = logging.getLogger(__name__)

class BasePersonListView(generics.ListAPIView):
    serializer_class = ApprovePersonSerializer
    pagination_class = StatusPagination

    def get_queryset(self):
        logger.info("Fetching persons list with filters: %s", self.request.query_params.dict())
        queryset = Person.objects.all().order_by('-created_at','updated_at')

        # Get filter parameters
        state = self.request.query_params.get('state')
        district = self.request.query_params.get('district')
        city = self.request.query_params.get('city')
        village = self.request.query_params.get('village')
        police_station = self.request.query_params.get('police_station')
        case_id = self.request.query_params.get('case_id')

        # If case_id is provided, ignore all other filters and return exact match
        if case_id:
            logger.debug("Filtering by case_id: %s", case_id)
            return queryset.filter(case_id__iexact=case_id)

        # Otherwise, apply normal filters
        filters = Q()
        if state:
            logger.debug("Applying filter: state=%s", state)
            filters &= Q(state__iexact=state)
        if district:
            logger.debug("Applying filter: district=%s", district)
            filters &= Q(district__iexact=district)
        if city:
            logger.debug("Applying filter: city=%s", city)
            filters &= Q(city__iexact=city)
        if village:
            logger.debug("Applying filter: village=%s", village)
            filters &= Q(village__iexact=village)
        if police_station:
            try:
                filters &= Q(firs__police_station__id=UUID(police_station))
                logger.debug("Filtering by police_station UUID=%s", police_station)
            except ValueError:
                logger.warning("Invalid police_station UUID: %s", police_station)

        return queryset.filter(filters)

    def paginate_queryset(self, queryset):
        # Disable pagination if case_id is present
        if self.request.query_params.get('case_id'):
            return None
        return super().paginate_queryset(queryset)

class StatusPersonView(BasePersonListView):
    """Base view for status-specific endpoints with count"""
    status = None  # To be overridden by subclasses

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(person_approve_status=self.status)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # If case_id is present, return direct results without pagination
        if request.query_params.get('case_id'):
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })

        # Otherwise, apply pagination
        return super().list(request, *args, **kwargs)

class PendingPersonsView(StatusPersonView):
    permission_classes = [IsAdminUser]
    status = 'pending'


class ApprovedPersonsView(StatusPersonView):
    permission_classes = [IsAdminUser]
    status = 'approved'


class RejectedPersonsView(StatusPersonView):
    permission_classes = [IsAdminUser]
    status = 'rejected'


class OnHoldPersonsView(StatusPersonView):
    permission_classes = [IsAdminUser]
    status = 'on_hold'


class SuspendedPersonsView(StatusPersonView):
    permission_classes = [IsAdminUser]
    status = 'suspended'


class StatusCountView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        base_qs = BasePersonListView().get_queryset()
        return Response({
            'pending': base_qs.filter(person_approve_status='pending').count(),
            'approved': base_qs.filter(person_approve_status='approved').count(),
            'rejected': base_qs.filter(person_approve_status='rejected').count(),
            'on_hold': base_qs.filter(person_approve_status='on_hold').count(),
            'suspended': base_qs.filter(person_approve_status='suspended').count(),
        })