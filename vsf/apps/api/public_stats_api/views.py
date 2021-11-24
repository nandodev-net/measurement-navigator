from django.http import Http404
import datetime
import json
import pytz
from apps.main.public_stats.models import *

from rest_framework import status, generics
from rest_framework.response import Response
from .serializers import *


class GetGeneralPublicStats(generics.GenericAPIView):
    serializer_class = GeneralPublicStatsDataSerializer

    def get_object(self):
        try:
            return GeneralPublicStats.objects.get(id=1)
        except GeneralPublicStats.DoesNotExist:
            raise Http404

    def get(self, request):
        stat = self.get_object()
        stat_json = GeneralPublicStatsDataSerializer(stat)
        return Response(stat_json.data, status=status.HTTP_200_OK)


class GetAsnPublicStats(generics.GenericAPIView):
    serializer_class = AsnPublicStatsDataSerializer

    def get_object(self,id):
        try:
            return AsnPublicStats.objects.get(asn__id=id)
        except AsnPublicStats.DoesNotExist:
            raise Http404
    
    def get(self, request, id):
        stat = self.get_object(id)
        stat_json = AsnPublicStatsDataSerializer(stat)
        return Response(stat_json.data, status=status.HTTP_200_OK)


class GetCategoryPublicStats(generics.GenericAPIView):
    serializer_class = CategoryPublicStatsDataSerializer

    def get_object(self,id):
        try:
            return CategoryPublicStats.objects.get(category__id=id)
        except CategoryPublicStats.DoesNotExist:
            raise Http404
    
    def get(self, request, id):
        stat = self.get_object(id)
        stat_json = CategoryPublicStatsDataSerializer(stat)
        return Response(stat_json.data, status=status.HTTP_200_OK)