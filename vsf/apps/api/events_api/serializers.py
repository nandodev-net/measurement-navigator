"""
    Serializer objects to send Events to clients apps
"""

from rest_framework import serializers
from apps.main.events.models import Event

class EventDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'identification',
            'start_date',
            'end_date',
            'issue_type',
            ]

class EventDetailDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'identification',
            'confirmed',
            'start_date',
            'end_date',
            'public_evidence',
            'private_evidence',
            'issue_type',

        ]