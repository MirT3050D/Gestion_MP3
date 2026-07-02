from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import FichierMP3, Playlist, PlaylistTrack
from .forms import FichierMP3Form
from .utils import generate_playlist_algorithm
import json

# --- VUES CRUD (WEB APP - BACKOFFICE) ---

def staff_required(user):
    return user.is_active and user.is_staff

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_list(request):
    musics = FichierMP3.objects.all().order_by('-date_upload')
    return render(request, 'core/music_list.html', {'musics': musics})

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_detail(request, pk):
    music = get_object_or_404(FichierMP3, pk=pk)
    # Formater les métadonnées pour un affichage lisible
    meta_json = json.dumps(music.metadonnees, indent=4, ensure_ascii=False) if music.metadonnees else "{}"
    return render(request, 'core/music_detail.html', {'music': music, 'meta_json': meta_json})

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_upload(request):
    if request.method == 'POST':
        form = FichierMP3Form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('music_list')
    else:
        form = FichierMP3Form()
    return render(request, 'core/music_form.html', {'form': form, 'title': 'Uploader une Musique'})

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_edit(request, pk):
    music = get_object_or_404(FichierMP3, pk=pk)
    if request.method == 'POST':
        form = FichierMP3Form(request.POST, request.FILES, instance=music)
        if form.is_valid():
            form.save()
            return redirect('music_detail', pk=music.pk)
    else:
        form = FichierMP3Form(instance=music)
    return render(request, 'core/music_form.html', {'form': form, 'title': 'Modifier les métadonnées', 'music': music})

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_delete(request, pk):
    music = get_object_or_404(FichierMP3, pk=pk)
    if request.method == 'POST':
        music.fichier.delete() # Supprime le fichier physique
        music.delete() # Supprime l'entrée BDD
        return redirect('music_list')
    return render(request, 'core/music_confirm_delete.html', {'music': music})

