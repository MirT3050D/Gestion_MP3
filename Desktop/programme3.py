import pika
import json
import os
import requests
import logging
import datetime

from config import LOG_FILE, URL_API_DJANGO, BLACKLIST_FILE, AETEBLACKLIST_TXT

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
        
        # 1. Normaliser et collecter les regles
        regles = []
        if isinstance(data, list):
            # Format moderne : liste directe de dictionnaires (regles)
            regles = data
        elif isinstance(data, dict):
            # Format herite (Legacy)
            # a) "artistes" -> regle {"artiste": artiste}
            for a in data.get("artistes", []):
                if isinstance(a, str) and a.strip():
                    regles.append({"artiste": a.strip()})
            # b) "genres" -> regle {"genre": genre}
            for g in data.get("genres", []):
                if isinstance(g, str) and g.strip():
                    regles.append({"genre": g.strip()})
            # c) "combinaisons" ou "regles" -> liste de dictionnaires
            for c in data.get("combinaisons", []):
                if isinstance(c, dict) and c:
                    regles.append(c)
            for r in data.get("regles", []):
                if isinstance(r, dict) and r:
                    regles.append(r)
        
        # 2. Verifier chaque regle
        for regle in regles:
            if not isinstance(regle, dict) or not regle:
                continue
            
            match_complet = True
            criteres_actifs = 0
            
            for cle, valeur_attendue in regle.items():
                if valeur_attendue is None:
                    continue
                val_attendue_str = str(valeur_attendue).strip().lower()
                if not val_attendue_str:
                    continue
                
                criteres_actifs += 1
                
                # Recuperation et normalisation de la valeur de la piste
                val_piste = metadonnees.get(cle)
                if val_piste is None:
                    match_complet = False
                    break
                
                val_piste_str = str(val_piste).strip().lower()
                if val_piste_str != val_attendue_str:
                    match_complet = False
                    break
            
            # Si au moins un critere actif est defini et qu'ils correspondent tous
            if criteres_actifs > 0 and match_complet:
                return True
                
    except Exception as e:
        logging.error(f" Erreur lecture blacklist : {e}")
    return False

def enregistrer_blackliste_txt(chemin, metadonnees):
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        nom_fichier = os.path.basename(chemin)
        details_meta = ", ".join(f"'{k}': '{v}'" for k, v in metadonnees.items() if v)
        log_line = f"{now_str} - Programme 3 - [BLACKLIST] - Fichier : {nom_fichier} | Chemin : {chemin} | Métadonnées : {{{details_meta}}}\n"
        
        with open(AETEBLACKLIST_TXT, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        logging.error(f" Erreur lors de l'écriture dans aeteblacklist.txt : {e}")

def callback(ch, method, properties, body):
    message_recu = json.loads(body.decode())
    chemin = message_recu["chemin_absolu"]
    
    # Verif existence
    if not os.path.exists(chemin):
        logging.warning(f"  Fichier introuvable ({chemin}). Il a probablement deja ete traite. Suppression du message de la file.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Verif blacklist
    meta_piste = message_recu.get("metadonnees_completes", {})
    if est_blackliste(meta_piste):
        logging.info(f"  Fichier blacklist. Enregistrement et suppression du fichier local...")
        enregistrer_blackliste_txt(chemin, meta_piste)
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