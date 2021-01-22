from django.http import Http404

from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import render

from apps.main.cases.models import Case, Category
from .serializers import CaseDataSerializer, CaseDetailDataSerializer

class ListCases(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all case instances in the database
    """
    serializer_class = CaseDataSerializer
    queryset = Case.objects.all()

    def get(self, request):
        cases = Case.objects.all()
        cases_json = CaseDataSerializer(cases, many=True)
        return Response(cases_json.data, status=status.HTTP_200_OK)


class CasesDetail(generics.GenericAPIView):
    """
        class created to provide response to endpoint 
        returning one case instance by id 
    """
    serializer_class = CaseDetailDataSerializer

    def get_object(self,id):
        try:
            return Case.objects.get(id=id)
        except Case.DoesNotExist:
            raise Http404
    
    def get(self, request, id):
        case = self.get_object(id)
        case_json = CaseDetailDataSerializer(case)
        return Response(case_json.data, status=status.HTTP_200_OK)
