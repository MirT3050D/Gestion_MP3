import os
import pika
import json

# 📁 Configuration du dossier et de RabbitMQ
DOSSIER_MUSIQUE = r"C:\Users\rahaj\Desktop\ITU\Info\Projet_Mr_Vahatra\Gestion_MP3\musique"
NOM_QUEUE = 'mp3_decouverts'

def envoyer_message_rabbitmq(chaine_json):
    # 🔌 Connexion à RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # 📥 Déclaration de la file
    channel.queue_declare(queue=NOM_QUEUE)
    
    # ✉️ Envoi du message
    channel.basic_publish(exchange='', routing_key=NOM_QUEUE, body=chaine_json)
    print(f" [x] Envoyé à RabbitMQ : {chaine_json}")
    
    connection.close()

def scanner_et_envoyer():
    # 📝 1. Récupérer la liste des fichiers
    tous_les_fichiers = os.listdir(DOSSIER_MUSIQUE)
    
    # 🔍 2. Filtrer les MP3
    for fichier in tous_les_fichiers:
        if fichier.endswith('.mp3'):
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

if __name__ == "__main__":
    scanner_et_envoyer()