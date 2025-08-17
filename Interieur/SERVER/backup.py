import os
import shutil
import logging
import time
from datetime import datetime, timedelta
from config import BACKUP_DIR, CSV_FILE, BACKUP_INTERVAL_SECONDS, BACKUP_RETENTION_DAYS, CLEANUP_INTERVAL_SECONDS

def backup_csv():
    while True:
        try:
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)
            backup_filename = datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + "_data.csv"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            shutil.copy(CSV_FILE, backup_path)
            logging.info(f"Sauvegarde effectuée : {backup_path}")
        except Exception as e:
            logging.error(f"Backup CSV : {e}")
        time.sleep(BACKUP_INTERVAL_SECONDS)

def cleanup_old_backups():
    while True:
        try:
            if os.path.exists(BACKUP_DIR):
                now = datetime.now()
                for filename in os.listdir(BACKUP_DIR):
                    file_path = os.path.join(BACKUP_DIR, filename)
                    if os.path.isfile(file_path):
                        creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if now - creation_time > timedelta(days=BACKUP_RETENTION_DAYS):
                            os.remove(file_path)
                            logging.info(f"Backup supprimé : {file_path}")
        except Exception as e:
            logging.error(f"Cleanup backups : {e}")
        time.sleep(CLEANUP_INTERVAL_SECONDS)