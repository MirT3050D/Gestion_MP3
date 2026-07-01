import pika
import json
import os
import requests
import datetime
import logging

from config import (
    LOG_FILE, URL_API_DJANGO, BLACKLIST_FILE, AETEBLACKLIST_TXT,
    DUREE_MAX_FILE, QUEUE_METADATA, QUEUE_A_SUPPRIMER
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 3 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def lire_duree_max():
    """Lit la durée maximale autorisée en secondes depuis le fichier Desktop."""
    if os.path.exists(DUREE_MAX_FILE):
        try:
            with open(DUREE_MAX_FILE, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return int(val)
        except Exception as e:
            logging.error(f" ❌ Erreur lecture duree_max.txt : {e}")
    return None

def est_blackliste(metadonnees):
    """Vérifie si les métadonnées correspondent à une règle dans blacklist.json."""
    if not os.path.exists(BLACKLIST_FILE):
        return False
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        regles = []
        if isinstance(data, list):
            regles = data
        elif isinstance(data, dict):
            for a in data.get("artistes", []):
                if isinstance(a, str) and a.strip():
                    regles.append({"artiste": a.strip()})
            for g in data.get("genres", []):
                if isinstance(g, str) and g.strip():
                    regles.append({"genre": g.strip()})
            for c in data.get("combinaisons", []) + data.get("regles", []):
                if isinstance(c, dict) and c:
                    regles.append(c)
        
        for regle in regles:
            if not isinstance(regle, dict) or not regle:
                continue
            
            match_complet = True
            criteres_actifs = 0
            for cle, valeur_attendue in regle.items():
                if valeur_attendue is None:
                    continue
                val_attendue_str = str(valeur_attendue).strip().lower()
                if not val_attendue_str:
                    continue
                
                criteres_actifs += 1
                val_piste = metadonnees.get(cle)
                if val_piste is None or str(val_piste).strip().lower() != val_attendue_str:
                    match_complet = False
                    break
            
            if criteres_actifs > 0 and match_complet:
                return True
    except Exception as e:
        logging.error(f" ❌ Erreur lecture blacklist : {e}")
    return False

def enregistrer_blackliste_txt(chemin, metadonnees):
    """Enregistre un fichier blacklisté dans aeteblacklist.txt."""
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        nom_fichier = os.path.basename(chemin)
        details_meta = ", ".join(f"'{k}': '{v}'" for k, v in metadonnees.items() if v)
        log_line = f"{now_str} - Programme 3 - [BLACKLIST] - Fichier : {nom_fichier} | Chemin : {chemin} | Métadonnées : {{{details_meta}}}\n"
        with open(AETEBLACKLIST_TXT, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        logging.error(f" ❌ Erreur écriture aeteblacklist.txt : {e}")

def envoyer_a_django(chemin_absolu, infos):
    """Envoie le fichier MP3 et ses métadonnées à l'API Django."""
    try:
        donnees = {
            "duree_secondes": infos.get("duree_secondes"),
            "metadonnees_completes": json.dumps(infos.get("metadonnees_completes"))
        }
        with open(chemin_absolu, 'rb') as fichier_mp3:
            fichiers = {'fichier_audio': fichier_mp3}
            reponse = requests.post(URL_API_DJANGO, data=donnees, files=fichiers)
            if reponse.status_code in [200, 201]:
                return True
            else:
                logging.error(f" ❌ Erreur Django (Code {reponse.status_code}) : {reponse.text}")
                return False
    except Exception as e:
        logging.error(f" ❌ Impossible de contacter Django : {e}")
        return False

def callback(ch, method, properties, body):
    """Filtre (blacklist & durée), envoie à Django, puis publie dans la file de suppression du Programme 4 sans supprimer."""
    try:
        message_recu = json.loads(body.decode())
        chemin = message_recu["chemin_absolu"]
        
        if not os.path.exists(chemin):
            logging.warning(f" ⚠️ Fichier introuvable ({chemin}). Ignoré.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        meta = message_recu.get("metadonnees_completes", {})
        duree = message_recu.get("duree_secondes", 0)
        
        # 1. Vérification Blacklist
        if est_blackliste(meta):
            logging.info(f" 🛑 [BLACKLIST] Fichier ignoré (ni envoyé, ni supprimé) : {os.path.basename(chemin)}")
            enregistrer_blackliste_txt(chemin, meta)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        # 2. Vérification Durée maximale
        duree_max = lire_duree_max()
        if duree_max is not None and duree > duree_max:
            logging.info(f" ⏳ [DUREE DEPASSEE] Fichier ({duree}s > {duree_max}s) ignoré (ni envoyé, ni supprimé) : {os.path.basename(chemin)}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        # 3. Envoi vers Django (Web)
        logging.info(f" 🚀 Envoi vers l'API Django : {os.path.basename(chemin)} ({duree}s)")
        succes = envoyer_a_django(chemin, message_recu)
        
        if succes:
            logging.info(f" ✅ Envoi Web réussi. Ajout à la file de suppression '{QUEUE_A_SUPPRIMER}' pour le Programme 4...")
            ch.basic_publish(
                exchange='',
                routing_key=QUEUE_A_SUPPRIMER,
                body=json.dumps({"chemin_absolu": chemin})
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logging.warning(f" ⚠️ Échec envoi Web. Requeue pour réessai.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
    except Exception as e:
        logging.error(f" ❌ Erreur générale lors du traitement : {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_METADATA)
    channel.queue_declare(queue=QUEUE_A_SUPPRIMER)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_METADATA, on_message_callback=callback)
    
    logging.info(f" [*] Programme 3 actif. Écoute de '{QUEUE_METADATA}' -> Filtrage & Envoi Web -> Envoi à '{QUEUE_A_SUPPRIMER}'... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme 3 arrêté par l’utilisateur.')