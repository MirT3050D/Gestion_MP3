import os

# Chemins systeme
DOSSIER_DESKTOP = r"C:\Users\rahaj\Desktop\ITU\Info\Projet_Mr_Vahatra\Gestion_MP3\Desktop"
LOG_FILE = os.path.join(DOSSIER_DESKTOP, "log.txt")
DOSSIER_MUSIQUE = r"C:\Users\rahaj\Desktop\ITU\Info\Projet_Mr_Vahatra\musique"

# Configuration API Django
URL_API_DJANGO = "http://localhost:8000/api/upload-mp3/"

# Fichier blacklist
BLACKLIST_FILE = os.path.join(DOSSIER_DESKTOP, "blacklist.json")
AETEBLACKLIST_TXT = os.path.join(DOSSIER_DESKTOP, "aeteblacklist.txt")

# Fichier de durée maximale en secondes
DUREE_MAX_FILE = os.path.join(DOSSIER_DESKTOP, "duree_max.txt")

# Noms des files RabbitMQ
QUEUE_DECOUVERTS = 'mp3_decouverts'
QUEUE_METADATA = 'metadata_extraites'
QUEUE_A_SUPPRIMER = 'mp3_a_supprimer'


