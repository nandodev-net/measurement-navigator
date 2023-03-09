from .                      import views
from django.contrib         import admin
from django.urls            import include, path, re_path

app_name = "fp_tables_api"

urlpatterns = [
    path(
        'ingest_fp/since/<str:since>/until/<str:until>', 
        views.FastPathIngestView.as_view(), 
        name='ingest_fastpath')
]