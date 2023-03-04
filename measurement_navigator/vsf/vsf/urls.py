"""vsf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# Django imports
import debug_toolbar
from django.contrib     import admin
from django.conf        import settings
from django.urls        import include, path, re_path
from django.conf.urls.static import static

# Third party imports
from rest_framework                 import routers
from drf_yasg                       import openapi
from rest_framework                 import permissions
from drf_yasg.views                 import get_schema_view
from rest_framework.documentation   import include_docs_urls

# Local imports
from .views import redirect_to_dashboard

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('dashboard/',      include('apps.dashboard.urls',         namespace = 'dashboard')),
    path('sites/',          include('apps.main.sites.urls',        namespace = 'sites')),
    path('api/',            include('apps.api.urls',               namespace = 'api')),
    path('measurements/',   include('apps.main.measurements.urls', namespace = 'measurements')),
    path('admin/',          admin.site.urls),
    path('', redirect_to_dashboard),
    path('prometheus/', include('django_prometheus.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

