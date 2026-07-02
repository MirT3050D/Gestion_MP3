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
                    
    # Trouver la duree la plus proche en priorisant la valeur exacte ou au-dessus (+59s max), 
    # puis en retombant en dessous en dernier recours.
    best_w = None
    
    # 1. Recherche entre target_seconds et target_seconds + 60 (exclut target_seconds + 60)
    for w in range(target_seconds, target_seconds + 60):
        if w in dp:
            best_w = w
            break
            
    # 2. Si aucune combinaison ne convient, recherche en dessous de target_seconds
    if best_w is None:
        for w in range(target_seconds - 1, -1, -1):
            if w in dp:
                best_w = w
                break
            
    best_combination_ids = dp[best_w] if best_w is not None else []
    
    result = []
    for m_id in best_combination_ids:
        for m in musics:
            if m.id == m_id:
                result.append(m)
                break
                
    return result
