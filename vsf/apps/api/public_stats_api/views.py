from django.http import Http404
import datetime
from decimal import Decimal
import json
import pytz
from apps.main.public_stats.models import *
from apps.main.asns.models          import ASN

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


class StatsByASN(generics.GenericAPIView):
    def get(self, request):
        stats = AsnPublicStats.objects.all()
        response = []
        for stat in stats:
            response.append({
                'asn': stat.asn.name,
                'blocked_domains': stat.blocked_domains_by_asn
            })    
        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)    
        

class StatsByCategory(generics.GenericAPIView):
    def get(self, request):
        stats = CategoryPublicStats.objects.all()    
        response = []
        for stat in stats:
            response.append({
                'category': stat.category.category_spa,
                'blocked_domains': stat.blocked_domains_by_category
            })    
        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)    



class SpeedInternetTimeline(generics.GenericAPIView):
    serializer_class = SpeedInternetTimelineSerializer

    
    def get(self, request):
        
        last_day = SpeedInternet.objects.last().day

        response = []
        for i in range(0, 4):
            date = last_day - datetime.timedelta( days = (i*7) )
            speed_data = SpeedInternet.objects.filter(day = date).first()
            
            response.append({
                'date': date.strftime("%b %d, %Y"),
                'download_average': speed_data.download_average
            })

        response_json = SpeedInternetTimelineSerializer(response, many=True)

        return Response(response_json.data, status=status.HTTP_200_OK)

class SpeedInternetByISPTimeline(generics.GenericAPIView):
    serializer_class = SpeedInternetByISPTimelineSerializer

    
    def get(self, request):
        
        last_day = SpeedInternetByISP.objects.last().day

        response = []

        
        asns = ASN.objects.all()
        for asn in asns:
            
            aux = []

            for i in range(0, 4):
                date = last_day - datetime.timedelta( days = (i*7) )
                speed_data = SpeedInternetByISP.objects.filter(
                    day = date,
                    asn = asn
                ).first()

                aux.append({
                    'date': date.strftime("%b %d, %Y"),
                    'download_average': float(speed_data.download_average)
                })

            response.append({
                asn.name: aux
            })    
            
        

        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)
