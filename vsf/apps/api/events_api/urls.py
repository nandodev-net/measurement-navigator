from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "events_api"

urlpatterns = [
    path(
        '', 
        views.ListEvents.as_view(), 
        name='list_events'
        ),

    path(
        '<int:id>', 
        views.EventDetail.as_view(), 
        name='event_detail'),

]