from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "cases_api"

urlpatterns = [
    path(
        '', 
        views.ListCases.as_view(), 
        name='list_cases'
        ),

    path(
        '<int:id>', 
        views.CaseDetail.as_view(), 
        name='case_detail'),

    path(
        'num-active', 
        views.CaseActiveNumber.as_view(), 
        name='case_active_num'),

]