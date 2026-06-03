import pika
import json
import os
import requests
import logging

LOG_FILE = r"C:\Users\rahaj\Desktop\ITU\Info\Projet_Mr_Vahatra\Gestion_MP3\Desktop\log.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 3 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 📥 File d'attente à écouter
QUEUE_ENTREE = 'metadata_extraites'

# 🌐 Configuration de l'API Django (à ajuster selon ton projet)
URL_API_DJANGO = "http://localhost:8000/api/upload-mp3/"

def envoyer_a_django(chemin_absolu, metadonnees):
    """Envoie le fichier MP3 et ses métadonnées à l'API Django."""
    try:
        # 📝 Préparation des données texte
        donnees = {
            "duree_secondes": metadonnees.get("duree_secondes"),
            "metadonnees_completes": json.dumps(metadonnees.get("metadonnees_completes"))
        }
        
        # 🎵 Ouverture du fichier MP3 en mode binaire ('rb')
        with open(chemin_absolu, 'rb') as fichier_mp3:
            fichiers = {'fichier_audio': fichier_mp3}
            
            # 🚀 Envoi de la requête HTTP POST
            reponse = requests.post(URL_API_DJANGO, data=donnees, files=fichiers)
            
            # Si le statut est 200 ou 201, c'est un succès
            if reponse.status_code in [200, 201]:
                return True
            else:
                logging.error(f" ❌ Erreur Django (Code {reponse.status_code}) : {reponse.text}")
                return False
                
    except Exception as e:
        logging.error(f" ❌ Impossible de contacter Django : {e}")
        return False

def callback(ch, method, properties, body):
    message_recu = json.loads(body.decode())
    chemin = message_recu["chemin_absolu"]
    
    # 🚨 VÉRIFICATION : Si le fichier n'existe plus (déjà supprimé ou traité)
    if not os.path.exists(chemin):
        logging.warning(f"  ⚠️ Fichier introuvable ({chemin}). Il a probablement déjà été traité. Suppression du message de la file.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    logging.info(f" [->] Tentative d'envoi pour : {chemin}")
    
    # 1. Envoi à l'API
    succes = envoyer_a_django(chemin, message_recu)
    
    if succes:
        logging.info(f"  ✅ Envoi réussi. Suppression du fichier local...")
        try:
            # 🗑️ 2. Suppression du fichier d'origine si succès
            os.remove(chemin)
            logging.info(f"  🗑️ Fichier supprimé : {chemin}")
            # 👍 3. Accusé de réception à RabbitMQ (le message est effacé de la file)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.warning(f"  ⚠️ Fichier envoyé mais impossible de le supprimer : {e}")
            # On acquitte quand même pour éviter de renvoyer le fichier en boucle
            ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        logging.warning(f"  🔄 Échec. Le message reste dans la file pour un nouvel essai.")
        # 🔁 En cas d'échec, on dit à RabbitMQ de remettre le message dans la file (requeue=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_ENTREE)
    
    # On configure RabbitMQ pour qu'il ne donne qu'un message à la fois à ce script
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_ENTREE, on_message_callback=callback)
    
    logging.info(f" [*] Programme 3 actif. En attente de métadonnées à envoyer... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    main()