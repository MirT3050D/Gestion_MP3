import pika
import json
import os
import requests
import logging

from config import LOG_FILE, URL_API_DJANGO, BLACKLIST_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 3 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Queue a ecouter
QUEUE_ENTREE = 'metadata_extraites'

def envoyer_a_django(chemin_absolu, metadonnees):
    try:
        # Preparation donnees
        donnees = {
            "duree_secondes": metadonnees.get("duree_secondes"),
            "metadonnees_completes": json.dumps(metadonnees.get("metadonnees_completes"))
        }
        
        # Ouverture fichier MP3
        with open(chemin_absolu, 'rb') as fichier_mp3:
            fichiers = {'fichier_audio': fichier_mp3}
            
            # Requete POST
            reponse = requests.post(URL_API_DJANGO, data=donnees, files=fichiers)
            
            # Succes si 200/201
            if reponse.status_code in [200, 201]:
                return True
            else:
                logging.error(f" Erreur Django (Code {reponse.status_code}) : {reponse.text}")
                return False
                
    except Exception as e:
        logging.error(f" Impossible de contacter Django : {e}")
        return False

def est_blackliste(metadonnees):
    if not os.path.exists(BLACKLIST_FILE):
        return False
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        blacklist_artistes = [a.strip().lower() for a in data.get("artistes", []) if a.strip()]
        blacklist_genres = [g.strip().lower() for g in data.get("genres", []) if g.strip()]
        
        artiste = str(metadonnees.get("artiste", "")).strip().lower()
        genre = str(metadonnees.get("genre", "")).strip().lower()
        
        if artiste and any(a == artiste for a in blacklist_artistes):
            return True
        if genre and any(g == genre for g in blacklist_genres):
            return True
    except Exception as e:
        logging.error(f" Erreur lecture blacklist : {e}")
    return False

def callback(ch, method, properties, body):
    message_recu = json.loads(body.decode())
    chemin = message_recu["chemin_absolu"]
    
    # Verif existence
    if not os.path.exists(chemin):
        logging.warning(f"  Fichier introuvable ({chemin}). Il a probablement deja ete traite. Suppression du message de la file.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Verif blacklist
    if est_blackliste(message_recu.get("metadonnees_completes", {})):
        logging.info(f"  Fichier blacklist (artiste ou genre). Suppression du fichier local...")
        try:
            os.remove(chemin)
        except Exception as e:
            logging.warning(f"  Impossible de supprimer le fichier de la blacklist : {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
 
    logging.info(f" [->] Tentative d'envoi pour : {chemin}")
    
    # 1. Envoi API
    succes = envoyer_a_django(chemin, message_recu)
    
    if succes:
        logging.info(f"  Envoi reussi. Suppression du fichier local...")
        try:
            # 2. Suppression fichier si succes
            os.remove(chemin)
            logging.info(f"  Fichier supprime : {chemin}")
            # 3. Accuse de reception
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.warning(f"  Fichier envoye mais impossible de le supprimer : {e}")
            # Acquittement
            ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        logging.warning(f"  Echec. Le message reste dans la file pour un nouvel essai.")
        # Requeue si echec
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_ENTREE)
    
    # QoS
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_ENTREE, on_message_callback=callback)
    
    logging.info(f" [*] Programme 3 actif. En attente de metadonnees a envoyer... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    main()