"""
URL configuration for alpha project.
"""
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path

from django.urls import include, path
from sqms_apps.admin import sqms_site
from sqms_apps.views_erros import custom_404  # Import the custom 404 view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sqms-admin/', sqms_site.urls),  # Admin untuk SQMS Apps
    path('sqms_apps/', include('sqms_apps.urls')),  # Url SQMS Apps
    path('geos_py/', include('geos_py.urls')),  # GeosPy Apps
    path('api_apps/', include('api_apps.urls')),  # Api apps

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
handler404 = custom_404  # Set the custom 404 handler