import pika
import json
import os
import logging

from config import LOG_FILE, QUEUE_A_SUPPRIMER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 4 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def callback(ch, method, properties, body):
    """Reçoit la liste des fichiers à supprimer et supprime physiquement les MP3 de l'ordinateur local."""
    try:
        message_recu = json.loads(body.decode())
        chemin = message_recu.get("chemin_absolu")
        
        if not chemin:
            logging.warning(" ⚠️ Message reçu sans chemin_absolu.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        if os.path.exists(chemin):
            try:
                os.remove(chemin)
                logging.info(f" 🗑️ [SUPPRESSION REUSSIE] Fichier supprimé : {chemin}")
            except Exception as e:
                logging.error(f" ❌ Erreur lors de la suppression du fichier '{chemin}' : {e}")
        else:
            logging.info(f" ℹ️ Fichier déjà introuvable ou déjà supprimé : {chemin}")
            
        # Acquittement du message pour le sortir de la file
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logging.error(f" ❌ Erreur lors du traitement de la suppression : {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_A_SUPPRIMER)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_A_SUPPRIMER, on_message_callback=callback)
    
    logging.info(f" [*] Programme 4 actif. Écoute de la file '{QUEUE_A_SUPPRIMER}' pour supprimer les MP3... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme 4 arrêté par l’utilisateur.')
