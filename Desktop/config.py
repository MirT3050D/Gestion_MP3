import os

# Chemins systeme
DOSSIER_DESKTOP = r"D:\NainaMP3\Gestion_MP3\Desktop"
LOG_FILE = os.path.join(DOSSIER_DESKTOP, "log.txt")
DOSSIER_MUSIQUE = r"D:\NainaMP3\musique"

# Configuration API Django
URL_API_DJANGO = "http://localhost:8000/api/upload-mp3/"

# Fichier blacklist
BLACKLIST_FILE = os.path.join(DOSSIER_DESKTOP, "blacklist.json")
AETEBLACKLIST_TXT = os.path.join(DOSSIER_DESKTOP, "aeteblacklist.txt")
DUREE_JSON = os.path.join(DOSSIER_DESKTOP, "duree.json")

