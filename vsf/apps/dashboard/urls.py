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
from django.urls            import include, path, re_path
from django.contrib.auth    import views            as auth_views

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
    path('measurements_data',               views.ListMeasurementsBackEnd.as_view(),   name="list_measurements_data"),
    path('measurements',                    views.ListMeasurementsTemplate.as_view(),  name="list_measurements"),
    path('measurements/dns',                views.ListDNSTemplate.as_view(),            name='list_dns'),
    path('measurements/dns_data',           views.ListDNSBackEnd.as_view(),             name='list_dns_data'),

    #   Sites
    path('pages',                           views.ListUrls.as_view(),               name="list_urls"),
    path('list_sites',                      views.ListSites.as_view(),              name="list_sites"),
    path('sites/<int:id>',                  views.SiteDetailView.as_view(),         name='site_details'),

    #   Events
    path('events',                          views.ListEvents.as_view(),         name="list_events"),

    #   Cases
    path('cases',                           views.ListCases.as_view(),          name="list_cases"),
    path('cases/categories',                views.ListCategories.as_view(),     name="list_categories"),
    path('cases/categories/new_category',   views.NewCategory.as_view(),        name="new_category"),

    #   Misc
    path('muted_Inputs',                    views.ListMutedInputs.as_view(),    name="list_muted_inputs"),
    path('probes',                          views.ListProbes.as_view(),         name="list_probes"),
]
