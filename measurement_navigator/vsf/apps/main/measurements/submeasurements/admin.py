"""
    This app contains every submeasurement model and its corresponding logic 
"""

from django.contrib import admin
from .models import *

class SubMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flag_type",
        "event",
        "confirmed",
        "measurement_id"
    )

# Register your models here.
admin.site.register(DNS, SubMeasurementAdmin)
admin.site.register(TCP, SubMeasurementAdmin)
admin.site.register(HTTP, SubMeasurementAdmin)

