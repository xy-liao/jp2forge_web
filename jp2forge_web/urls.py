from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('converter/', include('converter.urls')),
    path('dashboard/', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
