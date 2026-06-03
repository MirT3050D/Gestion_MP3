"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Rediriger /admin/ directement vers notre backoffice personnalisé
    path('admin/', RedirectView.as_view(pattern_name='music_list', permanent=False)),
    # Si on a vraiment besoin de l'admin Django brut, on le met sur une autre URL
    path('django-admin/', admin.site.urls),
    path('api/', include('core.api_urls')),
    path('', include('core.urls')),
    path('', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
