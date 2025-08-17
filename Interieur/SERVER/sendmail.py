import os
from dotenv import load_dotenv
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from db import get_mysql_connection
import mysql.connector
load_dotenv()

DB_FILE = os.environ.get("DB_FILE")
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

LAST_ALERT_FILE = "/tmp/last_alert_sent.timestamp"
ALERT_DELAY_SECONDS = 1800  # 30 minutes de délai entre envois 1800
LOGO_URL = os.environ.get("LOGO_URL")

def init_last_alert_file():
    """
    Crée le fichier last_alert_sent.timestamp avec une valeur initiale (0) 
    s'il n'existe pas.
    """
    if not os.path.exists(LAST_ALERT_FILE):
        try:
            with open(LAST_ALERT_FILE, "w") as f:
                f.write("0")
            print(f"[INFO] Fichier {LAST_ALERT_FILE} créé avec valeur initiale 0")
        except Exception as e:
            print(f"[ERREUR] Création du fichier {LAST_ALERT_FILE} : {e}")

# Fonction pour lire le timestamp de la dernière alerte

def read_last_alert_time():
    """
    Lit le timestamp depuis le fichier. Retourne float.
    Si problème, retourne 0.
    """
    try:
        with open(LAST_ALERT_FILE, "r") as f:
            return float(f.read().strip())
    except Exception as e:
        print(f"[ERREUR] Lecture du fichier {LAST_ALERT_FILE} : {e}")
        return 0


# Exemple d'utilisation :
init_last_alert_file()               # Crée le fichier au démarrage si besoin
last_time = read_last_alert_time()   # Lit la dernière alerte
print(f"Dernière alerte envoyée à : {last_time}")


# Fonction pour enregistrer une action d'administration dans la base de données

