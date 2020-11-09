# Django imports 
from rest_framework.response    import Response
from rest_framework.generics    import  (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.status      import  (
    HTTP_200_OK, 
    HTTP_201_CREATED, 
    HTTP_204_NO_CONTENT, 
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_412_PRECONDITION_FAILED
)
from   django.shortcuts         import render
from   rest_framework.views     import APIView
import django.utils.timezone    as timezone

# Third party imports
import time
import json
import requests
import datetime

# Local imports
from apps.main.sites.models             import URL
from .                                  import utils
from apps.main.ooni_fp.fp_tables.models import FastPath

class FastPathIngestView(APIView):
    """
        This view will receive a post request containing the CC (contry code),
        since (start date), until (end date), and if the data is valid, it will perform
        a get request to the ooni api to store data that matches the provided data and then store it 
        in the data base. Since the data format that comes from the fast path is not
        uniform and well-known, we can't use a serializer. We have to perform data validation
        by hand.

        The expected dates should be in the following format: 
            YYYY-mm-dd
    """
    # i don't know if this should be in settings @TODO
    """
        The url where de data will be asked to the ooni fast path
    """
    ooni_url = 'https://api.ooni.io/api/v1/measurements' 

    def post(self, request, since, until, format=None):
        #try:
        (status, measurements) = utils.request_fp_data(since, until)        
        #except:
        #    return Response([], status=HTTP_400_BAD_REQUEST)

        return Response(measurements, status=status)


   