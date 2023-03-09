from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "asns_api"

urlpatterns = [
    path(
        '', 
        views.ListASNs.as_view(), 
        name='list_asnss'
        ),

]