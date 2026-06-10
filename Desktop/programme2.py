import pika
import json
import os
from mutagen.mp3 import MP3
import logging

LOG_FILE = r"D:\NainaMP3\Gestion_MP3\Desktop\log.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Programme 2 - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 📥 Configuration des files d'attente RabbitMQ
QUEUE_ENTREE = 'mp3_decouverts'
QUEUE_SORTIE = 'metadata_extraites'

def extraire_toutes_les_metadonnees(chemin_fichier):
    """
    Ouvre le MP3 et extrait absolument toutes les métadonnées disponibles
    ainsi que la durée exacte en secondes.
    """
    try:
        print("p2")
        audio = MP3(chemin_fichier)
        
        # ⏱️ Extraction de la durée (essentielle pour l'algorithme de playlist)
        duree_secondes = int(audio.info.length)
        
        # 🏷️ Extraction de l'intégralité des tags présents dans le fichier
        tags_complets = {}
        for cle, valeur in audio.items():
            # On convertit les clés et les valeurs en texte pour la compatibilité JSON
            tags_complets[str(cle)] = str(valeur)
            
        # 🧩 Si aucun tag n'est trouvé, on met au moins le nom du fichier par défaut
        if not tags_complets:
            tags_complets["nom_defaut"] = os.path.basename(chemin_fichier)

        return {
            "chemin_absolu": chemin_fichier,
            "duree_secondes": duree_secondes,
            "metadonnees_completes": tags_complets
        }
        
    except Exception as e:
        # 📝 En cas d'erreur (fichier corrompu, etc.), on log et on retourne None
        logging.error(f" ❌ Erreur lors de la lecture du fichier {chemin_fichier} : {e}")
        return None

def callback(ch, method, properties, body):
    """Fonction déclenchée à la réception d'un message du Programme 1."""
    try:
        # 1. Lecture du message JSON reçu
        message_recu = json.loads(body.decode())
        print(message_recu)
        chemin = message_recu["chemin_absolu"]
        logging.info(f" [->] Analyse en cours : {chemin}")
        
        # 2. Extraction de toutes les métadonnées
        infos = extraire_toutes_les_metadonnees(chemin)
        
        # 3. Si l'extraction a réussi, on envoie le tout au Programme 3
        if infos:
            ch.basic_publish(
                exchange='',
                routing_key=QUEUE_SORTIE,
                body=json.dumps(infos)
            )
            logging.info(f" [<-] Toutes les métadonnées ont été envoyées dans la file '{QUEUE_SORTIE}'")
            
    except Exception as e:
        logging.error(f" ❌ Erreur générale lors du traitement du message : {e}")
        
    finally:
        # 4. Accusé de réception envoyé à RabbitMQ pour libérer le message d'entrée
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # 🔌 Connexion au serveur RabbitMQ local
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # 📥 Déclaration des deux files d'attente (sécurité si elles n'existent pas)
    channel.queue_declare(queue=QUEUE_ENTREE)
    channel.queue_declare(queue=QUEUE_SORTIE)
    
    # 🎧 Configuration de l'écoute active
    channel.basic_consume(queue=QUEUE_ENTREE, on_message_callback=callback)
    
    logging.info(f" [*] Programme 2 actif. Écoute de la file '{QUEUE_ENTREE}'... (CTRL+C pour quitter)")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info(' [%] Programme arrêté par l’utilisateur.')