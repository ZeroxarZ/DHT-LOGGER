import os
import time
import secrets
import logging
from threading import Thread

from flask import (
    Flask, render_template, jsonify, request, session, redirect, url_for, abort, flash
)
from flask_cors import CORS
from dotenv import load_dotenv

# Modules internes
from users import users_bp
from admin import admin_bp
from api import api_bp
from config import (
    SERVER_ADDRESS, SERVER_PORT, WEB_DIR, DATA_DIR, CSV_FILE, BACKUP_DIR,
    BACKUP_INTERVAL_SECONDS, BACKUP_RETENTION_DAYS, CLEANUP_INTERVAL_SECONDS
)
from limiter_config import limiter
from utils import add_measurement, get_all_measurements, initialize_csv
from backup import backup_csv, cleanup_old_backups
from sequence import update_sequence_table
from socket_server import start_socket_server
from sendmail import log_admin_action
from auth import admin_required
from db import get_mysql_connection
from errors import errors_bp

# Chargement des variables d'environnement
load_dotenv()

# ========== FLASK SETUP ==========
app = Flask(
    __name__,
    static_folder=WEB_DIR,
    static_url_path="",
    template_folder=WEB_DIR
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
CORS(app)
limiter.init_app(app)
app.register_blueprint(api_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(errors_bp)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    filename="app.log",
    filemode="a"
)

# Pour forcer tous les modules à utiliser ce handler
logging.getLogger().addHandler(logging.StreamHandler())

# ========== ROUTES ==========

@app.route("/")
def index():
    return render_template("index.html", server_address=SERVER_ADDRESS)

@app.route("/historique")
def historique():
    return render_template("historique.html")

@app.route("/rgpd")
def rgpd():
    return render_template("rgpd.html")

@app.route("/data")
def get_data():
    return jsonify(get_all_measurements())

@app.route("/alerte")
def alerte():
    return render_template("alerte.html")


# ========== MAIN ==========
if __name__ == "__main__":
    time.sleep(1)
    update_sequence_table()
    initialize_csv()
    Thread(target=start_socket_server, daemon=True).start()
    Thread(target=backup_csv, daemon=True).start()
    Thread(target=cleanup_old_backups, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
