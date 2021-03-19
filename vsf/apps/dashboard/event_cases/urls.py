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
    
]