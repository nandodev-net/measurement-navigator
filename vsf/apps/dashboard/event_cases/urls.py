from django.conf.urls import include
from django.urls import path
from . import views
app_name = 'event_cases'

urlpatterns = [
    path(
        '',
        views.CasesListView.as_view(),
        name="list_cases"
    ),  

    path(
        'create/',
        views.CaseCreateView.as_view(),
        name="create_case"
    ),  

    path(
        'add/',
        views.CaseCreateModalView.as_view(),
        name="add_case"
    ),  

    path(
        'data/',
        views.CasesData.as_view(),
        name="data"
    ),

    path(
        'detail/',
        views.CaseDetailData.as_view(),
        name="detail"
    ),

    path(
        'event_remove/',
        views.EventsUnlinking.as_view(),
        name="event_remove"
    ),

    path(
        'case_delete/',
        views.CaseDeleteView.as_view(),
        name="case_delete"
    ),

    path(
        'detail/<int:pk>',
        views.CaseDetailView.as_view(),
        name="detail_page"
    ),
    
]