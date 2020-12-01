from django.conf.urls import include
from django.urls import path
from .views import ListEvents

app_name = 'events'

urlpatterns = [
    path(
        'list_events/',
        ListEvents.as_view(),
        name='list_events',
    ),
]