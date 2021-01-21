from django.conf.urls import include, url
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path

app_name = 'api'

urlpatterns = [
    path(
        'ooni_fp/',
        include('apps.api.fp_tables_api.urls', namespace='fp_tables'),
        ),
        path(
        'api-token-auth/', 
        obtain_auth_token, name='api_token_auth'),
]
