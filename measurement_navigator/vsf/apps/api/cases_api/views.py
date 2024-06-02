import datetime

from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response

from apps.api.utils import utc_aware_date
from apps.main.cases.models import Case, Category

from .serializers import *


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


class ListCasesByDate(generics.GenericAPIView):
    """
    class created to provide response to endpoint listing
    all case instances in the database
    """

    serializer_class = CaseDataSerializer
    queryset = Case.objects.all()

    def get(self, start_date, end_date, request):
        cases = Case.objects.all()

        if start_date is not None and start_date != "":
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            utc_start_date = utc_aware_date(start_date)
            cases = cases.filter(created__gte=utc_start_date)

        if end_date is not None and end_date != "":
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            utc_end_date = utc_aware_date(end_date)
            cases = cases.filter(
                created__lte=utc_end_date + datetime.timedelta(hours=24)
            )

        cases_json = CaseDataSerializer(cases, many=True)
        return Response(cases_json.data, status=status.HTTP_200_OK)


class CaseDetail(generics.GenericAPIView):
    """
    class created to provide response to endpoint
    returning one case instance by id
    """

    serializer_class = CaseDetailDataSerializer

    def get_object(self, id):
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
        cases = Case.objects.filter(category__id=cat_id)
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
            "total_cases": total_cases,
            "active_cases": active_cases,
            "inactive_cases": total_cases - active_cases,
        }
        cases_json = CaseActiveNumberSerializer(cases_json)
        return Response(cases_json.data, status=status.HTTP_200_OK)


class BlockedCasesNumber(generics.GenericAPIView):
    """
    class used to show the number of open cases
    related to an internet blockage
    """

    queryset = Case.objects.all()

    def get(self, request):
        cases = Case.objects.filter(case_type="bloqueo").count()
        cases_json = {"total_cases": cases}
        cases_json = BlockedCasesNumberSerializer(cases_json)
        return Response(cases_json.data, status=status.HTTP_200_OK)
