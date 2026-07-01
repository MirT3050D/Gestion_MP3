from typing import List
from .models import FichierMP3

def generate_playlist_algorithm(queryset, target_seconds: int, priority_ids: List[int] = None) -> List[FichierMP3]:
    """
    Algorithme de Subset Sum (Sac à dos) pour trouver la combinaison de musiques
    dont la somme des durées se rapproche le plus possible de `target_seconds`.
    Priorise les musiques dont les IDs sont dans `priority_ids`.
    """
    if priority_ids is None:
        priority_ids = []
    
    priority_set = set(priority_ids)
    
    # Filtrer les musiques qui n'ont pas de durée ou dont la durée dépasse déjà la cible
    musics = [m for m in queryset if m.duree_secondes and m.duree_secondes <= target_seconds]
    
    if not musics:
        return []

    # dp[w] = (duree_prioritaire, [liste_ids])
    dp = {0: (0, [])}
    
    for music in musics:
        duration = music.duree_secondes
        is_priority = music.id in priority_set
        prio_val = duration if is_priority else 0
        
        # On itère à l'envers pour ne pas réutiliser la même musique plusieurs fois
        current_keys = list(dp.keys())
        for w in current_keys:
            new_w = w + duration
            if new_w <= target_seconds:
                new_prio_duration = dp[w][0] + prio_val
                new_combination = dp[w][1] + [music.id]
                
                # Si on n'a pas encore atteint ce poids, on l'ajoute
                if new_w not in dp:
                    dp[new_w] = (new_prio_duration, new_combination)
                else:
                    # Si on l'a atteint, on regarde si cette nouvelle combinaison offre une meilleure durée prioritaire
                    if new_prio_duration > dp[new_w][0]:
                        dp[new_w] = (new_prio_duration, new_combination)
                    
    # Trouver la clé la plus proche de target_seconds
    best_w = max(dp.keys())
    best_combination_ids = dp[best_w][1]
    
    # Récupérer les objets depuis la base (en gardant l'ordre n'est pas strictement nécessaire ici, 
    # mais on renvoie les objets)
    result = []
    for m_id in best_combination_ids:
        for m in musics:
            if m.id == m_id:
                result.append(m)
                break
                
    return result
