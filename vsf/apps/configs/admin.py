from django.contrib import admin
from .models import Config

# Register your models here.
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('hardflag_timewindow','hardflag_openning_treshold', 'hardflag_interval_size', 'hardflag_continue_treshold')  # fields to display in the listing


admin.site.register(Config, ConfigAdmin)