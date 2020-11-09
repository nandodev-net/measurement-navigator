"""
    This app is intended to store all logic and data related to measurement reports
"""


#Django imports
from django.contrib import admin

# Local imports
from .models import *
# Register your models here.

admin.site.register(Measurement)
admin.site.register(RawMeasurement)
