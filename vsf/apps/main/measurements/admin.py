"""
    This app is intended to store all logic and data related to measurement reports
"""


#Django imports
from django.contrib import admin

# Local imports
from .models import *
# Register your models here.

class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'domain',
        'asn',
        'raw_measurement_id',
        'anomaly'
    )

class RawMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'probe_asn',
        'test_name',
        'measurement_start_time',
        'input'
    )

admin.site.register(Measurement, MeasurementAdmin)
admin.site.register(RawMeasurement, RawMeasurementAdmin)
