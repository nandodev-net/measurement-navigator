from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "events_api"

urlpatterns = [
    path(
        '', 
        views.ListEvents.as_view(), 
        name='list_events'
        ),

    path(
        'full/<int:id>', 
        views.EventDetail.as_view(), 
        name='event_detail_full'),

    path(
        'partial/<int:id>', 
        views.EventPartialDetail.as_view(), 
        name='event_detail'),

    path(
        '<int:id>/start/<str:start_date>/end/<str:end_date>', 
        views.EventDateDetail.as_view(), 
        name='event_detail_date'),

    path(
        'asn/<str:asn>', 
        views.ListEventsByASN.as_view(), 
        name='list_event_by_asn'),

    path(
        'type/<str:type>', 
        views.ListEventsByType.as_view(), 
        name='list_event_by_type'),

    path(
        'num-active', 
        views.EventActiveNumber.as_view(), 
        name='event_active_num'),

    path(
        'num-asn', 
        views.EventAsnNumber.as_view(), 
        name='event_asn_num'),

    path(
        'num-type', 
        views.EventTypeNumber.as_view(), 
        name='event_type_num'),
]