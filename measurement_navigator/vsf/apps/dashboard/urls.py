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

from django.urls import include, path

from . import views

app_name = "dashboard"
urlpatterns = [
    # Auth
    path("login", views.VSFLogin.as_view(), name="login"),
    path("set_tz/", views.TZoneSelectorView.as_view(), name="set_tz"),
    path("", include("django.contrib.auth.urls")),
    # --------------- Sections --------------- #
    # -- Home
    path("", views.Dashboard.as_view(), name="home"),
    path("get_measurement", views.GetMeasurement.as_view(), name="get_measurement"),
    # -- Measurements
    path(
        "measurements/",
        include("apps.dashboard.measurements.urls", namespace="measurement"),
    ),
    # -- Submeasurements
    path(
        "submeasurements/",
        include(
            "apps.dashboard.measurements.submeasurements.urls",
            namespace="submeasurement",
        ),
    ),
    # -- Sites
    path("sites/", include("apps.dashboard.sites.urls", namespace="site")),
    # -- Event cases
    path("cases/", include("apps.dashboard.event_cases.urls", namespace="event_case")),
    # -- Events
    path("events/", include("apps.dashboard.events.urls", namespace="events")),
    # -- Control Panel
    path(
        "control_panel/",
        include("apps.dashboard.control_panel.urls", namespace="control_panel"),
    ),
    # -- Users
    path("users/", include("apps.dashboard.users.urls", namespace="users")),
    # -- Misc
    path("probes", views.ListProbes.as_view(), name="list_probes"),
]
