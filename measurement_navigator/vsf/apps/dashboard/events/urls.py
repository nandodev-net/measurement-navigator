from django.conf.urls import include
from django.urls import path
from .views import EventsList, EventsData, EventUpdateView, EventDetailData, EventConfirm, EventMute, EventDetailView, EventsByMeasurement, EditMeasurements

app_name = 'events'

urlpatterns = [
    
    path(
        '',
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
        EventUpdateView.as_view(),
        name="event_edit"
    ),

    path(
        'get/',
        EventDetailData.as_view(),
        name="get"
    ),
    path(
        'confirm/',
        EventConfirm.as_view(),
        name="confirm"
    ),
    path(
        'mute/',
        EventMute.as_view(),
        name="mute"
    ),
    path(
        'detail/<int:pk>',
        EventDetailView.as_view(),
        name="detail"
    ),
    path(
        'measurement/<int:pk>',
        EventsByMeasurement.as_view(),
        name="event_by_measurement"
    ),
    path(
        'detail/<int:pk>/editMeasurements/',
        EditMeasurements.as_view(),
        name="edit_measurements"
    ),

]
