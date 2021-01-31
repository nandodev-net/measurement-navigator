from django.conf.urls import include
from django.urls import path
from .views import ListMeasurementsTemplate, MeasurementDetails, MeasurementDetailView

app_name = 'measurements'

urlpatterns = [

    path(
        'list_measurements/',                    
        ListMeasurementsTemplate.as_view(),  
        name="list_measurements"
    ),

    path(
        'measurement',
        MeasurementDetails.as_view(),
        name="details"
    ),

    path(
        'detail/<uuid:pk>', 
        MeasurementDetailView.as_view(),
        name="detail"
    )

]