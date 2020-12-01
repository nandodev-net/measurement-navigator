from django.conf.urls import include
from django.urls import path
from .views import ListCases, ListCategories, NewCategory

app_name = 'cases'

urlpatterns = [
    path(
        'list_cases/',                           
        ListCases.as_view(),          
        name="list_cases"
        ),

    path(
        'categories/',                
        ListCategories.as_view(),     
        name="list_categories"
        ),

    path(
        'categories/new_category',   
        NewCategory.as_view(),        
        name="new_category"
        ),
]