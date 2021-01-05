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
from apps.dashboard.sections.control_panel                  import views as control_panel_views


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
    path(
        'measurements/',
        include(
            'apps.dashboard.sections.measurements.urls',
            namespace='measurement'
        )
    ),

    #   Submeasurements
    path(
        'submeasurements/',
        include(
            'apps.dashboard.sections.measurements.submeasurements.urls',
            namespace='submeasurement'
        )
    ),

    #   Sites
    path(
        'sites/',
        include(
            'apps.dashboard.sections.sites.urls',
            namespace='site'
        )
    ),

    #   Events
    path(
        'events/',
        include(
            'apps.dashboard.sections.events.urls',
            namespace='event'
        )
    ),

    #   Cases
    path(
        'cases/',
        include(
            'apps.dashboard.sections.cases.urls',
            namespace='case'
        )
    ),

    #   Misc
    path('muted_Inputs',                    events_views.ListMutedInputs.as_view(),    name="list_muted_inputs"),
    path('probes',                          views.ListProbes.as_view(),         name="list_probes"),
    path(
        'control_panel/',
        include(
            'apps.dashboard.sections.control_panel.urls',
            namespace='control_panel'
        )
    )
]
