from rest_framework import serializers

from apps.main.measurements.models import Measurement, RawMeasurement
from apps.main.measurements.submeasurements.models import (DNS, HTTP, TCP,
                                                           DNSJsonFields)


class MeasurementListDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = [
            "id",
        ]


class RawMeasurementDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMeasurement
        fields = "__all__"


class HTTPSubmeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = HTTP
        fields = "__all__"


class TCPSubmeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCP
        fields = "__all__"


class DNSJsonFieldsSerializer(serializers.ModelSerializer):
    control_resolver_answers = serializers.JSONField()
    answers = serializers.JSONField()

    class Meta:
        model = DNSJsonFields
        fields = [
            "control_resolver_answers",
            "answers",
        ]


class DNSSubmeasurementSerializer(serializers.ModelSerializer):
    jsons = DNSJsonFieldsSerializer(read_only=True)

    class Meta:
        model = DNS
        fields = [
            "control_resolver_failure",
            "control_resolver_hostname",
            "failure",
            "resolver_hostname",
            "inconsistent",
            "dns_consistency",
            "hostname",
            "jsons",
            "client_resolver",
        ]


class SubMeasurementDataSerializer(serializers.Serializer):
    DNS = DNSSubmeasurementSerializer(read_only=True, many=True)
    HTTP = HTTPSubmeasurementSerializer(read_only=True, many=True)
    TCP = TCPSubmeasurementSerializer(read_only=True, many=True)


class MeasurementDataSerializer(serializers.ModelSerializer):

    raw_measurement = RawMeasurementDataSerializer(read_only=True)

    class Meta:
        model = Measurement
        fields = [
            "id",
            "raw_measurement",
            "anomaly",
            "domain",
            "asn",
        ]


class MeasurementDetailSerializer(serializers.Serializer):
    measurement = MeasurementDataSerializer(read_only=True)
    submeasurement = SubMeasurementDataSerializer(read_only=True)
