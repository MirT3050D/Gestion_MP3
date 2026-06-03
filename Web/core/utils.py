from typing import List
from .models import FichierMP3

def generate_playlist_algorithm(queryset, target_seconds: int) -> List[FichierMP3]:
    """
    Algorithme de Subset Sum (Sac à dos) pour trouver la combinaison de musiques
    dont la somme des durées se rapproche le plus possible de `target_seconds`.
    """
    # Filtrer les musiques qui n'ont pas de durée ou dont la durée dépasse déjà la cible
    musics = [m for m in queryset if m.duree_secondes and m.duree_secondes <= target_seconds]
    
    if not musics:
        return []

    # dp[w] contiendra la liste des IDs des musiques pour atteindre la durée w
    dp = {0: []}
    
    for music in musics:
        duration = music.duree_secondes
        # On itère à l'envers pour ne pas réutiliser la même musique plusieurs fois
        current_keys = list(dp.keys())
        for w in current_keys:
            new_w = w + duration
            if new_w <= target_seconds:
                # Si on n'a pas encore atteint ce poids, ou si on veut juste le marquer
                if new_w not in dp:
                    dp[new_w] = dp[w] + [music.id]
                    
    # Trouver la clé la plus proche de target_seconds
    best_w = max(dp.keys())
    best_combination_ids = dp[best_w]
    
    # Récupérer les objets depuis la base (en gardant l'ordre n'est pas strictement nécessaire ici, 
    # mais on renvoie les objets)
    result = []
    for m_id in best_combination_ids:
        for m in musics:
            if m.id == m_id:
                result.append(m)
                break
                
    return result
