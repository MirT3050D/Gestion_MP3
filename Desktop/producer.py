import pika
import json

# 1. Connexion au serveur RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# 2. Création de la file d'attente (si elle n'existe pas déjà)
channel.queue_declare(queue='mp3_decouverts')

# 3. Préparation du message (on simule les données d'un MP3 trouvé)
data = {"chemin_fichier": "C:/ma_musique/chanson.mp3"}
message = json.dumps(data)

# 4. Envoi du message dans la file
channel.basic_publish(exchange='',
                      routing_key='mp3_decouverts',
                      body=message)

print(# Évitons les confirmations excessives, affichons juste l'action
f" [x] Message envoyé : {message}")

# 5. Fermeture propre de la connexion
connection.close()