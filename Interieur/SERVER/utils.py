import os
import csv
import logging
from datetime import datetime

from db import get_mysql_connection
from config import CSV_FILE, DATA_DIR

def add_measurement(device_id, temperature, humidity):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO measurements (device_id, time, temperature, humidity) VALUES (%s, %s, %s, %s)",
                (device_id, current_time, temperature, humidity)
            )
            conn.commit()
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([device_id, current_time, temperature, humidity])
    except Exception as e:
        logging.error(f"Ajout de mesure : {e}")

def get_all_measurements():
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT device_id, time, temperature, humidity 
            FROM measurements 
            ORDER BY time ASC
        """)
        rows = cursor.fetchall()
    def format_fr(dt):
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except:
                return dt
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    return [
        {
            "device_id": row[0],
            "time": format_fr(row[1]),
            "temperature": row[2],
            "humidity": row[3]
        }
        for row in rows
    ]

def initialize_csv():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Date/Heure", "Temperature (C)", "Humidite (%)"])
