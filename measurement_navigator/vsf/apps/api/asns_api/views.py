from django.http import Http404

from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import render

from apps.main.asns.models import ASN
from .serializers import ASNSDataSerializer


class ListASNs(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all asn instances in the database
    """
    serializer_class = ASNSDataSerializer
    queryset = ASN.objects.all()

    def get(self, request):
        asns = ASN.objects.all()
        asns_json = ASNSDataSerializer(asns, many=True)
        return Response(asns_json.data, status=status.HTTP_200_OK)

