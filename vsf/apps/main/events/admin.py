from django.contrib import admin
from .models import *

# Register your models here.
name = 'apps.main.events'


admin.site.register(Site)
admin.site.register(Target)
admin.site.register(Event)
admin.site.register(MutedInput)
admin.site.register(SiteCategory)

