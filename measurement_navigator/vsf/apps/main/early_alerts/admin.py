"""
    This app implements the early alert system
"""
#Django imports
from django.contrib import admin

# Local imports
from .models import *
# Register your models here.

admin.site.register(Input)
admin.site.register(EarlyAlertConfig)
admin.site.register(Emails)
