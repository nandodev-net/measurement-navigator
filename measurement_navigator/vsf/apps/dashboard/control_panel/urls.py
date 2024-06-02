from django.urls import path

from .views import ControlPanel, get_process_state

app_name = "control_panel"

urlpatterns = [
    path("controls", ControlPanel.as_view(), name="controls"),
    path("process_state", get_process_state, name="process_state"),
]
