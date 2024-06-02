from django.urls import path

from . import views

app_name = "asns_api"

urlpatterns = [
    path("", views.ListASNs.as_view(), name="list_asnss"),
]
