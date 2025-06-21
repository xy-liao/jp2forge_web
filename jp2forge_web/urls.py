"""JP2Forge Web URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .views import health_check
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('converter/', include('converter.urls')),
    path('accounts/', include('accounts.urls')),
]

# Always serve static and media files through Django when in Docker
# This is not recommended for production but works for development and demo environments
if settings.DEBUG or os.environ.get('DOCKER_ENVIRONMENT') == 'true':
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
