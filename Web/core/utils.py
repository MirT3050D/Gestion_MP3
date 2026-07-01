from typing import List
from .models import FichierMP3

def generate_playlist_algorithm(queryset, target_seconds: int, priority_ids: List[int] = None) -> List[FichierMP3]:
    if priority_ids is None:
        priority_ids = []
    priority_set = set(priority_ids)

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
                new_combo = dp[w] + [music.id]
                if new_w not in dp:
                    dp[new_w] = new_combo
                else:
                    # En cas d'égalité de durée, on privilégie la combinaison contenant le plus de morceaux prioritaires
                    old_count = sum(1 for cid in dp[new_w] if cid in priority_set)
                    new_count = sum(1 for cid in new_combo if cid in priority_set)
                    if new_count > old_count:
                        dp[new_w] = new_combo
                    
    # Priorité 1 : chercher une durée supérieure ou égale (pour combler et dépasser légèrement la cible)
    best_w = None
    for d in range(60): # de target_seconds à target_seconds + 59
        w_up = target_seconds + d
        if w_up in dp:
            best_w = w_up
            break
            
    # Priorité 2 : si aucune durée supérieure n'est trouvée, on cherche une durée inférieure
    if best_w is None:
        for d in range(1, 60): # de target_seconds - 1 à target_seconds - 59
            w_down = target_seconds - d
            if w_down >= 0 and w_down in dp:
                best_w = w_down
                break
            
    best_combination_ids = dp[best_w] if best_w is not None else []
    
    result = []
    for m_id in best_combination_ids:
        for m in musics:
            if m.id == m_id:
                result.append(m)
                break
                
    return result
