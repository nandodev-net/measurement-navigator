from django.conf.urls import include
from django.urls import path
from .views import EventsList, EventsData, EventUpdateView

app_name = 'events'

urlpatterns = [
    
    path(
        '',
        views.EventsList.as_view(),
        name="all"
    ),

    path(
        'data/',
        views.EventsData.as_view(),
        name="data"
    ),
    path(
        '<int:pk>',
        EventUpdateView.as_view(),
        name="event_edit"
    )       

]
