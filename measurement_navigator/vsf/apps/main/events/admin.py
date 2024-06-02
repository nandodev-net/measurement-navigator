from django.contrib import admin

from .models import *

# Register your models here.
name = "apps.main.events"


admin.site.register(Event)
