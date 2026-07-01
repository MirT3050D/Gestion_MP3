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

ID3_MAPPING = {
    "TIT2": "titre",
    "TPE1": "artiste",
    "TCON": "genre",
    "TALB": "album",
    "TRCK": "piste",
    "TDRC": "annee",
    "TYER": "annee",
    "TORY": "annee_originale",
    "TDAT": "date",
    "TIME": "heure",
    "COMM": "commentaire",
    "TPE2": "artiste_album",
    "TPOS": "disque",
    "TSRC": "isrc",
    "TIT1": "groupe",
    "TIT3": "sous_titre",
    "TEXT": "parolier",
    "TCOM": "compositeur",
    "TPE3": "chef_orchestre",
    "TPE4": "interprete_remixeur",
    "TPUB": "editeur",
    "TLEN": "duree_ms",
    "TMED": "type_media",
    "TCOP": "copyright",
    "USLT": "paroles",
    "SYLT": "paroles_synchronisees"
}

def format_valeur(valeur):
    if hasattr(valeur, 'text'):
        if isinstance(valeur.text, list):
            return "\n".join(str(x) for x in valeur.text)
        return str(valeur.text)
    return str(valeur)

def extraire_toutes_les_metadonnees(chemin_fichier):
    try:
        print("p2")
        audio = MP3(chemin_fichier)
        duree_secondes = int(audio.info.length)
        
        tags_complets = {}
        # Extrait tags ID3
        for cle, valeur in audio.items():
            base_key = cle.split(':')[0]
            nom_lisible = ID3_MAPPING.get(base_key, cle)
            tags_complets[nom_lisible] = format_valeur(valeur)
            
        # Infos techniques
        tags_complets["duree_secondes"] = duree_secondes
        if hasattr(audio, 'info') and audio.info:
            info = audio.info
            if hasattr(info, 'bitrate') and info.bitrate:
                tags_complets["bitrate_kbps"] = int(info.bitrate / 1000)
            if hasattr(info, 'sample_rate') and info.sample_rate:
                tags_complets["taux_echantillonnage_hz"] = info.sample_rate
            if hasattr(info, 'channels') and info.channels:
                tags_complets["canaux"] = info.channels

        if "artiste_album" in tags_complets and "artiste" not in tags_complets:
            tags_complets["artiste"] = tags_complets["artiste_album"]
        elif "artiste" in tags_complets and "artiste_album" not in tags_complets:
            tags_complets["artiste_album"] = tags_complets["artiste"]

        if not tags_complets or all(k in ("duree_secondes", "bitrate_kbps", "taux_echantillonnage_hz", "canaux") for k in tags_complets):
            # Nom par defaut
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