import pika
import json
import os
from mutagen.mp3 import MP3
import logging

from config import LOG_FILE, QUEUE_DECOUVERTS, QUEUE_METADATA

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 2 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def extraire_toutes_les_metadonnees(chemin_fichier):
    """Ouvre le MP3 et extrait toutes les métadonnées ID3 disponibles ainsi que la durée en secondes."""
    try:
        audio = MP3(chemin_fichier)
        duree_secondes = int(audio.info.length)
        
        tags_complets = {}
        for cle, valeur in audio.items():
            tags_complets[str(cle)] = str(valeur)
            
        if not tags_complets:
            tags_complets["nom_defaut"] = os.path.basename(chemin_fichier)

        return {
            "chemin_absolu": chemin_fichier,
            "duree_secondes": duree_secondes,
            "metadonnees_completes": tags_complets
        }
    except Exception as e:
        logging.error(f" ❌ Erreur lors de la lecture du fichier {chemin_fichier} : {e}")
        return None

def callback(ch, method, properties, body):
    """Extrait les métadonnées du fichier reçu et les transmet au Programme 3."""
    try:
        message_recu = json.loads(body.decode())
        chemin = message_recu["chemin_absolu"]
        logging.info(f" [->] Analyse en cours : {chemin}")
        
        infos = extraire_toutes_les_metadonnees(chemin)
        
        if infos:
            ch.basic_publish(
                exchange='',
                routing_key=QUEUE_METADATA,
                body=json.dumps(infos)
            )
            logging.info(f" [<-] Métadonnées extraites et envoyées dans la file '{QUEUE_METADATA}'")
            
    except Exception as e:
        logging.error(f" ❌ Erreur générale lors du traitement du message : {e}")
        
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_DECOUVERTS)
    channel.queue_declare(queue=QUEUE_METADATA)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_DECOUVERTS, on_message_callback=callback)
    
    logging.info(f" [*] Programme 2 actif. Écoute de '{QUEUE_DECOUVERTS}' -> Extraction -> Envoi à '{QUEUE_METADATA}'... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme 2 arrêté par l’utilisateur.')