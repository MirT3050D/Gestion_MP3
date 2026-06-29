import pika
import json
import os
from mutagen.mp3 import MP3
import logging

from config import LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 2 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Config queues RabbitMQ
QUEUE_ENTREE = 'mp3_decouverts'
QUEUE_SORTIE = 'metadata_extraites'

def extraire_toutes_les_metadonnees(chemin_fichier):
    try:
        print("p2")
        audio = MP3(chemin_fichier)
        
        # Extrait la duree
        duree_secondes = int(audio.info.length)
        
        # Extrait les tags
        tags_complets = {}
        for cle, valeur in audio.items():
            # Conversion string pour JSON
            tags_complets[str(cle)] = str(valeur)
            
        # Nom par defaut si pas de tag
        if not tags_complets:
            tags_complets["nom_defaut"] = os.path.basename(chemin_fichier)

        return {
            "chemin_absolu": chemin_fichier,
            "duree_secondes": duree_secondes,
            "metadonnees_completes": tags_complets
        }
        
    except Exception as e:
        # Erreur de lecture
        logging.error(f" Erreur lors de la lecture du fichier {chemin_fichier} : {e}")
        return None

def callback(ch, method, properties, body):
    # Callback message P1
    try:
        # 1. JSON
        message_recu = json.loads(body.decode())
        print(message_recu)
        chemin = message_recu["chemin_absolu"]
        logging.info(f" [->] Analyse en cours : {chemin}")
        
        # 2. Extraction
        infos = extraire_toutes_les_metadonnees(chemin)
        
        # 3. Envoi P3
        if infos:
            ch.basic_publish(
                exchange='',
                routing_key=QUEUE_SORTIE,
                body=json.dumps(infos)
            )
            logging.info(f" [<-] Toutes les metadonnees ont ete envoyees dans la file '{QUEUE_SORTIE}'")
            
    except Exception as e:
        logging.error(f" Erreur generale lors du traitement du message : {e}")
        
    finally:
        # Accuse de reception
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Connexion RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # Declaration des deux files
    channel.queue_declare(queue=QUEUE_ENTREE)
    channel.queue_declare(queue=QUEUE_SORTIE)
    
    # Configuration ecoute
    channel.basic_consume(queue=QUEUE_ENTREE, on_message_callback=callback)
    
    logging.info(f" [*] Programme 2 actif. Ecoute de la file '{QUEUE_ENTREE}'... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme arrete par l\'utilisateur.')