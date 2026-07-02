from django.urls import path
from . import api

urlpatterns = [
    path('upload-mp3/', api.upload_mp3, name='api_upload_mp3'),
    path('replace/<int:track_id>/', api.replace_track_api, name='replace_track_api'),
    path('remove-track/<int:track_id>/', api.remove_track_api, name='remove_track_api'),
    path('available-tracks/', api.list_available_tracks_api, name='list_available_tracks_api'),
    path('add-track/', api.add_track_api, name='add_track_api'),
]
