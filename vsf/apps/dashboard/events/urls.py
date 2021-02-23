from django.conf.urls import include
from django.urls import path
from .views import EventsList, EventsData

app_name = 'events'

urlpatterns = [
    
    path(
        'all/',
        EventsList.as_view(),
        name="all"
    ),
    path(
        'data/',
        EventsData.as_view(),
        name="data"
    ),
    path(
        '<int:pk>',
        views.EventUpdateView.as_view(),
        name="event_edit"
    )       

]
