from django.contrib import admin

from .models import ASN


# Register your models here.
class ASNAdmin(admin.ModelAdmin):
    list_display = ("asn", "name")  # fields to display in the listing


admin.site.register(ASN, ASNAdmin)
