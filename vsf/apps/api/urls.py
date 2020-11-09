from django.conf.urls import include, url
from django.urls import path

app_name = 'api'

urlpatterns = [
    path(
        'ooni_fp/',
        include('apps.api.fp_tables_api.urls', namespace='fp_tables'),
    )
]
