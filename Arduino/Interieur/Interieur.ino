#include <WiFi.h>
#include "DHT.h"

// Configuration du WiFi
const char* ssid = "SSID"; // Remplacez par votre SSID
const char* password = "PASSWORD"; // Remplacez par votre mot de passe

// Adresse IP et port du serveur
const char* serverAddress = "SERVER_ADDRESS"; // Remplacez par l'adresse de votre serveur
const uint16_t serverPort = 10000;

// Capteur DHT
#define NANO_ID "Interieur"
#define DHTPIN 7
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Chrono pour redémarrage toutes les 24h
unsigned long restartInterval = 86400000; // 24h = 86 400 000 ms
unsigned long startMillis;

void connectToWiFi() {
  Serial.print("Connexion au WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnecté au WiFi !");
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectToWiFi();
  startMillis = millis(); // Enregistrer l'heure de démarrage
}

void loop() {
  // Redémarrage automatique après 24h
  if (millis() - startMillis >= restartInterval) {
    Serial.println("Redémarrage automatique après 24h...");
    delay(1000); // petite pause pour le message
    ESP.restart();
  }

  // Vérifier connexion WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi déconnecté. Reconnexion...");
    connectToWiFi();
  }

  // Lecture DHT
  float temperature = dht.readTemperature() - 0.5;
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Erreur de lecture du capteur DHT!");
    delay(2000);
    return;
  }

  String data = "ID:" + String(NANO_ID) + " Temperature:" + String(temperature) + "C Humidity:" + String(humidity) + "%";

  // Connexion serveur (répétée jusqu'à succès)
  WiFiClient client;
  while (!client.connect(serverAddress, serverPort)) {
    Serial.println("Connexion au serveur échouée ! Nouvelle tentative dans 5 secondes...");
    delay(5000);
  }

  Serial.println("Envoi des données au serveur : " + data);
  client.println(data);
  delay(100);
  client.stop();

  delay(60000); // Pause 1 min
}
