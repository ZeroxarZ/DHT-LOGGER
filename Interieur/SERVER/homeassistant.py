import os
import requests
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

HOME_ASSISTANT_URL = os.environ.get("HOME_ASSISTANT_URL")
HOME_ASSISTANT_TOKEN = os.environ.get("HOME_ASSISTANT_TOKEN")

def send_state(sensor, value, unit, name):
    try:
        headers = {
            "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json"
        }
        resp = requests.post(
            f"{HOME_ASSISTANT_URL}/api/states/sensor.{sensor}",
            headers=headers,
            json={
                "state": value,
                "attributes": {
                    "unit_of_measurement": unit,
                    "friendly_name": name,
                    "last_update": datetime.now().isoformat()
                }
            },
            timeout=5
        )
        if resp.status_code != 200:
            logging.error(f"Erreur Home Assistant: {resp.status_code} - {resp.text}")
    except Exception as e:
        logging.error(f"Erreur d'envoi à Home Assistant : {e}")

def send_to_home_assistant(device_id, temperature, humidity):
    if temperature is None or temperature == "":
        logging.error(f"Température manquante pour device {device_id}, envoi ignoré.")
    else:
        send_state(f"{device_id}_temperature", temperature, "°C", f"Température {device_id}")
        send_state(f"{device_id}_humidity", humidity, "%", f"Humidité {device_id}")