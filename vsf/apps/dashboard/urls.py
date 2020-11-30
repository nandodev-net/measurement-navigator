"""vsf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from .                      import views
from django.contrib         import admin
from django.conf.urls import include, url
from django.urls            import include, path, re_path
from django.contrib.auth    import views            as auth_views
#Section import
from apps.dashboard.sections.events                         import views as events_views
from apps.dashboard.sections.cases                          import views as cases_views
from apps.dashboard.sections.sites                          import views as sites_views
from apps.dashboard.sections.measurements                   import views as measurements_views
from apps.dashboard.sections.measurements.submeasurements   import views as submeasurements_views



app_name = 'dashboard'
urlpatterns = [

    # Accounting pages
    path('login',                           views.VSFLogin.as_view(),           name='login'),
    path('',                                include('django.contrib.auth.urls')),

    # Site Pages

    #   Main dashboard
    path('',                                views.Dashboard.as_view(),          name="home"),
    path('get_measurement',                 views.GetMeasurement.as_view(),     name='get_measurement'),

    #   Measurements
    path('measurements_data',               measurements_views.ListMeasurementsBackEnd.as_view(),   name="list_measurements_data"),
    path('measurements',                    measurements_views.ListMeasurementsTemplate.as_view(),  name="list_measurements"),
    path('measurements/dns',                submeasurements_views.ListDNSTemplate.as_view(),           name='list_dns'),
    path('measurements/dns_data',           submeasurements_views.ListDNSBackEnd.as_view(),            name='list_dns_data'),
    path('measurements/http',               submeasurements_views.ListHTTPTemplate.as_view(),          name='list_http'),
    path('measurements/http_data',          submeasurements_views.ListHTTPBackEnd.as_view(),           name='list_http_data'),
    path('measurements/tcp',                submeasurements_views.ListTCPTemplate.as_view(),            name='list_tcp'),
    path('measurements/tcp_data',           submeasurements_views.ListTCPBackEnd.as_view(),             name='list_tcp_data'),
    #   Sites
    path('pages',                           sites_views.ListUrls.as_view(),               name="list_urls"),
    path('list_sites',                      sites_views.ListSites.as_view(),              name="list_sites"),
    path('sites/<int:id>',                  sites_views.SiteDetailView.as_view(),         name='site_details'),

    #   Events
    path('events',                          events_views.ListEvents.as_view(),         name="list_events"),

    #   Cases
    path('cases',                           cases_views.ListCases.as_view(),          name="list_cases"),
    path('cases/categories',                cases_views.ListCategories.as_view(),     name="list_categories"),
    path('cases/categories/new_category',   cases_views.NewCategory.as_view(),        name="new_category"),

    #   Misc
    path('muted_Inputs',                    events_views.ListMutedInputs.as_view(),    name="list_muted_inputs"),
    path('probes',                          views.ListProbes.as_view(),         name="list_probes"),
]
