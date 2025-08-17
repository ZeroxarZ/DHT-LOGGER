# **DHT-LOGGER**

> Home Assistant Compatible: This project can easily integrate with Home Assistant for advanced home automation.

DHT-Logger is a complete solution for monitoring, logging, and visualizing temperature and humidity using a DHT22 sensor, a microcontroller (ESP32/ESP8266), and a Python web server. The project features a modern web interface, data storage SQL, exports, alerts, and user management.

---

## 🔧 **Required Hardware**

* 🖥️ Raspberry Pi 4 or 5
* 🔌 ESP32 Nano
* 🌡️ DHT22 Sensor
* 🧵 Jumper wires
* 🏠 Waterproof enclosure (for outdoor installations)
* 📡 Wi-Fi or Ethernet connection

---

## 🛠️ **Wiring Diagram**

| DHT22 | ESP32 Nano         |
| ----- | ------------------ |
| VCC   | 3.3V               |
| DATA  | D4 (Digital Pin 4) |
| GND   | GND                |

---

## 🚀 **Installation & Setup**

### 1️⃣ **Program the ESP32**

* Download and install Arduino IDE: [📥 Arduino IDE](https://www.arduino.cc/en/software)
* Configure ESP32-S3-Box:

  * If it doesn’t appear, add this URL in *File → Preferences → Additional Boards Manager URLs*:

    ```
    http://arduino.esp8266.com/stable/package_esp8266com_index.json
    ```
  * Select the correct COM port and board architecture.
* Install required libraries via *Tools → Manage Libraries*:

  * DHT sensor library (`DHT.h`)
  * ESP32 WiFi library (`WiFi.h`)
* Upload the code, modifying:

  * 📶 Wi-Fi SSID & password
  * 🌍 Server IP address and port

### 2️⃣ **Install Raspberry Pi OS (or Ubuntu)**

* Download Raspberry Pi Imager: [📥 Raspberry Pi Imager](https://www.raspberrypi.com/software/)
* Flash a 64-bit OS image to your SD card
* Configure SSH and Wi-Fi before first boot

### 3️⃣ **Deploy DHT-Logger Server**

* Copy the `DHT-LOGGER-main` folder to your Desktop
* Create `DHTLOGGER` folder and extract the zip
* Edit `server.py` to set server IP & port

### 4️⃣ **Automate server startup with systemd ⚙️**

```bash
sudo nano /etc/systemd/system/dhtlogger.service
```

Paste:

```ini
[Unit]
Description=DHT Logger Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/Interieur/SERVER/server.py
WorkingDirectory=/home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/Interieur/SERVER
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Reload and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dhtlogger
sudo systemctl restart dhtlogger
sudo systemctl status dhtlogger
```

Do the same for the mail alert service (`dhtloggermailinterieur.service`) if email notifications are needed.

---

## **Project Structure**

```
DHT-Logger/
│
├── Arduino/Interieur/Interieur.ino      # Arduino code for microcontroller
│
├── Interieur/
│   ├── DATA/data.csv                    # Collected data (CSV)
│   ├── SERVER/                          # Python backend (API, management, storage…)
│   └── WEB/                             # Web interface (HTML, CSS, JS, icons…)
│
├── .env                                 # Configuration (environment variables)
├── LICENSE                              # MIT License
├── README.md                             # This file
```

---

## **Main Features**

* Automatic temperature & humidity readings (DHT22)
* Wi-Fi data transmission to a central server
* Data storage in CSV files
* Responsive web interface (graphs, history, CSV/Excel export)
* **Graphical history of temperature and humidity**
* Authentication, user management, GDPR compliance
* **Google Authenticator 2FA support**
* Alerts & water restrictions
* Home Assistant & OpenWeatherMap integration

**General Architecture:**

```
[DHT22 Sensor] --(ESP32/ESP8266 via Wi-Fi)--> [Python Server] --(CSV/MySQL)--> [Web Interface]
```

---

## **Software Installation**

### 1. Required hardware

* 1 ESP32 or ESP8266 microcontroller
* 1 DHT22 sensor
* Stable Wi-Fi connection
* Computer or server to host Python backend

### 2. Microcontroller setup

* Open `Arduino/Interieur/Interieur.ino` in Arduino IDE
* Set Wi-Fi credentials:

```cpp
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
```

* Set server address:

```cpp
const char* serverAddress = "SERVER_IP";
```

* Upload the code

### 3. Python server installation

* Install Python 3.8+
* Clone or download the repository
* Install dependencies:

```bash
pip install -r requirements.txt
```

* Configure `.env` file:

```
FLASK_SECRET_KEY=...
MAIL_USERNAME=...
MAIL_PASSWORD=...
SERVER_ADDRESS=0.0.0.0
SERVER_PORT=10000
MYSQL_HOST=...
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...
OPENWEATHER_API_KEY=...
HOME_ASSISTANT_TOKEN=...
HOME_ASSISTANT_URL=...
```

* Edit `Interieur/SERVER/config.py` for project path:

```python
BASE_DIR = "/home/pi/Desktop/DHT-Logger/Interieur"
```

### 4. Start the server

```bash
python Interieur/SERVER/server.py
```

* Server listens by default on port `10000`

### 5. Access the web interface

* Open browser: `http://localhost:10000` or `http://SERVER_IP:10000`
* View real-time data, history, export CSV/Excel, etc.

---

## **Usage**

* Data sent every minute by ESP32
* Stored in `Interieur/DATA/data.csv`
* Web interface features:

  * Real-time temperature & humidity
  * Interactive graphs
  * Export CSV/Excel
  * History browsing
  * Water alerts
  * Email notifications every 30 min if thresholds exceeded
  * User account management
  * GDPR compliance

---

## ⚠️ Configuration to adapt 

Make sure to check and adapt some JavaScript (`js/`) and Python (`SERVER/`) files: certain fields, variable names, or the city may need modification to match **your project** or **your location**.

### Example files/lines to edit:

* `Interieur/WEB/js/alerte.js`: line 1 (department/region)
* `Interieur/WEB/js/index.js`: line 267 (city or postal code)
* `Interieur/SERVER/api.py`: line 51 (city or API parameters)
* `Interieur/SERVER/config.py`: line 3 (project path or configuration)

---

## **Security & GDPR**

* Personal data is protected and never shared
* Users can request access, correction, or deletion via GDPR page

---

## **License**

MIT License. See `LICENSE`

---

## **Support & Contact**

For questions, suggestions, or bugs, open a GitHub issue.

---

# **VERSION FRANÇAISE**

> Compatible Home Assistant : Ce projet peut s’intégrer facilement à Home Assistant pour une domotique avancée.

DHT-Logger est une solution complète pour surveiller, enregistrer et visualiser la température et l’humidité via un capteur DHT22, un microcontrôleur (ESP32/ESP8266) et un serveur web Python. L’interface est moderne, avec stockage des données SQL, export, alertes et gestion des utilisateurs.

---

## 🔧 **Matériel requis**

* 🖥️ Raspberry Pi 4 ou 5
* 🔌 ESP32 Nano
* 🌡️ Capteur DHT22
* 🧵 Fils de connexion
* 🏠 Boîtier étanche (pour l’extérieur)
* 📡 Connexion Wi-Fi ou Ethernet

---

## 🛠️ **Schéma de connexion**

| DHT22 | ESP32 Nano        |
| ----- | ----------------- |
| VCC   | 3.3V              |
| DATA  | D4 (PIN DIGITAL4) |
| GND   | GND               |

---

## 🚀 **Installation & Configuration**

### 1️⃣ **Programmer l’ESP32**

* Télécharger l’IDE Arduino : [📥 Arduino IDE](https://www.arduino.cc/en/software)
* Configurer l’ESP32-S3-Box :

  * Si non visible, ajouter cette URL dans *Fichier → Préférences → URL de gestionnaire de cartes supplémentaires* :

    ```
    http://arduino.esp8266.com/stable/package_esp8266com_index.json
    ```
  * Choisir le bon port COM et la bonne architecture.
* Ajouter les bibliothèques :

  * DHT sensor library (`DHT.h`)
  * ESP32 WiFi library (`WiFi.h`)
* Modifier le code pour :

  * 📶 SSID et mot de passe Wi-Fi
  * 🌍 IP et port du serveur

### 2️⃣ **Installer Raspberry Pi OS (ou Ubuntu)**

* Télécharger Raspberry Pi Imager : [📥 Raspberry Pi Imager](https://www.raspberrypi.com/software/)
* Flasher une image 64-bit
* Configurer SSH et Wi-Fi avant le premier démarrage

### 3️⃣ **Déployer le serveur DHT-Logger**

* Copier le dossier `DHT-LOGGER-main` sur le bureau
* Créer le dossier `DHTLOGGER` et y extraire le zip
* Modifier `server.py` pour définir IP et port

### 4️⃣ **Automatiser le démarrage avec systemd ⚙️**

```bash
sudo nano /etc/systemd/system/dhtlogger.service
```

Ajouter :

```ini
[Unit]
Description=Serveur DHT Logger
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/Interieur/SERVER/server.py
WorkingDirectory=/home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/Interieur/SERVER
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Puis :

```bash
sudo systemctl daemon-reload
sudo systemctl enable dhtlogger
sudo systemctl restart dhtlogger
sudo systemctl status dhtlogger
```

Faire de même pour le service mail si nécessaire.

---

## **Structure du projet**

```
DHT-Logger/
│
├── Arduino/Interieur/Interieur.ino      # Code Arduino pour ESP32
│
├── Interieur/
│   ├── DATA/data.csv                    # Données collectées (CSV)
│   ├── SERVER/                          # Backend Python
│   └── WEB/                             # Interface web
│
├── .env                                 # Variables d’environnement
├── LICENSE                              # Licence MIT
├── README.md                             # Ce fichier
```

---

## **Fonctionnalités principales**

* Lecture automatique température & humidité (DHT22)
* Transmission Wi-Fi vers serveur central
* Stockage des mesures CSV
* Interface web responsive
* **Historique graphique de la température et de l’humidité**
* Gestion utilisateur et RGPD
* **Support Google Authenticator (2FA)**
* Alertes & restrictions d’eau
* Intégration Home Assistant & OpenWeatherMap

**Schéma général :**

```
[Capteur DHT22] --(ESP32/ESP8266 via Wi-Fi)--> [Serveur Python] --(CSV/MySQL)--> [Interface Web]
```

---

## **Installation logicielle**

### 1. Matériel

* ESP32 ou ESP8266
* Capteur DHT22
* Connexion Wi-Fi stable
* Serveur/ordinateur pour le backend Python

### 2. Configuration microcontrôleur

* Ouvrir `Arduino/Interieur/Interieur.ino`
* Paramètres Wi-Fi :

```cpp
const char* ssid = "VOTRE_SSID";
const char* password = "VOTRE_MDP";
```

* Adresse serveur :

```cpp
const char* serverAddress = "ADRESSE_SERVEUR";
```

* Téléverser le code

### 3. Installation serveur Python

* Installer Python 3.8+
* Cloner/dézipper le projet
* Installer dépendances :

```bash
pip install -r requirements.txt
```

* Configurer `.env`

* Modifier `Interieur/SERVER/config.py` pour chemin absolu :

```python
BASE_DIR = "/home/pi/Desktop/DHT-Logger/Interieur"
```

### 4. Lancer le serveur

```bash
python Interieur/SERVER/server.py
```

* Port par défaut : `10000`

### 5. Accéder à l’interface web

* Browser : `http://localhost:10000` ou `http://IP_SERVEUR:10000`
* Visualiser données, historiques, export CSV/Excel

---

## **Utilisation**

* Données envoyées chaque minute
* Stockées dans `Interieur/DATA/data.csv`
* Interface web :

  * Température & humidité en temps réel
  * Graphiques interactifs
  * Export CSV/Excel
  * Historique
  * Alertes d’eau
  * Notifications email toutes les 30 min
  * Gestion des comptes
  * RGPD

---

## ⚠️ Configuration à adapter 

Pensez à vérifier et adapter certains fichiers JavaScript (`js/`) et Python (`SERVER/`) : certains champs, noms de variables ou la ville peuvent nécessiter une modification pour correspondre à **votre projet** ou **votre localisation**.

### Exemple de fichiers/lignes à modifier :

* `Interieur/WEB/js/alerte.js` : ligne 1 (département)
* `Interieur/WEB/js/index.js` : ligne 267 (ville ou code postal)
* `Interieur/SERVER/api.py` : ligne 51 (ville ou paramètres API)
* `Interieur/SERVER/config.py` : ligne 3 (chemin du projet ou configuration)

---

## **Sécurité & RGPD**

* Données personnelles protégées
* Droits d’accès, rectification et suppression via page RGPD

---

## **Licence**

MIT License. Voir `LICENSE`

---

## **Aide & Contact**

Pour questions, suggestions ou bugs, ouvrir une issue sur GitHub.


