


# DHT-LOGGER

> Compatible Home Assistant : Ce projet peut s'intégrer facilement à Home Assistant pour une domotique avancée.

DHT-Logger est une solution complète pour surveiller, enregistrer et visualiser la température et l’humidité à l’aide d’un capteur DHT22, d’un microcontrôleur (ESP32/ESP8266) et d’un serveur web Python. Le projet propose une interface web moderne, un stockage des données, des exports, des alertes et une gestion utilisateur.

---

## 🔧 Matériel requis

- 🖥️ Raspberry Pi 4 ou 5
- 🔌 ESP32 Nano
- 🌡️ Capteur DHT22
- 🧵 Fils de connexion
- 🏠 Boîtier étanche (si le capteur est installé en extérieur)
- 📡 Connexion Wi-Fi ou Ethernet

## 🛠️ Schéma de connexion

Pour connecter le capteur DHT22 à l'ESP32 Nano :

| DHT22 | ESP32 Nano |
|-------|------------|
| VCC   | 3.3V       |
| DATA  | D4 (PIN DIGITAL4) |
| GND   | GND        |

---

## 🚀 Installation et configuration

### 1️⃣ Programmer l'ESP32

- Télécharger et installer l'IDE Arduino : [📥 Lien de téléchargement](https://www.arduino.cc/en/software)
- Configurer l'ESP32-S3-Box :
	- Si l'ESP32-S3-Box n'apparaît pas, ajoutez ce lien dans Fichier -> Préférences -> URL de gestionnaire de cartes supplémentaires :
		`http://arduino.esp8266.com/stable/package_esp8266com_index.json`
	- Sélectionnez le bon port COM et la bonne architecture.
- Ajouter les bibliothèques nécessaires dans l'IDE Arduino (Outils -> Gestionnaire de Bibliothèques) :
	- DHT sensor library (`DHT.h`)
	- ESP32 WiFi library (`WiFi.h`)
- Téléverser le code en modifiant les paramètres suivants :
	- 📶 SSID et mot de passe Wi-Fi
	- 🌍 Adresse IP et Port du serveur

### 2️⃣ Installer l'OS Raspberry Pi (ou Ubuntu)

