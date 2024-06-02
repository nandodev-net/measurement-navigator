from django.contrib import admin
from django.urls import include, path, re_path

from . import views

app_name = "public_stats_api"

urlpatterns = [
    path("general", views.GetGeneralPublicStats.as_view(), name="general_public_stats"),
    path("asn/<str:id>", views.GetAsnPublicStats.as_view(), name="asn_public_stats"),
    path("asn", views.StatsByASN.as_view(), name="stats_by_asn"),
    path(
        "category/<str:id>",
        views.GetCategoryPublicStats.as_view(),
        name="category_public_stats",
    ),
    path("category", views.StatsByCategory.as_view(), name="stats_by_category"),
    path(
        "speed_timeline/", views.SpeedInternetTimeline.as_view(), name="speed_internet"
    ),
    path(
        "speed_timeline_asn/",
        views.SpeedInternetByISPTimeline.as_view(),
        name="speed_internet_asn",
    ),
]
