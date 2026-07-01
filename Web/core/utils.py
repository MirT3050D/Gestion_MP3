from typing import List
from .models import FichierMP3

def generate_playlist_algorithm(queryset, target_seconds: int) -> List[FichierMP3]:
    # Filtrer les musiques de duree valide
    musics = [m for m in queryset if m.duree_secondes and m.duree_secondes <= target_seconds + 59]
    
    if not musics:
        return []

    # dp[w] associe la duree w aux IDs de musiques
    dp = {0: []}
    
    for music in musics:
        duration = music.duree_secondes
        current_keys = list(dp.keys())
        for w in current_keys:
            new_w = w + duration
            if new_w <= target_seconds + 59:
                if new_w not in dp:
                    dp[new_w] = dp[w] + [music.id]
                    
    # Trouver la duree la plus proche en elargissant petit a petit
    best_w = None
    for d in range(target_seconds + 1):
        w_down = target_seconds - d
        w_up = target_seconds + d
        if w_down in dp:
            best_w = w_down
            break
        if w_up <= target_seconds + 59 and w_up in dp:
            best_w = w_up
            break
            
    best_combination_ids = dp[best_w] if best_w is not None else []
    
    result = []
    for m_id in best_combination_ids:
        for m in musics:
            if m.id == m_id:
                result.append(m)
                break
                
    return result
