"""
    This app contains every submeasurement model and its corresponding logic 
"""

from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(DNS)
admin.site.register(TCP)
admin.site.register(HTTP)

