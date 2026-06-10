Bash
docker run -d --name mon-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
🔍 Que fait cette commande ?
-d : Lance le conteneur en arrière-plan (détaché).

--name mon-rabbitmq : Donne un nom simple à ton conteneur.

-p 5672:5672 : Ouvre le port utilisé par Python pour envoyer les messages. 🔌

-p 15672:15672 : Ouvre le port de l'interface web de gestion. 💻

rabbitmq:3-management : Télécharge la version de RabbitMQ avec l'interface graphique.

Une fois la commande lancée, attends une minute, puis ouvre ton navigateur et va sur http://localhost:15672. Les identifiants par défaut sont guest pour le nom d'utilisateur et guest pour le mot de passe.