from django.conf.urls import include
from django.urls import path
from .views import ControlPanel

app_name = 'control_panel'

urlpatterns = [

    path(
        'controls',               
        ControlPanel.as_view(),   
        name="controls"
    ),
    

]