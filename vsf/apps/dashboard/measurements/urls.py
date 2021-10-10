from django.conf.urls import include
from django.urls import path
from .views import ListMeasurementsTemplate, MeasurementDetailView, ListMeasurementsBackEnd, MeasurementCounter, TorDetailView

app_name = 'measurements'

urlpatterns = [
    
    path(
        'measurements_data/',
        ListMeasurementsBackEnd.as_view(),
        name="list_measurements_data"
    ),

    path(
        'list_measurements/',                    
        ListMeasurementsTemplate.as_view(),  
        name="list_measurements"
    ),

    path(
        'detail/<uuid:pk>', 
        MeasurementDetailView.as_view(),
        name="detail"
    ),

    path(
        'counter/',
        MeasurementCounter.as_view(),
        name="counter"
    ),

    path(
        'tor_detail/<uuid:pk>',
        TorDetailView.as_view(),
        name='tor_detail'
    )

]