from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "public_stats_api"

urlpatterns = [
    path(
        'general', 
        views.GetGeneralPublicStats.as_view(), 
        name='general_public_stats'
        ),

    path(
        'asn/<str:id>', 
        views.GetAsnPublicStats.as_view(), 
        name='asn_public_stats'),

    path(
        'category/<str:id>', 
        views.GetCategoryPublicStats.as_view(), 
        name='category_public_stats'),
]