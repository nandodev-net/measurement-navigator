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
    events = EventDataSerializer(many=True, read_only=True)
    start_date = serializers.ReadOnlyField(source='get_start_date')
    end_date = serializers.ReadOnlyField(source='get_end_date')
    category = CategoryDataSerializer(read_only=True)
    case_expired = serializers.ReadOnlyField(source='is_case_expired')
    start_date_beautify = serializers.ReadOnlyField(source='get_start_date_beautify')
    end_date_beautify = serializers.ReadOnlyField(source='get_end_date_beautify')

    class Meta:
        model = Case
        fields = [
            'id',
            'title',
            'description',
            'start_date',
            'end_date',
            'category',
            'case_type',
            'events',
            'twitter_search',
            'case_expired',
            'start_date_beautify',
            'end_date_beautify'
        ]

class CaseActiveNumberSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    active_cases = serializers.IntegerField()
    inactive_cases = serializers.IntegerField()