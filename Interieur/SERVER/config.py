import os

BASE_DIR = "CHEMIN" # Remplacez CHEMIN par le chemin absolu vers le dossier de votre projet
SERVER_DIR = os.path.join(BASE_DIR, "SERVER")
WEB_DIR = os.path.join(BASE_DIR, "WEB")
DATA_DIR = os.path.join(BASE_DIR, "DATA")
BACKUP_DIR = os.path.join(BASE_DIR, "BACKUPS")
CSV_FILE = os.path.join(DATA_DIR, "data.csv")
# Variables d'environnement et valeurs par défaut
SERVER_ADDRESS = os.environ.get("SERVER_ADDRESS")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 10000))

BACKUP_INTERVAL_SECONDS = 86400  # 24h
CLEANUP_INTERVAL_SECONDS = 86400  # 24h
BACKUP_RETENTION_DAYS = 5