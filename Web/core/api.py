from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import FichierMP3
import json

@csrf_exempt
def upload_mp3(request):
    if request.method == 'POST':
        fichier_audio = request.FILES.get('fichier_audio')
        duree_secondes = request.POST.get('duree_secondes')
        metadonnees_completes = request.POST.get('metadonnees_completes')

        if not fichier_audio:
            return JsonResponse({'erreur': 'Aucun fichier audio fourni'}, status=400)

        # Parse des métadonnées envoyées en JSON texte
        meta = {}
        if metadonnees_completes:
            try:
                meta = json.loads(metadonnees_completes)
            except json.JSONDecodeError:
                pass

        # Sauvegarde en base de données
        nouveau_mp3 = FichierMP3.objects.create(
            fichier=fichier_audio,
            duree_secondes=int(duree_secondes) if duree_secondes else None,
            metadonnees=meta
        )

        return JsonResponse({'message': 'Fichier uploadé avec succès', 'id': nouveau_mp3.id}, status=201)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@login_required
def replace_track_api(request, track_id):
    """
    API AJAX pour trouver des alternatives de même durée et remplacer.
    Si method=GET, retourne les alternatives.
    Si method=POST avec new_track_id, met à jour la session.
    """
    try:
        current_track = FichierMP3.objects.get(id=track_id)
    except FichierMP3.DoesNotExist:
        return JsonResponse({'error': 'Track not found'}, status=404)

    if request.method == 'GET':
        # Chercher des alternatives avec EXACTEMENT la même durée (et exclure celle-ci)
        duree = current_track.duree_secondes
        if not duree:
            return JsonResponse({'alternatives': []})
            
        alternatives = FichierMP3.objects.filter(duree_secondes=duree).exclude(id=track_id)[:10]
        data = []
        for alt in alternatives:
            titre = alt.metadonnees.get('titre') or alt.metadonnees.get('TIT2') if alt.metadonnees else None
            artiste = alt.metadonnees.get('artiste') or alt.metadonnees.get('TPE1') if alt.metadonnees else None
            data.append({
                'id': alt.id,
                'titre': titre or alt.fichier.name,
                'artiste': artiste or 'Artiste Inconnu'
            })
        return JsonResponse({'alternatives': data})
        
    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
            new_id = int(body.get('new_track_id'))
        except:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
            
        # Mettre à jour la session
        temp_playlist = request.session.get('temp_playlist', [])
        if track_id in temp_playlist:
            idx = temp_playlist.index(track_id)
            temp_playlist[idx] = new_id
            request.session['temp_playlist'] = temp_playlist
            request.session.modified = True
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Track not in playlist'}, status=400)

@login_required
def remove_track_api(request, track_id):
    if request.method == 'POST':
        temp_playlist = request.session.get('temp_playlist', [])
        if track_id in temp_playlist:
            temp_playlist.remove(track_id)
            request.session['temp_playlist'] = temp_playlist
            request.session.modified = True
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Track not in playlist'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def list_available_tracks_api(request):
    temp_playlist = request.session.get('temp_playlist', [])
    search_query = request.GET.get('q', '').strip()
    
    queryset = FichierMP3.objects.exclude(id__in=temp_playlist)
    
    if search_query:
        filtered_tracks = []
        for t in queryset:
            titre = (t.metadonnees.get('titre') or t.metadonnees.get('TIT2') or '').lower() if t.metadonnees else ''
            artiste = (t.metadonnees.get('artiste') or t.metadonnees.get('artiste_album') or t.metadonnees.get('TPE1') or t.metadonnees.get('TPE2') or '').lower() if t.metadonnees else ''
            filename = t.fichier.name.lower()
            if search_query.lower() in titre or search_query.lower() in artiste or search_query.lower() in filename:
                filtered_tracks.append(t)
                if len(filtered_tracks) >= 30:
                    break
        tracks = filtered_tracks
    else:
        tracks = queryset[:30]

    data = []
    for track in tracks:
        titre = track.metadonnees.get('titre') or track.metadonnees.get('TIT2') if track.metadonnees else None
        artiste = track.metadonnees.get('artiste') or track.metadonnees.get('artiste_album') or track.metadonnees.get('TPE1') or track.metadonnees.get('TPE2') if track.metadonnees else None
        data.append({
            'id': track.id,
            'titre': titre or track.fichier.name.split('/')[-1],
            'artiste': artiste or 'Artiste Inconnu',
            'duree_secondes': track.duree_secondes or 0
        })
    return JsonResponse({'tracks': data})

@login_required
def add_track_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            track_id = int(body.get('track_id'))
        except:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
            
        temp_playlist = request.session.get('temp_playlist', [])
        if track_id not in temp_playlist:
            temp_playlist.append(track_id)
            request.session['temp_playlist'] = temp_playlist
            request.session.modified = True
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Track already in playlist'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

