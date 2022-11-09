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
# Django imports
from django.contrib         import admin
from django.urls            import include, path, re_path

# Local imports
from .                      import views


app_name = 'sites'
urlpatterns = [

    # Delete site url
    path("delete",          views.DeleteSiteView.as_view(),         name='delete_site'),
    path('add_site',        views.CreateSiteView.as_view(),         name="create_site"),
    path("remove_from_site",views.RemoveUrlFromSite.as_view(),      name="remove_from_site" ),

]