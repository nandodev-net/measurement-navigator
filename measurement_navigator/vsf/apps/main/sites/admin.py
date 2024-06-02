from django.contrib import admin

from .models import *


class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "description_spa",
        "description_eng",
    )


class UrlAdmin(admin.ModelAdmin):
    list_display = ("url", "site")


class SiteCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "old_code",
        "category_spa",
        "category_eng",
        "description_spa",
        "description_eng",
    )


admin.site.register(Site, SiteAdmin)
admin.site.register(URL, UrlAdmin)
admin.site.register(SiteCategory, SiteCategoryAdmin)
