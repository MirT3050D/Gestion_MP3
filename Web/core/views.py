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
    import os
    from django.conf import settings
    from django.contrib import messages
    musics = FichierMP3.objects.all()
    count = musics.count()
    if request.method == 'POST':
        # 1. Supprimer chaque fichier physique associé aux objets en BDD
        for music in musics:
            if music.fichier:
                try:
                    music.fichier.delete(save=False)
                except Exception:
                    pass
        
        # 2. Nettoyer aussi le dossier physique media/mp3/ au cas où il resterait des fichiers orphelins
        media_mp3_dir = os.path.join(settings.MEDIA_ROOT, 'mp3')
        if os.path.exists(media_mp3_dir):
            for filename in os.listdir(media_mp3_dir):
                file_path = os.path.join(media_mp3_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

        # 3. Supprimer toutes les entrées en base de données
        musics.delete()
        
        messages.success(request, f"La bibliothèque a été réinitialisée avec succès ({count} fichier(s) supprimé(s)).")
        return redirect('music_list')
    return render(request, 'core/music_confirm_reset.html', {'count': count})

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
            # Recherche des clés génériques ou des tags ID3 (TCON = Genre, TPE1 = Artiste)
            g = m.metadonnees.get('genre') or m.metadonnees.get('TCON')
            a = m.metadonnees.get('artiste') or m.metadonnees.get('TPE1')
            if g: genres_set.add(str(g).strip())
            if a: artistes_set.add(str(a).strip())
            
    genres_list = sorted(list(genres_set))
    artistes_list = sorted(list(artistes_set))

    if request.method == 'POST':
        # Avec un <select multiple>, les valeurs arrivent sous forme de liste
        genres_list_post = request.POST.getlist('genre')
        artistes_list_post = request.POST.getlist('artiste')
        genres_exclus_list_post = request.POST.getlist('genre_exclu')
        artistes_exclus_list_post = request.POST.getlist('artiste_exclu')
        
        # Pour gérer aussi le cas où certaines valeurs contiennent des virgules (ex: tapé manuellement)
        genres_inclus = []
        for g in genres_list_post:
            genres_inclus.extend([x.strip().lower() for x in g.split(',') if x.strip()])
            
        artistes_inclus = []
        for a in artistes_list_post:
            artistes_inclus.extend([x.strip().lower() for x in a.split(',') if x.strip()])
            
        genres_exclus = []
        for g in genres_exclus_list_post:
            genres_exclus.extend([x.strip().lower() for x in g.split(',') if x.strip()])
            
        artistes_exclus = []
        for a in artistes_exclus_list_post:
            artistes_exclus.extend([x.strip().lower() for x in a.split(',') if x.strip()])
            
        duree_minutes = request.POST.get('duree_minutes')
        duree_secondes = request.POST.get('duree_secondes')
        
        target_seconds = None
        try:
            m_val = int(duree_minutes) if duree_minutes and duree_minutes.strip() else 0
            s_val = int(duree_secondes) if duree_secondes and duree_secondes.strip() else 0
            if m_val > 0 or s_val > 0:
                target_seconds = m_val * 60 + s_val
        except ValueError:
            target_seconds = None

        filtered_queryset = []
        priority_ids = []
        
        for music in all_musics:
            meta = music.metadonnees or {}
            music_genre = str(meta.get('genre') or meta.get('TCON') or '').lower()
            music_artiste = str(meta.get('artiste') or meta.get('TPE1') or '').lower()
            
            # 1. Vérification des exclusions
            is_excluded = False
            for g_ex in genres_exclus:
                if g_ex in music_genre and music_genre != '':
                    is_excluded = True
                    break
            if not is_excluded:
                for a_ex in artistes_exclus:
                    if a_ex in music_artiste and music_artiste != '':
                        is_excluded = True
                        break
            
            if is_excluded:
                continue # Ignore cette musique totalement
                
            # 2. Vérification des inclusions (pour la priorité)
            match_genre = False
            if not genres_inclus:
                match_genre = True
            else:
                for g_in in genres_inclus:
                    if g_in in music_genre:
                        match_genre = True
                        break
                        
            match_artiste = False
            if not artistes_inclus:
                match_artiste = True
            else:
                for a_in in artistes_inclus:
                    if a_in in music_artiste:
                        match_artiste = True
                        break
                        
            is_priority = match_genre and match_artiste
            
            filtered_queryset.append(music)
            if is_priority:
                priority_ids.append(music.id)

        queryset = filtered_queryset
        
        # Algorithme
        if target_seconds:
            selected_musics = generate_playlist_algorithm(queryset, target_seconds, priority_ids=priority_ids)
            total_duration = sum(m.duree_secondes for m in selected_musics if m.duree_secondes)
            
            if not selected_musics or abs(total_duration - target_seconds) > 59:
                logger.warning(f"Impossible de générer une playlist de {target_seconds}s (à 59s près). Le plus proche trouvé est de {total_duration}s.")
                messages.error(request, f"Aucune combinaison de musiques ne correspond à la durée de {target_seconds} secondes ({m_val} min et {s_val} sec) dans une marge de 59 secondes.")
                return redirect('playlist_generate')
            elif total_duration != target_seconds:
                diff = abs(total_duration - target_seconds)
                m_found = total_duration // 60
                s_found = total_duration % 60
                messages.info(request, f"💡 Playlist générée avec une durée totale de {m_found}m {s_found}s (à {diff}s de l'objectif de {m_val}m {s_val}s).")
        else:
            # Si pas de durée spécifiée, on ne prend que les musiques prioritaires (celles qui matchent les inclusions)
            selected_musics = [m for m in queryset if m.id in priority_ids]
            
            # Si aucune musique ne matche les inclusions (ou si pas d'inclusions), on prend tout ce qui n'est pas exclu
            if not selected_musics and not (genres_inclus or artistes_inclus):
                selected_musics = queryset
        
        # Sauvegarde temporaire dans la session
        request.session['temp_playlist'] = [m.id for m in selected_musics]
        return redirect('playlist_preview')

    return render(request, 'core/playlist_generate.html', {
        'genres': genres_list,
        'artistes': artistes_list
    })

@login_required
def playlist_preview(request):
    track_ids = request.session.get('temp_playlist', [])
    musics_dict = {m.id: m for m in FichierMP3.objects.filter(id__in=track_ids)}
    musics = [musics_dict[tid] for tid in track_ids if tid in musics_dict]
    
    available_musics = FichierMP3.objects.all().order_by('-date_upload')
    
    # Recalculer la durée totale
    total_seconds = sum(m.duree_secondes for m in musics if m.duree_secondes)
    total_minutes = total_seconds // 60
    total_remainder_seconds = total_seconds % 60
    
    return render(request, 'core/playlist_preview.html', {
        'musics': musics,
        'available_musics': available_musics,
        'total_seconds': total_seconds,
        'total_minutes': total_minutes,
        'total_remainder_seconds': total_remainder_seconds
    })

@login_required
def playlist_preview_remove(request, index):
    if request.method == 'POST':
        track_ids = request.session.get('temp_playlist', [])
        if 0 <= index < len(track_ids):
            track_ids.pop(index)
            request.session['temp_playlist'] = track_ids
            request.session.modified = True
            messages.success(request, "Titre retiré de votre sélection.")
    return redirect('playlist_preview')

@login_required
def playlist_preview_add(request, music_id):
    if request.method == 'POST':
        track_ids = request.session.get('temp_playlist', [])
        track_ids.append(music_id)
        request.session['temp_playlist'] = track_ids
        request.session.modified = True
        music = get_object_or_404(FichierMP3, pk=music_id)
        messages.success(request, f"Titre '{music.fichier.name}' ajouté à votre sélection.")
    return redirect('playlist_preview')


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
            
            return redirect('playlist_list')
    return redirect('playlist_preview')

@login_required
def playlist_list(request):
    playlists = Playlist.objects.filter(utilisateur=request.user).order_by('-date_creation')
    return render(request, 'core/playlist_list.html', {'playlists': playlists})

@login_required
def playlist_merge(request):
    user_playlists = Playlist.objects.filter(utilisateur=request.user).order_by('-date_creation')
    
    if request.method == 'POST':
        nom = request.POST.get('nom', 'Playlist Fusionnée').strip()
        if not nom:
            nom = 'Playlist Fusionnée'
            
        selected_ids = request.POST.getlist('playlists')
        if len(selected_ids) < 2:
            messages.error(request, "Veuillez sélectionner au moins deux playlists à fusionner.")
            return render(request, 'core/playlist_merge.html', {'playlists': user_playlists})
            
        # Création de la nouvelle playlist
        new_playlist = Playlist.objects.create(nom=nom, utilisateur=request.user)
        
        # Récupération de toutes les musiques des playlists sélectionnées, en ordre
        ordre_actuel = 0
        added_mp3_ids = set()
        
        for p_id in selected_ids:
            try:
                pl = Playlist.objects.get(id=p_id, utilisateur=request.user)
                tracks = PlaylistTrack.objects.filter(playlist=pl).order_by('ordre')
                for track in tracks:
                    if track.fichier_mp3_id not in added_mp3_ids:
                        PlaylistTrack.objects.create(
                            playlist=new_playlist,
                            fichier_mp3=track.fichier_mp3,
                            ordre=ordre_actuel
                        )
                        added_mp3_ids.add(track.fichier_mp3_id)
                        ordre_actuel += 1
            except Playlist.DoesNotExist:
                continue
                
        messages.success(request, f"La playlist '{nom}' a été créée en fusionnant {len(selected_ids)} playlists ({ordre_actuel} titres au total) !")
        return redirect('playlist_detail', pk=new_playlist.pk)
        
    return render(request, 'core/playlist_merge.html', {'playlists': user_playlists})

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
