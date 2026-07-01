from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', RedirectView.as_view(pattern_name='playlist_list', permanent=False), name='home'),
    
    # --- Frontoffice (Playlists) ---
    path('playlist/generate/', views.playlist_generate, name='playlist_generate'),
    path('playlist/preview/', views.playlist_preview, name='playlist_preview'),
    path('playlist/preview/remove/<int:index>/', views.playlist_preview_remove, name='playlist_preview_remove'),
    path('playlist/preview/add/<int:music_id>/', views.playlist_preview_add, name='playlist_preview_add'),
    path('playlist/save/', views.playlist_save, name='playlist_save'),
    path('playlist/merge/', views.playlist_merge, name='playlist_merge'),
    path('playlists/', views.playlist_list, name='playlist_list'),
    path('playlists/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlists/<int:pk>/export/', views.playlist_export_zip, name='playlist_export_zip'),
    
    # --- Backoffice (Gestion des MP3) ---
    path('backoffice/', views.music_list, name='music_list'),
    path('backoffice/upload/', views.music_upload, name='music_upload'),
    path('backoffice/reset/', views.music_reset, name='music_reset'),
    path('backoffice/<int:pk>/', views.music_detail, name='music_detail'),
    path('backoffice/<int:pk>/edit/', views.music_edit, name='music_edit'),
    path('backoffice/<int:pk>/delete/', views.music_delete, name='music_delete'),
]
