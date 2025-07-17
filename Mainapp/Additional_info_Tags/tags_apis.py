"""
Created By : Sanket Lodhe
Created Date : Feb 2025
"""
from rest_framework import generics

from .tags_model import Caste, educational_tag, occupation_tags
from .tag_serializers import CasteSerializer, educationalSerializer, occupationSerializer
from ..access_permision import AllUserAccess, IsAdminUser


class CasteListCreateAPIView(generics.ListCreateAPIView):
    queryset = Caste.objects.all().order_by('name')
    serializer_class = CasteSerializer


class CasteDestroyAPIView(generics.DestroyAPIView):
    queryset = Caste.objects.all()
    serializer_class = CasteSerializer
    permission_classes = [IsAdminUser]


class educationaltagAPIView(generics.ListCreateAPIView):
    queryset = educational_tag.objects.all().order_by('name')
    serializer_class = educationalSerializer

class occupationtagAPIView(generics.ListCreateAPIView):
    queryset = occupation_tags.objects.all().order_by('name')
    serializer_class = occupationSerializer

