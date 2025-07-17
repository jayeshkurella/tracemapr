"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from Mainapp.Serializers.serializers import PersonSerializer
from Mainapp.models import Person


class RetrieveUnfilteredPersonView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        try:
            person = Person.objects.filter(_is_deleted=False).prefetch_related(
                'addresses', 'contacts', 'additional_info',
                'last_known_details', 'firs', 'consent'
            ).get(pk=pk)
            serializer = PersonSerializer(person)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
