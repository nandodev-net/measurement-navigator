from django.contrib import admin
from .models import *


# Register your models here.

name = "main.apps.cases"

admin.site.register(Category)
admin.site.register(Case)
admin.site.register(Update)