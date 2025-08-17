import socket
import logging
from config import SERVER_ADDRESS, SERVER_PORT
from utils import add_measurement
from homeassistant import send_to_home_assistant
from admin import get_homeassistant_enabled

def start_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))
    server_socket.listen(5)
    logging.info(f"Serveur à l'écoute sur {SERVER_ADDRESS}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        logging.info(f"Connexion de {client_address}")
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if data:
                logging.info(f"Données reçues : {data}")
                if "ID:" in data and "Temperature:" in data and "Humidity:" in data:
                    try:
                        device_id = data.split("ID:")[1].split(" ")[0].strip()
                        temperature = float(data.split("Temperature:")[1].split("C")[0].strip())
                        humidity = float(data.split("Humidity:")[1].split("%")[0].strip())
                        add_measurement(device_id, temperature, humidity)
                        if get_homeassistant_enabled():
                            send_to_home_assistant(device_id, temperature, humidity)
                    except ValueError as ve:
                        logging.error(f"Extraction des données : {ve}")
                else:
                    logging.warning("Format de données inattendu.")
        except Exception as e:
            logging.error(f"Réception données socket : {e}")
        finally:
            client_socket.close()