@login_required
@user_passes_test(staff_required, login_url='playlist_list')
def music_reset(request):
    if request.method == 'POST':
        PlaylistTrack.objects.all().delete()
        Playlist.objects.all().delete()
        for music in FichierMP3.objects.all():
            try:
                music.fichier.delete()
            except:
                pass
            music.delete()
        messages.success(request, "La bibliotheque a ete reinitialisee.")
        return redirect('music_list')
    return redirect('music_list')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('playlist_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

import logging
from django.contrib import messages
logger = logging.getLogger(__name__)

@login_required
def playlist_generate(request):
    # Récupérer la liste des genres et artistes uniques pour l'autocomplétion
    all_musics = FichierMP3.objects.all()
    genres_set = set()
    artistes_set = set()
    
    for m in all_musics:
        if m.metadonnees:
            # Recherche des cles generiques ou des tags ID3 (TCON = Genre, TPE1 = Artiste)
            g = m.metadonnees.get('genre') or m.metadonnees.get('TCON')
            a = m.metadonnees.get('artiste') or m.metadonnees.get('artiste_album') or m.metadonnees.get('TPE1') or m.metadonnees.get('TPE2')
            if g: genres_set.add(str(g).strip())
            if a: artistes_set.add(str(a).strip())
            
    genres_list = sorted(list(genres_set))
    artistes_list = sorted(list(artistes_set))

    if request.method == 'POST':
        genre = request.POST.get('genre')
        artiste = request.POST.get('artiste')
        genre_exclu = request.POST.get('genre_exclu')
        artiste_exclu = request.POST.get('artiste_exclu')
        duree_minutes = request.POST.get('duree_minutes')
        duree_secondes = request.POST.get('duree_secondes')
        
        # Sauvegarder les criteres dans la session
        request.session['playlist_criteria'] = {
            'genre': genre,
            'artiste': artiste,
            'genre_exclu': genre_exclu,
            'artiste_exclu': artiste_exclu,
            'duree_minutes': duree_minutes,
            'duree_secondes': duree_secondes,
        }
        
        target_seconds = None
        try:
            m_val = int(duree_minutes) if duree_minutes and duree_minutes.strip() else 0
            s_val = int(duree_secondes) if duree_secondes and duree_secondes.strip() else 0
            if m_val > 0 or s_val > 0:
                target_seconds = m_val * 60 + s_val
        except ValueError:
            target_seconds = None

        queryset = all_musics
        
        # Filtres d'inclusion et d'exclusion
        if genre or artiste or genre_exclu or artiste_exclu:
            filtered_queryset = []
            for music in queryset:
                meta = music.metadonnees or {}
                music_genre = str(meta.get('genre') or meta.get('TCON') or '').lower()
                music_artiste = str(meta.get('artiste') or meta.get('artiste_album') or meta.get('TPE1') or meta.get('TPE2') or '').lower()
                
                match = True
                
                # Inclusions
                if genre and genre.lower() not in music_genre:
                    match = False
                if artiste and artiste.lower() not in music_artiste:
                    match = False
                    
                # Exclusions
                if genre_exclu and genre_exclu.lower() in music_genre and music_genre != '':
                    match = False
                if artiste_exclu and artiste_exclu.lower() in music_artiste and music_artiste != '':
                    match = False
                
                if match:
                    filtered_queryset.append(music)
            queryset = filtered_queryset
        else:
            queryset = list(queryset) # Convertir en liste si pas de filtre
        
        # Algorithme
        if target_seconds:
            selected_musics = generate_playlist_algorithm(queryset, target_seconds)
            if not selected_musics:
                messages.error(request, "Aucune combinaison de musiques disponible pour cette duree.")
                return redirect('playlist_generate')
        else:
            # Si pas de durée spécifiée, on prend tout ce qui matche (tous les sons)
            selected_musics = queryset
        
        # Sauvegarde temporaire dans la session
        request.session['temp_playlist'] = [m.id for m in selected_musics]
        return redirect('playlist_preview')

    criteria = request.session.get('playlist_criteria', {})
    return render(request, 'core/playlist_generate.html', {
        'genres': genres_list,
        'artistes': artistes_list,
        'criteria': criteria
    })

@login_required
def playlist_preview(request):
    track_ids = request.session.get('temp_playlist', [])
    musics = FichierMP3.objects.filter(id__in=track_ids)
    
    # Recalculer la durée totale
    total_seconds = sum(m.duree_secondes for m in musics if m.duree_secondes)
    total_minutes = total_seconds // 60
    total_remainder_seconds = total_seconds % 60
    
    return render(request, 'core/playlist_preview.html', {
        'musics': musics,
        'total_seconds': total_seconds,
        'total_minutes': total_minutes,
        'total_remainder_seconds': total_remainder_seconds
    })

@login_required
def playlist_save(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', 'Nouvelle Playlist')
        track_ids = request.session.get('temp_playlist', [])
        
        if track_ids:
            playlist = Playlist.objects.create(nom=nom, utilisateur=request.user)
            for index, m_id in enumerate(track_ids):
                PlaylistTrack.objects.create(
                    playlist=playlist,
                    fichier_mp3_id=m_id,
                    ordre=index
                )
            # Nettoyer la session
            if 'temp_playlist' in request.session:
                del request.session['temp_playlist']
            if 'playlist_criteria' in request.session:
                del request.session['playlist_criteria']
            
            return redirect('playlist_list')
    return redirect('playlist_preview')

@login_required
def playlist_cancel(request):
    if 'temp_playlist' in request.session:
        del request.session['temp_playlist']
    if 'playlist_criteria' in request.session:
        del request.session['playlist_criteria']
    return redirect('playlist_generate')

@login_required
def playlist_list(request):
    playlists = Playlist.objects.filter(utilisateur=request.user).order_by('-date_creation')
    return render(request, 'core/playlist_list.html', {'playlists': playlists})

@login_required
def playlist_detail(request, pk):
    playlist = get_object_or_404(Playlist, pk=pk, utilisateur=request.user)
    tracks = PlaylistTrack.objects.filter(playlist=playlist).select_related('fichier_mp3')
    
    total_seconds = sum(t.fichier_mp3.duree_secondes for t in tracks if t.fichier_mp3.duree_secondes)
    total_minutes = total_seconds // 60
    total_remainder_seconds = total_seconds % 60
    
    return render(request, 'core/playlist_detail.html', {
        'playlist': playlist,
        'tracks': tracks,
        'total_minutes': total_minutes,
        'total_remainder_seconds': total_remainder_seconds
    })

@login_required
def playlist_export_zip(request, pk):
    import zipfile
    import io
    from django.http import HttpResponse
    
    playlist = get_object_or_404(Playlist, pk=pk, utilisateur=request.user)
    tracks = PlaylistTrack.objects.filter(playlist=playlist).select_related('fichier_mp3')
    
    # Créer le ZIP en mémoire
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, track in enumerate(tracks):
            file_obj = track.fichier_mp3.fichier
            try:
                # Ajout d'un préfixe avec l'ordre pour garder le bon ordre de lecture
                file_name = f"{idx + 1:02d} - {file_obj.name.split('/')[-1]}"
                zip_file.writestr(file_name, file_obj.read())
            except Exception as e:
                # En cas de fichier manquant sur le disque
                pass

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Playlist_{playlist.nom}.zip"'
    return response

@login_required
def playlist_merge(request):
    if request.method == 'POST':
        nom_fusion = request.POST.get('nom_fusion', '').strip()
        playlist_ids = request.POST.getlist('playlist_ids')
        
        if not nom_fusion:
            messages.error(request, "Veuillez spécifier un nom pour la playlist fusionnée.")
            return redirect('playlist_list')
            
        if not playlist_ids:
            messages.error(request, "Veuillez sélectionner au moins une playlist à fusionner.")
            return redirect('playlist_list')
            
        playlists = Playlist.objects.filter(id__in=playlist_ids, utilisateur=request.user)
        if not playlists.exists():
            messages.error(request, "Aucune playlist valide sélectionnée.")
            return redirect('playlist_list')
            
        nouvelle_playlist = Playlist.objects.create(nom=nom_fusion, utilisateur=request.user)
        
        added_track_ids = set()
        ordre_courant = 0
        for pl in playlists:
            playlist_tracks = PlaylistTrack.objects.filter(playlist=pl).select_related('fichier_mp3').order_by('ordre')
            for pt in playlist_tracks:
                if pt.fichier_mp3_id not in added_track_ids:
                    PlaylistTrack.objects.create(
                        playlist=nouvelle_playlist,
                        fichier_mp3=pt.fichier_mp3,
                        ordre=ordre_courant
                    )
                    ordre_courant += 1
                    added_track_ids.add(pt.fichier_mp3_id)
                
        messages.success(request, f"La playlist '{nom_fusion}' a été créée avec succès en fusionnant {playlists.count()} playlists.")
        return redirect('playlist_list')
        
    return redirect('playlist_list')

@login_required
def playlist_delete_all(request):
    if request.method == 'POST':
        playlists = Playlist.objects.filter(utilisateur=request.user)
        count = playlists.count()
        playlists.delete()
        messages.success(request, f"Toutes vos playlists ({count}) ont été supprimées.")
    return redirect('playlist_list')

