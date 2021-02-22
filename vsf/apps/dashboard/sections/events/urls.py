from django.conf.urls import include
from django.urls import path
from .views import EventsList, EventsData

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
    )    

]
