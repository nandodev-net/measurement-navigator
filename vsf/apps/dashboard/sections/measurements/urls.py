from django.conf.urls import include
from django.urls import path
from .views import ListMeasurementsTemplate, ListMeasurementsBackEnd, MeasurementDetails

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
        'measurement',
        MeasurementDetails.as_view(),
        name="details"
    )

]