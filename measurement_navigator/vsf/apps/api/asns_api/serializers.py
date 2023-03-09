from rest_framework import serializers
from apps.main.asns.models import ASN



class ASNSDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASN
        fields = [
            'id',
            'name',
            'asn',
        ]