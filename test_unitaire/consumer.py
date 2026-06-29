import pika
import sys
import os

def main():
    # 1. Connexion au serveur RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # 2. On s'assure que la file existe (au cas où le consumer démarrerait avant le producer)
    channel.queue_declare(queue='mp3_decouverts')

    # 3. Définition de la fonction qui va gérer la réception du message
    def callback(ch, method, properties, body):
        print(f" [x] Message reçu : {body.decode()}")
        # On dit à RabbitMQ que le message a bien été traité
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # 4. On indique à RabbitMQ quelle fonction appeler quand un message arrive
    channel.basic_consume(queue='mp3_decouverts', on_message_callback=callback)

    print(' [*] En attente de messages. Pour quitter, appuyez sur CTRL+C')
    # 5. On lance une boucle infinie qui écoute la file
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrompu')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)