from django.conf.urls import include
from django.urls import path
from . import views

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
        views.EventUpdateView.as_view(),
        name="event_edit"
    )   

]
