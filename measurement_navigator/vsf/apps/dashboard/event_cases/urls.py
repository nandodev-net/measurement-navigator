from django.urls import path

from . import views

app_name = "event_cases"

urlpatterns = [
    path("", views.CasesListView.as_view(), name="list_cases"),
    path("create/", views.CaseCreateView.as_view(), name="create_case"),
    path("add/", views.CaseCreateModalView.as_view(), name="add_case"),
    path("data/", views.CasesData.as_view(), name="data"),
    path("detail/", views.CaseDetailData.as_view(), name="detail"),
    path("event_remove/", views.EventsUnlinking.as_view(), name="event_remove"),
    path("case_delete/", views.CaseDeleteView.as_view(), name="case_delete"),
    path("detail/<int:pk>", views.CaseDetailView.as_view(), name="detail_page"),
    path("detail/<int:pk>/editEvents/", views.EditEvents.as_view(), name="edit_events"),
    path("publish/", views.CasePublish.as_view(), name="publish"),
    path("goAutomatic/", views.CaseChangeToAutomatic.as_view(), name="goAutomatic"),
    path("goActive/", views.CaseChangeToActive.as_view(), name="goActive"),
    path("separate_case/", views.CaseSeparation.as_view(), name="separate_case"),
]
