from django.conf.urls import include
from django.urls import path
from .views import EventsList, EventsData, EventUpdateView, EventDetailData, EventConfirm, EventDetailView

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
        'detail/<int:pk>',
        EventDetailView.as_view(),
        name="detail"
    ),


]
