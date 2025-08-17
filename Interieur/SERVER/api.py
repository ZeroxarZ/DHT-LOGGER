from flask import Blueprint, jsonify, request, session
from db import get_mysql_connection
from sendmail import log_admin_action
from auth import admin_required
import logging
import requests
import os

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/check_alert")
def check_alert():
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT temp_min, temp_max, humidity_min, humidity_max FROM alert_config WHERE id=1")
        alert_conf = cursor.fetchone()
        if not alert_conf:
            return jsonify({"error": "Config introuvable"}), 404
        temp_min, temp_max, humidity_min, humidity_max = alert_conf
        cursor.execute("SELECT temperature, humidity FROM measurements ORDER BY time DESC LIMIT 1")
        last_measure = cursor.fetchone()
    if not last_measure:
        return jsonify({"alert": False})
    temperature, humidity = last_measure
    alert = temperature < temp_min or temperature > temp_max or humidity < humidity_min or humidity > humidity_max
    if alert:
        return jsonify({
            "alert": True,
            "temperature": temperature,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "humidity": humidity,
            "humidity_min": humidity_min,
            "humidity_max": humidity_max
        })
    else:
        return jsonify({"alert": False})

@api_bp.route("/api/weather")
def api_weather():
    city = request.args.get("city", "Le Petit-Quevilly,FR")
    api_key = OPENWEATHER_API_KEY
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=fr&appid={api_key}"
    r = requests.get(url)
    return jsonify(r.json())

@api_bp.route("/api/uv")
def api_uv():
    city = request.args.get("city", "TA VILLE,FR") # Remplacez par la ville souhaitée
    api_key = OPENWEATHER_API_KEY
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json()
    if not geo_data:
        return jsonify({"error": "Ville introuvable"}), 404
    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]
    uv_url = f"https://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={api_key}"
    uv_resp = requests.get(uv_url)
    uv_data = uv_resp.json()
    if "value" in uv_data:
        return jsonify({"value": uv_data["value"]})
    else:
        return jsonify({"error": "Indice UV non disponible"}), 404

@api_bp.route("/api/secheresse_all")
def api_secheresse_all():
    try:
        resp = requests.get("https://api.vigieau.beta.gouv.fr/api/departements", timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des données Vigieau : {e}"}), 500

@api_bp.route("/api/secheresse")
def api_secheresse():
    code_dept = request.args.get("code", "XX") # Remplacez par le code de votre département
    try:
        resp = requests.get("https://api.vigieau.beta.gouv.fr/api/departements", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        dep = next((d for d in data if d["code"] == code_dept), None)
        if not dep:
            return jsonify({"error": "Département non trouvé"}), 404
        return jsonify({
            "code": dep["code"],
            "nom": dep["nom"],
            "niveauGraviteMax": dep["niveauGraviteMax"],
            "niveauGraviteSupMax": dep["niveauGraviteSupMax"],
            "niveauGraviteSouMax": dep["niveauGraviteSouMax"],
            "niveauGraviteAepMax": dep["niveauGraviteAepMax"]
        })
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des données Vigieau : {e}"}), 500

@api_bp.route("/save-alert-config", methods=["POST"])
@admin_required
def save_alert_config():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données manquantes"}), 400
    temp_min = data.get("temp_min")
    temp_max = data.get("temp_max")
    humidity_min = data.get("humidity_min")
    humidity_max = data.get("humidity_max")
    if None in (temp_min, temp_max, humidity_min, humidity_max):
        return jsonify({"error": "Paramètres incomplets"}), 400
    try:
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM alert_config WHERE id = 1")
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE alert_config
                    SET temp_min = %s, temp_max = %s, humidity_min = %s, humidity_max = %s
                    WHERE id = 1
                """, (temp_min, temp_max, humidity_min, humidity_max))
            else:
                cursor.execute("""
                    INSERT INTO alert_config (id, temp_min, temp_max, humidity_min, humidity_max)
                    VALUES (1, %s, %s, %s, %s)
                """, (temp_min, temp_max, humidity_min, humidity_max))
            conn.commit()
    except Exception as e:
        logging.error(f"Erreur sauvegarde config alerte : {e}")
        return jsonify({"error": "Erreur interne"}), 500
    log_admin_action(session["user"], "modification des seuils d'alerte", "alert_config")
    return jsonify({"success": True, "message": "Configuration sauvegardée"})