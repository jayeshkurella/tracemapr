"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from Mainapp.Serializers.serializers import PersonSerializer
from Mainapp.models import Person

import logging

logger = logging.getLogger(__name__)
class RetrieveUnfilteredPersonView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        logger.info("RetrieveUnfilteredPersonView called with pk=%s", pk)
        try:
            person = Person.objects.filter(_is_deleted=False).prefetch_related(
                'addresses', 'contacts', 'additional_info',
                'last_known_details', 'firs', 'consent'
            ).get(pk=pk)
            logger.debug("Person found with pk=%s", pk)
            serializer = PersonSerializer(person)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            logger.warning("Person with pk=%s not found", pk)
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
