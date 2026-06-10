import os
import pika
import json
import logging
import time

# 📁 Configuration du dossier et de RabbitMQ
DOSSIER_MUSIQUE = r"D:\NainaMP3\musique"
NOM_QUEUE = 'mp3_decouverts'
LOG_FILE = r"D:\NainaMP3\Gestion_MP3\Desktop\log.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 1 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def envoyer_message_rabbitmq(chaine_json):
    # 🔌 Connexion à RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # 📥 Déclaration de la file
    channel.queue_declare(queue=NOM_QUEUE)
    
    # ✉️ Envoi du message
    channel.basic_publish(exchange='', routing_key=NOM_QUEUE, body=chaine_json)
    logging.info(f" [x] Envoyé à RabbitMQ : {chaine_json}")
    
    connection.close()

def scanner_et_envoyer():
    fichiers_deja_envoyes = set()
    
    while True:
        logging.info(" 🔍 Démarrage du scan du dossier musique...")
        # 📝 1. Récupérer la liste des fichiers
        tous_les_fichiers = os.listdir(DOSSIER_MUSIQUE)
        
        nouveaux_fichiers = 0
        
        # 🔍 2. Filtrer les MP3
        for fichier in tous_les_fichiers:
            if fichier.endswith('.mp3') and fichier not in fichiers_deja_envoyes:
                chemin_complet = os.path.join(DOSSIER_MUSIQUE, fichier)
                
                # 🧱 3. Création du dictionnaire selon notre format validé
                donnees = {
                    "evenement": "fichier_decouvert",
                    "chemin_absolu": chemin_complet,
                    "nom_fichier": fichier
                }
                
                # 🔤 4. Conversion en texte JSON
                message_json = json.dumps(donnees)
                
                # 🚀 5. Envoi
                envoyer_message_rabbitmq(message_json)
                
                fichiers_deja_envoyes.add(fichier)
                nouveaux_fichiers += 1
                
        if nouveaux_fichiers == 0:
            logging.info(" 😴 Aucun nouveau fichier MP3 détecté.")
        else:
            logging.info(f" ✅ {nouveaux_fichiers} nouveaux fichiers détectés et envoyés.")
            
        logging.info(" ⏳ Attente de 5 minutes avant le prochain scan (ou scan manuel)...")
        # Attente de 300 secondes (5 minutes), interruptible si 'force_scan.txt' est créé
        for _ in range(300):
            if os.path.exists("force_scan.txt"):
                try:
                    os.remove("force_scan.txt")
                except:
                    pass
                logging.info(" ⚡ Scan forcé demandé par l'utilisateur !")
                break
            time.sleep(1)

if __name__ == "__main__":
    scanner_et_envoyer()