"""
    Serializer objects to communicate with the OONI fast path
"""

from rest_framework import serializers

from apps.main.fp_tables.models import FastPath


class FastPathDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FastPath
        fields = "__all__"
