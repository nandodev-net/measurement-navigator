"""
    Serializer objects to send Cases to clients apps
"""

from rest_framework import serializers
from apps.main.cases.models import Case, Category
from apps.api.events_api.serializers import EventDataSerializer

class CategoryDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'display_name',
        ]

class CaseDataSerializer(serializers.ModelSerializer):
    """
        class created to define the format of
        serialization for the Case model.
    """
    
    category = CategoryDataSerializer(read_only=True)
    start_date_beautify = serializers.ReadOnlyField(source='get_start_date_beautify')
    end_date_beautify = serializers.ReadOnlyField(source='get_end_date_beautify')
    sites = serializers.ReadOnlyField(source='get_sites')
    asns = serializers.ReadOnlyField(source='get_asns')

    class Meta:
        model = Case
        fields = [
            'id', 
            'start_date_beautify',
            'end_date_beautify',
            'sites',
            'category',
            'title', 
            'asns'
        ]
        depth = 1

class CaseDetailDataSerializer(serializers.ModelSerializer):
    """
        class created to define the format of
        serialization for a instance of Case model.
    """

    category = CategoryDataSerializer(read_only=True)
    case_expired = serializers.ReadOnlyField(source='is_case_expired')
    start_date_beautify = serializers.ReadOnlyField(source='get_start_date_beautify')
    end_date_beautify = serializers.ReadOnlyField(source='get_end_date_beautify')
    sites = serializers.ReadOnlyField(source='get_sites')
    asns = serializers.ReadOnlyField(source='get_asns')


    class Meta:
        model = Case
        fields = [
            'id',
            'start_date_beautify',
            'end_date_beautify',
            'sites',
            'title',
            'asns',
            'description',
            'category'
            
        ]

class BlockedCasesNumberSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()

class CaseActiveNumberSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    active_cases = serializers.IntegerField()
    inactive_cases = serializers.IntegerField()