def log_admin_action(admin_username, action, target=None):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admin_logs (admin_username, action, target, timestamp) VALUES (%s, %s, %s, %s)",
            (admin_username, action, target, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

# Fonction pour envoyer un email

def sendmail(destinataire, sujet, contenu_texte, contenu_html=None):
    """
    Envoie un email simple ou multipart (texte + HTML).
    - destinataire : str ou list d'emails
    - sujet : sujet du mail
    - contenu_texte : version texte brut
    - contenu_html : version HTML (optionnelle)
    """
    if isinstance(destinataire, str):
        destinataires = [destinataire]
    else:
        destinataires = destinataire

    message = MIMEMultipart("alternative")
    message["From"] = MAIL_USERNAME
    message["To"] = ", ".join(destinataires)
    message["Subject"] = sujet

    # Partie texte obligatoire
    message.attach(MIMEText(contenu_texte, "plain"))
    # Partie HTML optionnelle
    if contenu_html:
        message.attach(MIMEText(contenu_html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, destinataires, message.as_string())
        print(f"[INFO] Email envoyé à : {destinataires}")
        # LOG ICI
        log_admin_action("SYSTEM", f"envoi mail : {sujet}", str(destinataires))
        return True
    except Exception as e:
        print(f"[ERREUR] Envoi email : {e}")
        return False
    
# Fonction pour envoyer un email d'alerte

def send_alert_email(temperature, temp_min, temp_max, humidity, humidity_min, humidity_max):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email IS NOT NULL AND email != ''")
        recipients = [row[0] for row in cursor.fetchall()]

    if not recipients:
        print("[INFO] Aucun destinataire email trouvé.")
        return False, "Pas d'emails configurés"

    subject = "⚠️ Alerte seuil dépassé ! ⚠️"
    image_url = "https://cdn-icons-png.flaticon.com/512/564/564619.png"
    logo_url = LOGO_URL

    html = f"""
    <html>
    <body style="font-family:'Segoe UI',Roboto,sans-serif;background-color:#f4f4f4;margin:0;padding:0;">
        <div style="max-width:600px;margin:30px auto;background:white;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);overflow:hidden;">
            <div style="background:#d93025;padding:24px 0;text-align:center;">
                <img src="{logo_url}" alt="Logo" style="max-height:40px;max-width:120px;margin-bottom:20px;">
                <h1 style="color:white;margin:0;font-size:2em;">Alerte seuil dépassé !</h1>
            </div>
            <div style="padding:32px 24px 24px 24px;">
                <p style="font-size:17px;color:#333;">Bonjour,</p>
                <p style="font-size:16px;color:#555;">
                    <b>Un seuil de température ou d'humidité a été dépassé :</b>
                </p>
                <table style="width:100%;border-collapse:collapse;margin:20px 0;">
                    <thead>
                        <tr>
                            <th style="background:#d93025;color:white;padding:10px;border-radius:5px 5px 0 0;">Mesure</th>
                            <th style="background:#d93025;color:white;padding:10px;">Valeur</th>
                            <th style="background:#d93025;color:white;padding:10px;">Min autorisé</th>
                            <th style="background:#d93025;color:white;padding:10px;border-radius:0 0 5px 5px;">Max autorisé</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:10px;text-align:center;">🌡️ Température (°C)</td>
                            <td style="padding:10px;text-align:center;">{temperature}</td>
                            <td style="padding:10px;text-align:center;">{temp_min}</td>
                            <td style="padding:10px;text-align:center;">{temp_max}</td>
                        </tr>
                        <tr>
                            <td style="padding:10px;text-align:center;">💧 Humidité (%)</td>
                            <td style="padding:10px;text-align:center;">{humidity}</td>
                            <td style="padding:10px;text-align:center;">{humidity_min}</td>
                            <td style="padding:10px;text-align:center;">{humidity_max}</td>
                        </tr>
                    </tbody>
                </table>
                <p style="color:#d93025;font-weight:bold;font-size:16px;text-align:center;">
                    Merci de vérifier rapidement votre installation !
                </p>
            </div>
            <div style="background:#f1f1f1;padding:12px;text-align:center;color:#888;font-size:13px;">
                © 2025 Système de Surveillance - Alerte automatique
            </div>
        </div>
    </body>
    </html>
    """

    text = (
        f"Alerte seuil dépassé !\n\n"
        f"Température : {temperature}°C (min {temp_min} / max {temp_max})\n"
        f"Humidité : {humidity}% (min {humidity_min} / max {humidity_max})\n"
    )

    if sendmail(recipients, subject, text, html):
        return True, "Email envoyé avec succès"
    else:
        return False, "Échec de l'envoi de l'email"
    
# Fonction pour envoyer un email de réinitialisation de mot de passe

def send_password_reset_email(email, username, token, server_address):
    reset_url = f"https://{server_address}/reset_password?token={token}"
    logo_url = LOGO_URL
    subject = "Réinitialisation de votre mot de passe"
    body_text = (
        f"Bonjour {username},\n\n"
        f"Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_url}\n\n"
        "Si vous n'avez pas demandé cette opération, ignorez ce mail."
    )
    body_html = f"""
    <html>
    <body style="font-family:'Segoe UI',Roboto,sans-serif;background-color:#f9f9f9;margin:0;padding:40px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:8px;padding:30px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="text-align:center;">
                <img src="{logo_url}" alt="Logo" style="max-height:40px;max-width:120px;margin-bottom:20px;">
            </div>
            <h2 style="color:#333;">Bonjour {username},</h2>
            <p style="font-size:16px;color:#555;">
                Nous avons reçu une demande de réinitialisation de votre mot de passe. Pour continuer, cliquez sur le bouton ci-dessous :
            </p>
            <p style="text-align:center;margin:30px 0;">
                <a href="{reset_url}" style="background:#d93025;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-size:16px;display:inline-block;">
                    Réinitialiser mon mot de passe
                </a>
            </p>
            <p style="font-size:14px;color:#999;">
                Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.
            </p>
            <hr style="margin:30px 0;border:0;border-top:1px solid #eee;">
            <p style="font-size:12px;color:#aaa;text-align:center;">
                © 2025 DHT Logger - Tous droits réservés.
            </p>
        </div>
    </body>
    </html>
    """
    return sendmail(email, subject, body_text, body_html)



def send_verification_email(email, username, token, server_address):
    confirm_url = f"https://{server_address}/verify_email?token={token}"
    logo_url = LOGO_URL
    subject = "🛡️ Vérification de votre adresse email"

    body_text = (
        f"Bonjour {username},\n\n"
        f"Cliquez sur ce lien pour vérifier votre adresse email : {confirm_url}\n\n"
        "Merci."
    )

    body_html = f"""
    <html>
    <body style="font-family:'Segoe UI',Roboto,sans-serif;background-color:#f9f9f9;margin:0;padding:40px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:8px;padding:30px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="text-align:center;">
                <img src="{logo_url}" alt="Logo" style="max-height:40px;max-width:120px;margin-bottom:20px;">
            </div>
            <h2 style="color:#333;">Bonjour {username},</h2>
            <p style="font-size:16px;color:#555;">
                Pour finaliser votre inscription, veuillez vérifier votre adresse email en cliquant sur le bouton ci-dessous :
            </p>
            <p style="text-align:center;margin:30px 0;">
                <a href="{confirm_url}" style="background:#1a73e8;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-size:16px;display:inline-block;">
                    Vérifier mon adresse
                </a>
            </p>
            <p style="font-size:14px;color:#999;">
                Si vous n'avez pas demandé ce message, vous pouvez ignorer cet email.
            </p>
            <hr style="margin:30px 0;border:0;border-top:1px solid #eee;">
            <p style="font-size:12px;color:#aaa;text-align:center;">
                © 2025 DHT Logger - Tous droits réservés.
            </p>
        </div>
    </body>
    </html>
    """

    result = sendmail(email, subject, body_text, body_html)
    if result:
        return True, "Email envoyé avec succès"
    else:
        return False, "Échec de l'envoi du mail"
    
# Fonction pour envoyer un email de confirmation de suppression de compte        

def send_delete_account_email(email, username, confirm_url):
    # Utilise le même logo que pour les autres mails
    # Adapte le chemin si besoin
    server_address = os.environ.get("SERVER_ADDRESS", "localhost")
    logo_url = LOGO_URL
    subject = "Confirmation de suppression de votre compte"
    body_text = f"""Bonjour {username},

Cliquez sur ce lien pour confirmer la suppression de votre compte :
{confirm_url}

Si vous n'êtes pas à l'origine de cette demande, ignorez ce mail."""
    body_html = f"""
    <html>
    <body style="font-family:'Segoe UI',Roboto,sans-serif;background-color:#f9f9f9;margin:0;padding:40px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:8px;padding:30px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="text-align:center;">
                <img src="{logo_url}" alt="Logo" style="max-height:40px;max-width:120px;margin-bottom:20px;">
            </div>
            <h2 style="color:#d93025;">Suppression de votre compte</h2>
            <p style="font-size:16px;color:#555;">
                Bonjour {username},<br>
                Cliquez sur le bouton ci-dessous pour confirmer la suppression de votre compte :
            </p>
            <p style="text-align:center;margin:30px 0;">
                <a href="{confirm_url}" style="background:#d93025;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-size:16px;display:inline-block;">
                    Confirmer la suppression
                </a>
            </p>
            <p style="font-size:14px;color:#999;">
                Si vous n'êtes pas à l'origine de cette demande, ignorez ce mail.
            </p>
            <hr style="margin:30px 0;border:0;border-top:1px solid #eee;">
            <p style="font-size:12px;color:#aaa;text-align:center;">
                © 2025 DHT Logger - Tous droits réservés.
            </p>
        </div>
    </body>
    </html>
    """
    return sendmail(email, subject, body_text, body_html)

# Fonction pour envoyer un email de confirmation de changement d'adresse email

def send_email_change_confirmation(email, username, confirm_url):
    from os import environ
    logo_url = environ.get("LOGO_URL", "")
    subject = "Confirmation de changement d'adresse email"
    body_text = f"""Bonjour {username},

Cliquez sur ce lien pour confirmer votre nouvelle adresse email :
{confirm_url}

Si vous n'êtes pas à l'origine de cette demande, ignorez ce mail."""
    body_html = f"""
    <html>
    <body style="font-family:'Segoe UI',Roboto,sans-serif;background-color:#f9f9f9;margin:0;padding:40px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:8px;padding:30px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="text-align:center;">
                <img src="{logo_url}" alt="Logo" style="max-height:40px;max-width:120px;margin-bottom:20px;">
            </div>
            <h2 style="color:#333;">Confirmation de changement d'adresse email</h2>
            <p style="font-size:16px;color:#555;">
                Bonjour {username},<br>
                Cliquez sur le bouton ci-dessous pour confirmer votre nouvelle adresse email :
            </p>
            <p style="text-align:center;margin:30px 0;">
                <a href="{confirm_url}" style="background:#388e3c;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-size:16px;display:inline-block;">
                    Confirmer mon nouvel email
                </a>
            </p>
            <p style="font-size:14px;color:#999;">
                Si vous n'êtes pas à l'origine de cette demande, ignorez ce mail.
            </p>
            <hr style="margin:30px 0;border:0;border-top:1px solid #eee;">
            <p style="font-size:12px;color:#aaa;text-align:center;">
                © 2025 DHT Logger - Tous droits réservés.
            </p>
        </div>
    </body>
    </html>
    """
    return sendmail(email, subject, body_text, body_html)

# Fonction pour vérifier si on peut envoyer une alerte

def can_send_alert():
    try:
        if not os.path.exists(LAST_ALERT_FILE):
            print(f"[DEBUG] Aucun fichier {LAST_ALERT_FILE} → Envoi autorisé")
            return True

        with open(LAST_ALERT_FILE, "r") as f:
            last_sent = float(f.read().strip())
        elapsed = time.time() - last_sent
        print(f"[DEBUG] Dernière alerte il y a {elapsed:.0f} sec → Autorisé : {elapsed > ALERT_DELAY_SECONDS}")
        return elapsed > ALERT_DELAY_SECONDS

    except Exception as e:
        print(f"[ERREUR] Lecture fichier délai : {e}")
        return True  # mieux vaut prévenir trop que jamais
    
# Fonction pour mettre à jour le fichier avec le timestamp actuel

def update_last_alert_time():
    try:
        now = str(time.time())
        with open(LAST_ALERT_FILE, "w") as f:
            f.write(now)
        print(f"[DEBUG] Alerte enregistrée à : {now} → fichier {LAST_ALERT_FILE}")
    except Exception as e:
        print(f"[ERREUR] Écriture fichier délai : {e}")


 # Fonction principale pour vérifier les seuils et envoyer des alertes       

def check_and_send_alert():
    try:
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT temp_min, temp_max, humidity_min, humidity_max FROM alert_config WHERE id=%s", (1,))
            alert_conf = cursor.fetchone()
            if not alert_conf:
                print("[WARN] Config alerte introuvable")
                return

            temp_min, temp_max, humidity_min, humidity_max = alert_conf

            cursor.execute("SELECT device_id, temperature, humidity, time FROM measurements ORDER BY time DESC LIMIT 1")
            last_measure = cursor.fetchone()

        if not last_measure:
            print("[WARN] Aucune mesure trouvée")
            return

        device_id, temperature, humidity, measure_time = last_measure
        print(f"[DEBUG] Mesure → Température: {temperature}, Humidité: {humidity}")
        print(f"[DEBUG] Seuils → Temp: {temp_min}-{temp_max}, Hum: {humidity_min}-{humidity_max}")

        alert = (
            temperature < temp_min or temperature > temp_max or
            humidity < humidity_min or humidity > humidity_max
        )

        if alert:
            print("[DEBUG] Seuil dépassé → alerte requise")
            if can_send_alert():
                success, msg = send_alert_email(temperature, temp_min, temp_max, humidity, humidity_min, humidity_max)
                if success:
                    print("[INFO]", msg)
                    update_last_alert_time()
                else:
                    print("[ERREUR]", msg)
            else:
                print("[INFO] Délai entre alertes non expiré")
        else:
            print("[DEBUG] Aucun dépassement de seuil")
    except Exception as e:
        print(f"[ERREUR] check_and_send_alert: {e}")


if __name__ == "__main__":
    while True:
        check_and_send_alert()
        time.sleep(60)  # vérifie toutes les minutes
    