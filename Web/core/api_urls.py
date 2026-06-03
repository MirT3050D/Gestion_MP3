from django.urls import path
from . import api

urlpatterns = [
    path('upload-mp3/', api.upload_mp3, name='api_upload_mp3'),
    path('replace/<int:track_id>/', api.replace_track_api, name='replace_track_api'),
]
