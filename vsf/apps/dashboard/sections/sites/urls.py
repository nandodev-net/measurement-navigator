from django.conf.urls import include
from django.urls import path
from .views import ListSites, ListDomains, SiteDetailView

app_name = 'sites'

urlpatterns = [
    path(
        'list_domains/',
        ListDomains.as_view(),
        name='list_domains'
        ),

    path(
        'list_sites/',
        ListSites.as_view(),
        name='list_sites'
        ),

    path(
        'sites/<int:id>/',
        SiteDetailView.as_view(),
        name='site_details'
        ),
]