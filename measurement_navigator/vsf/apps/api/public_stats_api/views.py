import datetime
import json
from decimal import Decimal

import pytz
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response

from apps.main.asns.models import ASN
from apps.main.public_stats.models import *

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

    def get_object(self, id):
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

    def get_object(self, id):
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
        response = {"names": [], "blocked_domains": []}
        for stat in stats:
            response["names"].append(stat.asn.name)
            response["blocked_domains"].append(stat.blocked_domains_by_asn)

        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)


class StatsByCategory(generics.GenericAPIView):
    def get(self, request):
        stats = CategoryPublicStats.objects.all()
        response = {
            "category_name_1": "",
            "blocked_domains_1": 0,
            "category_name_2": "",
            "blocked_domains_2": 0,
        }

        for stat in stats:
            if stat.blocked_domains_by_category > response["blocked_domains_1"]:
                response["category_name_1"] = stat.category.category_spa
                response["blocked_domains_1"] = int(stat.blocked_domains_by_category)
            elif stat.blocked_domains_by_category > response["blocked_domains_2"]:
                response["category_name_2"] = stat.category.category_spa
                response["blocked_domains_2"] = int(stat.blocked_domains_by_category)

        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)


class SpeedInternetTimeline(generics.GenericAPIView):
    serializer_class = SpeedInternetTimelineSerializer

    def get(self, request):

        last_day = SpeedInternet.objects.last().day

        response = {"dates": [], "data": []}
        for i in range(0, 4):
            date = last_day - datetime.timedelta(days=(i * 7))
            speed_data = SpeedInternet.objects.filter(day=date).first()

            response["dates"].append(date.strftime("%b %d, %Y"))
            response["data"].append(float(speed_data.download_average))

        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)


class SpeedInternetByISPTimeline(generics.GenericAPIView):
    serializer_class = SpeedInternetByISPTimelineSerializer

    def get(self, request):

        last_day = SpeedInternetByISP.objects.last().day

        response = []

        asns = ASN.objects.all()
        for asn in asns:

            aux = []

            for i in range(0, 4):
                date = last_day - datetime.timedelta(days=(i * 7))
                speed_data = SpeedInternetByISP.objects.filter(
                    day=date, asn=asn
                ).first()

                if speed_data:
                    aux.append(
                        {
                            "date": date.strftime("%b %d, %Y"),
                            "download_average": float(speed_data.download_average),
                        }
                    )

            response.append({asn.name: aux})

        response_json = json.dumps(response)
        return Response(json.loads(response_json), status=status.HTTP_200_OK)
