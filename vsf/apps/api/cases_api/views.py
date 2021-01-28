from django.http import Http404

from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import render

from apps.main.cases.models import Case, Category
from .serializers import CategoryDataSerializer, CaseDataSerializer, CaseDetailDataSerializer, CaseActiveNumberSerializer


class ListCategories(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all category instances in the database
    """
    serializer_class = CategoryDataSerializer
    queryset = Category.objects.all()

    def get(self, request):
        categories = Category.objects.all()
        categories_json = CategoryDataSerializer(categories, many=True)
        return Response(categories_json.data, status=status.HTTP_200_OK)


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


class CaseDetail(generics.GenericAPIView):
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


class ListCasesByCategory(generics.GenericAPIView):
    """
        class created to provide response to endpoint listing
        all case instances by category
    """
    serializer_class = CaseDataSerializer
    queryset = Case.objects.all()

    def get(self, request, cat_id):
        cases = Case.objects.filter(category__id = cat_id)
        cases_json = CaseDataSerializer(cases, many=True)
        return Response(cases_json.data, status=status.HTTP_200_OK)


class CaseActiveNumber(generics.GenericAPIView):
    """
        class created to provide response to endpoint 
        returning total number of active cases 
    """
    queryset = Case.objects.all()

    def get(self, request):
        total_cases = Case.objects.count()
        active_cases = Case.objects.filter(end_date=None).count()

        cases_json = {
            'total_cases' : total_cases,
            'active_cases' : active_cases,
            'inactive_cases' : total_cases - active_cases
        }
        cases_json = CaseActiveNumberSerializer(cases_json)
        return Response(cases_json.data, status=status.HTTP_200_OK)