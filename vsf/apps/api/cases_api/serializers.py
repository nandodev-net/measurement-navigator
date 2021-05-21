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
    start_date = serializers.ReadOnlyField(source='get_start_date')
    end_date = serializers.ReadOnlyField(source='get_end_date')
    class Meta:
        model = Case
        fields = [
            'id', 
            'title', 
            'description',
            'twitter_search',
            'category',
            'case_type',
            'start_date', 
            'end_date'
            ]

class CaseDetailDataSerializer(serializers.ModelSerializer):
    """
        class created to define the format of
        serialization for a instance of Case model.
    """
    events = EventDataSerializer(many=True, read_only=True)
    start_date = serializers.ReadOnlyField(source='get_start_date')
    end_date = serializers.ReadOnlyField(source='get_end_date')

    class Meta:
        model = Case
        fields = [
            'id',
            'title',
            'description',
            'start_date',
            'end_date',
            'category',
            'events',
            'twitter_search',
            ]

class CaseActiveNumberSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    active_cases = serializers.IntegerField()
    inactive_cases = serializers.IntegerField()