from django.http import Http404
import datetime
import json
import pytz

from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import render
from apps.main.measurements.submeasurements.models import *

from apps.main.measurements.models import Measurement, RawMeasurement
from apps.main.measurements.submeasurements.models import DNS, HTTP, TCP


from .serializers import (  MeasurementListDataSerializer,
                            MeasurementDetailSerializer,
                        )

utc=pytz.UTC

class ListMeasurements(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all measurements instances in the database
    """
    serializer_class = MeasurementListDataSerializer
    queryset = Measurement.objects.all()

    def get(self, request):
        measurements = Measurement.objects.all()
        measurements_json = MeasurementListDataSerializer(measurements, many=True)
        return Response(measurements_json.data, status=status.HTTP_200_OK)


class MeasurementDetail(generics.GenericAPIView):
    """
        class created to provide response to endpoint 
        returning one measurement instance by id 
    """
    serializer_class = MeasurementDetailSerializer

    def get_object(self,id):
        try:
            return Measurement.objects.get(id=id)
        except Measurement.DoesNotExist:
            raise Http404
    
    def get(self, request, id):
        measurement = self.get_object(id)
        
        dns = measurement.dns_list
        http = measurement.http_list
        tcp = measurement.tcp_list

        submeasurement = {'DNS':dns, 'HTTP':http, 'TCP':tcp}
        _measurement = {'measurement':measurement,'submeasurement':submeasurement}

        measurement_json = MeasurementDetailSerializer(_measurement)
        return Response(measurement_json.data, status=status.HTTP_200_OK)
