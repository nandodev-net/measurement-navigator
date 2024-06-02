from django.urls import path

from . import views

app_name = "cases_api"

urlpatterns = [
    path("", views.ListCases.as_view(), name="list_cases"),
    path("quantity", views.BlockedCasesNumber.as_view(), name="quantity"),
    path("categories", views.ListCategories.as_view(), name="list_categories"),
    path(
        "category/<int:cat_id>",
        views.ListCasesByCategory.as_view(),
        name="list_cases_by_category",
    ),
    path("<int:id>", views.CaseDetail.as_view(), name="case_detail"),
    path("num-active", views.CaseActiveNumber.as_view(), name="case_active_num"),
    path(
        "case-by-date/<str:start_date>/<str:end_date>",
        views.ListCasesByDate.as_view(),
        name="case_by_date",
    ),
]
