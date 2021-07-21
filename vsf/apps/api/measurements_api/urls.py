from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "measurements_api"

urlpatterns = [
    path(
        '', 
        views.ListMeasurements.as_view(), 
        name='list_measurements'
        ),

    path(
        'full/<str:id>', 
        views.MeasurementDetail.as_view(), 
        name='measurement_detail'),
]