from rest_framework import serializers
from apps.main.measurements.models import Measurement, RawMeasurement
from apps.main.measurements.submeasurements.models import DNS, HTTP, TCP

class MeasurementListDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = [
            'id',
        ]