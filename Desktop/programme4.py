import pika
import json
import os
import logging

from config import LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 4 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

QUEUE_ENTREE = 'fichiers_a_supprimer'

def callback(ch, method, properties, body):
    try:
        message_recu = json.loads(body.decode())
        chemin = message_recu.get("chemin_absolu")
        
        if not chemin:
            logging.warning(" Message recu sans chemin_absolu.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        if not os.path.exists(chemin):
            logging.warning(f" Fichier introuvable ({chemin}). Il a probablement deja ete supprime.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        logging.info(f" [->] Tentative de suppression pour : {chemin}")
        os.remove(chemin)
        logging.info(f"  Fichier supprime avec succes : {chemin}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logging.error(f" Erreur lors de la suppression : {e}")
        # Acquittement quand meme pour eviter de bloquer la file
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_ENTREE)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_ENTREE, on_message_callback=callback)
    
    logging.info(f" [*] Programme 4 actif. En attente de fichiers a supprimer... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme arrete par l\'utilisateur.')