- Télécharger et installer Raspberry Pi Imager : [📥 Lien de téléchargement](https://www.raspberrypi.com/software/)
- (Vous pouvez aussi utiliser Ubuntu ou tout système Linux compatible pour héberger le serveur.)
- Flasher la carte SD avec l'OS Raspberry Pi 64 bits avec interface
- Configurer le SSH et le Wi-Fi avant l'installation pour éviter des manipulations ultérieures

### 3️⃣ Déployer le serveur DHT-Logger

- 📂 Copier le dossier DHT-LOGGER-main sur le bureau
- 📁 Créer un dossier DHTLOGGER et y extraire le fichier .zip
- ✏️ Modifier `server.py` pour définir l’IP et le port du serveur

### 4️⃣ Automatiser le lancement du serveur au démarrage ⚙️

Créer un service systemd pour démarrer automatiquement le serveur :

```ini
sudo nano /etc/systemd/system/dhtlogger.service
```
Ajouter le contenu suivant :

```ini
[Unit]
Description=Serveur DHT Logger
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/(Interieur ou Exterieur)/SERVER/server.py
WorkingDirectory=/home/pi/Desktop/DHTLOGGER/DHT-LOGGER-main/Interieur/SERVER
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

💾 Sauvegarder avec CTRL + X, puis Y et Entrée.

Ensuite, rechargez la configuration systemd et activez le service au démarrage avec les commandes suivantes :

```bash
sudo systemctl daemon-reload
sudo systemctl enable dhtlogger
sudo systemctl restart dhtlogger
sudo systemctl status dhtlogger
```

Faites la même chose pour le service mail (`dhtloggermailinterieur.service`) si vous souhaitez automatiser l'envoi des alertes par email.

```



---

## Structure du projet

```
DHT-Logger/
│
├── Arduino/Interieur/Interieur.ino      # Code Arduino pour le microcontrôleur
│
├── Interieur/
│   ├── DATA/data.csv                    # Données collectées (CSV)
│   ├── SERVER/                          # Backend Python (API, gestion, sauvegarde…)
│   └── WEB/                             # Interface web (HTML, CSS, JS, icônes…)
│
├── .env                                 # Configuration (variables d’environnement)
├── LICENSE                              # Licence MIT
├── README.md                            # Ce fichier

```


## Fonctionnalités principales

- Lecture automatique de la température et de l’humidité (DHT22)
- Transmission WiFi vers un serveur central
- Stockage des mesures dans un fichier CSV
- Interface web responsive (graphiques, historique, export CSV/Excel)
- Authentification, gestion de compte, RGPD
- Alertes et restrictions d’eau
- Intégration possible avec Home Assistant et OpenWeatherMap

## Schéma général

```
[Capteur DHT22] --(ESP32/ESP8266 via WiFi)--> [Serveur Python] --(CSV/MySQL)--> [Interface Web]
```

---

## Installation logicielle

### 1. Matériel nécessaire

- 1 microcontrôleur ESP32 ou ESP8266
- 1 capteur DHT22 (température/humidité)
- Connexion WiFi stable
- Un ordinateur ou serveur pour héberger le backend Python

### 2. Configuration du microcontrôleur

- Ouvre `Arduino/Interieur/Interieur.ino` dans l’IDE Arduino.
- Renseigne le SSID et le mot de passe WiFi :
	```cpp
	const char* ssid = "VOTRE_SSID";
	const char* password = "VOTRE_MDP";
	```
- Renseigne l’adresse IP ou le nom de domaine du serveur Python :
	```cpp
	const char* serverAddress = "ADRESSE_DU_SERVEUR";
	```
- Téléverse le code sur ton ESP32/ESP8266.

### 3. Installation du serveur Python

- Installe Python 3.8+ sur ton ordinateur/serveur.
- Clone ce dépôt ou télécharge-le.
- Installe les dépendances nécessaires :
	```bash
	pip install -r requirements.txt
	```
- Configure le fichier `.env` à la racine :
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
- Modifie `Interieur/SERVER/config.py` pour indiquer le chemin absolu de ton projet :
	```python
	BASE_DIR = "C:/chemin/vers/DHT-Logger/Interieur"
	```

### 4. Lancement du serveur

- Lance le serveur Python :
	```bash
	python Interieur/SERVER/server.py
	```
- Le serveur écoute par défaut sur le port 10000.

### 5. Accès à l’interface web

- Ouvre un navigateur et rends-toi à l’adresse du serveur (ex : http://localhost:10000 ou http://ADRESSE_IP:10000).
- Profite de l’interface pour visualiser les données, exporter les fichiers, consulter l’historique, etc.

---

## Utilisation

- Les mesures sont envoyées automatiquement toutes les minutes par le microcontrôleur.
- Les données sont stockées dans `Interieur/DATA/data.csv`.
- L’interface web permet de :
	- Voir la température et l’humidité en temps réel.
	- Afficher des graphiques interactifs.
	- Télécharger les données au format CSV ou Excel.
	- Consulter l’historique par période.
	- Recevoir des alertes en cas de restrictions d’eau.
	- Recevoir des alertes par mail toutes les 30 minutes si un seuil est dépassé.
	- Gérer son compte utilisateur (connexion, inscription, mot de passe oublié…).
	- Consulter la politique de confidentialité (RGPD).

---

## Personnalisation

- Pour changer la ville ou le code postal de la météo externe, modifie la configuration dans le backend.
- Pour ajouter d’autres capteurs, duplique et adapte le code Arduino et la gestion côté serveur.
- Pour activer l’intégration Home Assistant ou OpenWeatherMap, renseigne les clés API dans `.env`.
 - ⚠️ Pensez à vérifier et adapter tous les fichiers JavaScript (`js/`) et Python (`SERVER/`) : certains champs, noms de variables, ou la ville peuvent nécessiter une modification pour correspondre à votre projet ou votre localisation.

	- Exemple de fichiers/lignes à modifier :
		- `Interieur/WEB/js/alerte.js` : ligne 1 (département)
		- `Interieur/WEB/js/index.js` : ligne 267 (ville ou code postal)
		- `Interieur/SERVER/api.py` : ligne 51 (ville ou paramètres API)
		- `Interieur/SERVER/config.py` : ligne 3 (chemin du projet ou configuration)

---

## Sécurité & RGPD

- Les données personnelles sont protégées et ne sont jamais transmises à des tiers.
- Vous pouvez exercer vos droits (accès, rectification, suppression…) en contactant l’administrateur (voir page RGPD).

---

## Licence

Projet sous licence MIT. Voir le fichier `LICENSE`.

---

## Aide & contact

Pour toute question, suggestion ou bug, ouvre une issue sur GitHub ou contacte l’administrateur à l’adresse indiquée dans la page RGPD.
