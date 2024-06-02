from rest_framework import serializers

from apps.main.public_stats.models import *


class GeneralPublicStatsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralPublicStats
        fields = "__all__"


class AsnPublicStatsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsnPublicStats
        fields = "__all__"


class CategoryPublicStatsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryPublicStats
        fields = "__all__"


class SpeedInternetTimelineSerializer(serializers.Serializer):
    date = serializers.DateField()
    download_average = serializers.FloatField()


class SpeedInternetByISPTimelineSerializer(serializers.Serializer):
    date = serializers.DateField()
    download_average = serializers.FloatField()
