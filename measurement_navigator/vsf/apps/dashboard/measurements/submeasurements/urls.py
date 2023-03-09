from django.conf.urls import include
from django.urls import path
from .views import *
from django.views.decorators.cache  import cache_page


app_name = 'submeasurements'

urlpatterns = [

    path(
        'dns/',
        ListDNSTemplate.as_view(),
        name='list_dns'
    ),
    path(
        'dns_data/',
        # seconds * n_minutes
        cache_page(60 * 5, cache='filesystem')(ListDNSBackEnd.as_view()),
        name='list_dns_data'
    ),
    path(
        'http/',
        ListHTTPTemplate.as_view(),
        name='list_http'
    ),
    path(
        'http_data/',
        ListHTTPBackEnd.as_view(),
        name='list_http_data'
    ),
    path(
        'tcp/',
        ListTCPTemplate.as_view(),
        name='list_tcp'
    ),
    path(
        'tcp_data/',
        ListTCPBackEnd.as_view(),
        name='list_tcp_data'
    ),
    path(
        'tor/',
        ListTorTemplate.as_view(),
        name='list_tor'
    ),
    path(
        'tor_data/',
        ListTORBackEnd.as_view(),
        name='list_tor_data'
    ),

]