import os
import pika
import json
import logging
import time

# Config dossier et RabbitMQ
from config import DOSSIER_MUSIQUE, LOG_FILE
NOM_QUEUE = 'mp3_decouverts'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 1 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def envoyer_message_rabbitmq(chaine_json):
    # Connexion RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # Declaration queue
    channel.queue_declare(queue=NOM_QUEUE)
    
    # Envoi message
    channel.basic_publish(exchange='', routing_key=NOM_QUEUE, body=chaine_json)
    logging.info(f" [x] Envoye a RabbitMQ : {chaine_json}")
    
    connection.close()

def scanner_et_envoyer():
    fichiers_deja_envoyes = set()
    
    while True:
        logging.info(" Demarrage du scan du dossier musique...")
        # 1. Liste fichiers
        tous_les_fichiers = os.listdir(DOSSIER_MUSIQUE)
        
        nouveaux_fichiers = 0
        
        # 2. Filtrer MP3
        for fichier in tous_les_fichiers:
            if fichier.lower().endswith('.mp3') and fichier not in fichiers_deja_envoyes:
                chemin_complet = os.path.join(DOSSIER_MUSIQUE, fichier)
                
                # 3. Creation dict
                donnees = {
                    "evenement": "fichier_decouvert",
                    "chemin_absolu": chemin_complet,
                    "nom_fichier": fichier
                }
                
                # 4. JSON
                message_json = json.dumps(donnees)
                
                # 5. Envoi
                envoyer_message_rabbitmq(message_json)
                
                fichiers_deja_envoyes.add(fichier)
                nouveaux_fichiers += 1
                
        if nouveaux_fichiers == 0:
            logging.info(" Aucun nouveau fichier MP3 detecte.")
        else:
            logging.info(f" {nouveaux_fichiers} nouveaux fichiers detectes et envoyes.")
            
        logging.info(" Attente de 5 min avant prochain scan...")
        # Attente 300s, interruptible
        for _ in range(300):
            if os.path.exists("force_scan.txt"):
                try:
                    os.remove("force_scan.txt")
                except:
                    pass
                logging.info(" Scan force demande par l'utilisateur !")
                break
            time.sleep(1)

if __name__ == "__main__":
    scanner_et_envoyer()