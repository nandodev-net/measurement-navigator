from django.contrib import admin
from .models import Config

# Register your models here.
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('hardflag_timewindow','hardflag_minmeasurements')  # fields to display in the listing



admin.site.register(Config, ConfigAdmin)