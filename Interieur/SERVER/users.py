from flask import (
    render_template, request, redirect, url_for, session, flash, Blueprint, send_file, current_app, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_mysql_connection
from sendmail import send_verification_email, send_password_reset_email, send_delete_account_email, send_email_change_confirmation
from auth import login_required
import time
import secrets
from datetime import datetime
import mysql.connector
import pyotp
import io
import csv
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import qrcode
from config import SERVER_ADDRESS
from limiter_config import limiter
import logging


users_bp = Blueprint('users', __name__)

# ========== UTILS ==========
def is_strong_password(password):
    # Minimum 8 caractères, au moins 1 chiffre et 1 lettre
    if len(password) < 8:
        return False
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    return has_digit and has_letter

def generate_email_token():
    return secrets.token_urlsafe(32)

def generate_reset_token():
    return secrets.token_urlsafe(32)

def is_admin(username):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
    return user and user[0] == 1

def log_admin_action(admin_username, action, target=None):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO admin_logs (admin_username, action, target, timestamp) VALUES (%s, %s, %s, %s)",
            (admin_username, action, target, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

# ========== INSCRIPTION ==========
@users_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        if not username or not password or not email:
            return render_template("register.html", error="Tous les champs sont obligatoires.")
        if not is_strong_password(password):
            return render_template("register.html", error="Mot de passe trop faible. Il doit contenir au moins 8 caractères, une lettre et un chiffre.")
        token = generate_email_token()
        hashed = generate_password_hash(password)
        try:
            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, email, email_verified, email_token, creation_date, last_login) VALUES (%s, %s, %s, 0, %s, %s, %s)",
                    (username, hashed, email, token, datetime.now().strftime("%Y-%m-%d"), "")
                )
                conn.commit()
            send_verification_email(email, username, token, SERVER_ADDRESS)
            return render_template("register.html", message="Inscription réussie ! Un mail de vérification a été envoyé à votre adresse. Vérifiez-la puis connectez-vous.")
        except mysql.connector.IntegrityError:
            return render_template("register.html", error="Nom d'utilisateur déjà pris.")
        except Exception as e:
            logging.exception(e)  # Log la stack trace complète
            flash("Une erreur est survenue lors de l'inscription. Veuillez réessayer ou contacter l'administrateur.", "error")
            return render_template("register.html")  # ou "login.html" selon le contexte
    return render_template("register.html")

# ========== VÉRIFICATION EMAIL ==========
@users_bp.route("/verify_email")
def verify_email():
    token = request.args.get("token", "")
    if not token:
        return render_template("verify_email.html", error="Lien invalide")
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email_token = %s", (token,))
        user = cursor.fetchone()
        if not user:
            return render_template("verify_email.html", error="Lien invalide ou expiré")
        cursor.execute("UPDATE users SET email_verified = 1, email_token = NULL WHERE id = %s", (user[0],))
        conn.commit()
    return render_template("verify_email.html", success="Email vérifié avec succès ! Vous pouvez maintenant vous connecter.")

@users_bp.route("/resend_verification")
@login_required
def resend_verification():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return redirect(url_for("profil"))
        email = user[0]
        token = generate_email_token()
        cursor.execute("UPDATE users SET email_token = %s WHERE username = %s", (token, username))
        conn.commit()
    send_verification_email(email, username, token, SERVER_ADDRESS)
    flash("Lien de vérification renvoyé !")
    return redirect(url_for("profil"))

@users_bp.route("/resend_email", methods=["GET"])
def resend_email():
    return render_template("resend_email.html")

@users_bp.route("/resend_verification_mail", methods=["POST"])
def resend_verification_mail():
    username = request.form.get("username", "").strip()
    if not username:
        return render_template("resend_email.html", error="Veuillez entrer votre nom d'utilisateur.")
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, email_token, email_verified FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return render_template("resend_email.html", error="Utilisateur inconnu.")
        email, token, email_verified = user
        if email_verified:
            return render_template("resend_email.html", message="Votre adresse email est déjà vérifiée. Vous pouvez vous connecter.")
        last_sent = session.get("last_verif_mail", 0)
        now = time.time()
        if now - last_sent < 60:
            return render_template("resend_email.html", error="Veuillez attendre avant de renvoyer un mail de vérification.")
        send_verification_email(email, username, token, SERVER_ADDRESS)
        session["last_verif_mail"] = now
        return render_template("resend_email.html", message="Mail de vérification renvoyé ! Vérifiez votre boîte mail.")

# ========== CONNEXION ==========
@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password, email_verified, active, otp_secret FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if not user:
                    time.sleep(1)
                    return render_template("login.html", error="Identifiants invalides.", username=username)
                hashed_password, email_verified, active, otp_secret = user
                if active == 0:
                    time.sleep(1)
                    return render_template("login.html", error="Ce compte est désactivé.")
                if not email_verified:
                    last_sent = session.get("last_verif_mail", 0)
                    now = time.time()
                    can_resend = now - last_sent > 60
                    time.sleep(1)
                    return render_template("login.html",
                                           error="Votre adresse email n'est pas vérifiée.",
                                           show_resend=True, can_resend=can_resend, username=username)
                if not check_password_hash(hashed_password, password):
                    time.sleep(1)
                    return render_template("login.html", error="Identifiants invalides.", username=username)
                # Si 2FA activé, stocke l'utilisateur en session temporaire et redirige vers /2fa
                if otp_secret:
                    session["pending_2fa_user"] = username
                    return redirect(url_for("a2f"))
                session["user"] = username
                with get_mysql_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET last_login = %s WHERE username = %s", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
                    conn.commit()
                return redirect(url_for("index"))
        except Exception as e:
            logging.exception(e)
            flash("Erreur lors de la connexion. Vérifiez vos identifiants ou réessayez plus tard.", "error")
            return render_template("login.html")
    return render_template("login.html")

# ========== PANEL UTILISATEUR ==========
@users_bp.route("/panel")
@login_required
def panel():
    username = session.get("user")
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT can_access_panel FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
    if not result or result[0] != 1:
        return "Accès refusé. Permission requise pour accéder au panel.", 403
    return render_template("panel.html")

# ========== ADMIN : ACTIVER/DÉSACTIVER UN UTILISATEUR ==========
@users_bp.route("/admin/toggle_active/<int:user_id>", methods=["POST"])
def toggle_active(user_id):
    if "user" not in session or not is_admin(session["user"]):
        return redirect(url_for("login"))
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return redirect(url_for("panel_admin"))
        new_status = 0 if user[0] == 1 else 1
        cursor.execute("UPDATE users SET active = %s WHERE id = %s", (new_status, user_id))
        conn.commit()
    log_admin_action(session["user"], "désactivation/réactivation compte", f"user_id={user_id}")
    return redirect(url_for("admin_panel"))

# ========== MOT DE PASSE OUBLIÉ ==========
@users_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return render_template("forgot_password.html", error="Veuillez entrer votre adresse email.")
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return render_template("forgot_password.html", error="Aucun compte associé à cet email.")
            username = user[0]
            token = generate_reset_token()
            cursor.execute("UPDATE users SET reset_token = %s WHERE email = %s", (token, email))
            conn.commit()
        send_password_reset_email(email, username, token, SERVER_ADDRESS)
        return render_template("forgot_password.html", message="Un email de réinitialisation a été envoyé si l'adresse existe.")
    return render_template("forgot_password.html")

# ========== RÉINITIALISATION MOT DE PASSE ==========
@users_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    if not token:
        return "Lien invalide", 400
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        if not is_strong_password(new_password):
            return render_template("reset_password.html", token=token, error="Mot de passe trop faible.")
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE reset_token = %s", (token,))
            user = cursor.fetchone()
            if not user:
                return render_template("reset_password.html", token=token, error="Lien invalide ou expiré.")
            hashed = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password = %s, reset_token = NULL WHERE id = %s", (hashed, user[0]))
            conn.commit()
        return render_template("reset_password.html", message="Mot de passe réinitialisé. Vous pouvez vous connecter.")
    return render_template("reset_password.html", token=token)

@users_bp.route("/profil")
@login_required
def profil():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, otp_secret, creation_date, last_login FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
    email = user[0] if user else ""
    has_2fa = bool(user and user[1])
    creation_date = user[2] if user else ""
    last_login = user[3] if user else ""
    return render_template("profil.html",
                           username=username,
                           email=email,
                           has_2fa=has_2fa,
                           creation_date=creation_date,
                           last_login=last_login)

# ========== ACTIVATION 2FA ==========
@users_bp.route("/2fa", methods=["GET", "POST"])
def a2f():
    if "pending_2fa_user" not in session:
        return redirect(url_for("login"))
    username = session["pending_2fa_user"]
    if request.method == "POST":
        otp_code = request.form.get("otp_code", "")
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT otp_secret FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
        if user and user[0]:
            totp = pyotp.TOTP(user[0])
            if totp.verify(otp_code):
                session.pop("pending_2fa_user")
                session["user"] = username
                return redirect(url_for("index"))
        return render_template("A2F.html", error="Code 2FA invalide.")
    return render_template("A2F.html")

# ========== METTRE À JOUR EMAIL ==========

@users_bp.route("/update_email", methods=["POST"])
@login_required
def update_email():
    username = session["user"]
    new_email = request.form.get("email", "").strip()
    if not new_email:
        flash("Veuillez saisir un email.", "error")
        return redirect(url_for("profil"))
    s = URLSafeTimedSerializer(current_app.secret_key)
    token = s.dumps({"username": username, "new_email": new_email}, salt="confirm-email")
    server_address = request.host
    confirm_url = f"https://{server_address}/confirm_email_change?token={token}"
    send_email_change_confirmation(new_email, username, confirm_url)
    flash("Un email de confirmation a été envoyé à votre nouvelle adresse. Veuillez cliquer sur le lien pour valider le changement.", "info")
    return redirect(url_for("profil"))

# ========== CONFIRMER ACTIVATION 2FA ==========

@users_bp.route("/confirm_email_change")
def confirm_email_change():
    token = request.args.get("token", "")
    if not token:
        return render_template("confirm_email_change.html", error="Lien invalide ou manquant.")
    s = URLSafeTimedSerializer(current_app.secret_key)
    try:
        data = s.loads(token, salt="confirm-email", max_age=3600)
        username = data["username"]
        new_email = data["new_email"]
    except (BadSignature, SignatureExpired):
        return render_template("confirm_email_change.html", error="Lien de confirmation invalide ou expiré.")
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email=%s WHERE username=%s", (new_email, username))
        conn.commit()
    return render_template("confirm_email_change.html", success="Votre nouvelle adresse email a bien été confirmée.")

# ========== CHANGER MOT DE PASSE ==========

@users_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    username = session["user"]
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if not old_password or not new_password:
        return render_template("error.html", title="Erreur", message="Champs manquants.", redirect_url=url_for("profil"))
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user or not check_password_hash(user[0], old_password):
            return render_template("error.html", title="Erreur", message="Ancien mot de passe incorrect.", redirect_url=url_for("profil"))
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (generate_password_hash(new_password), username))
        conn.commit()
    return redirect(url_for("profil"))

# ========== ACTIVER/DÉSACTIVER 2FA ==========

@users_bp.route("/enable_2fa", methods=["GET"])
@login_required
def enable_2fa_page():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp_secret FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result and result[0]:
            # Déjà activé
            return redirect(url_for("profil"))
    # Génère un secret temporaire et stocke-le en session
    secret = pyotp.random_base32()
    session['pending_2fa_secret_user'] = secret
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
    return render_template("enable_2fa_user.html", otp_uri=otp_uri, username=username)


@users_bp.route("/disable_2fa", methods=["POST"])
@login_required
def disable_2fa():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET otp_secret = '' WHERE username = %s", (username,))
        conn.commit()
    return redirect(url_for("profil"))

# ========== TÉLÉCHARGER MES DONNÉES ==========

@users_bp.route("/download_my_data")
@login_required
def download_my_data():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, creation_date, last_login FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.execute("SELECT * FROM measurements WHERE device_id = %s", (username,))
        measurements = cursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "email", "creation_date", "last_login"])
    writer.writerow(user)
    writer.writerow([])
    # On écrit seulement les valeurs, sans les noms de colonnes
    for row in measurements:
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="mes_donnees.csv")

# ========== DEMANDER SUPPRESSION COMPTE ==========

@users_bp.route("/request_delete_account", methods=["POST"])
@login_required
def request_delete_account():
    username = session["user"]
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
    if not row or not row[1]:
        flash("Aucune adresse email trouvée pour ce compte.", "error")
        return redirect(url_for("profil"))
    user_id = row[0]
    email = row[1]
    s = URLSafeTimedSerializer(current_app.secret_key)
    token = s.dumps({"user_id": user_id}, salt="delete-account")
    confirm_url = f"https://{request.host}/confirm_delete_account?token={token}"
    result = send_delete_account_email(email, username, confirm_url)
    if result:
        flash("Un email de confirmation de suppression vous a été envoyé.", "info")
    else:
        flash("Erreur lors de l'envoi de l'email de confirmation.", "error")
    return redirect(url_for("profil"))

# ========== CONFIRMER SUPPRESSION COMPTE ==========

@users_bp.route("/confirm_delete_account")
def confirm_delete_account():
    token = request.args.get("token", "")
    if not token:
        return render_template("confirm_delete_account.html", error="Lien invalide ou manquant.")
    s = URLSafeTimedSerializer(current_app.secret_key)
    try:
        data = s.loads(token, salt="delete-account", max_age=3600)  # 1h de validité
        user_id = data["user_id"]
    except (BadSignature, SignatureExpired):
        return render_template("confirm_delete_account.html", error="Lien de confirmation invalide ou expiré.")
    # Supprime le compte
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    session.clear()
    return render_template("confirm_delete_account.html", success="Votre compte a bien été supprimé.")

# ========== STATUT UTILISATEUR ==========

@users_bp.route("/user/status")
def user_status():
    if "user" not in session:
        return jsonify({"logged_in": False})
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin, can_access_panel FROM users WHERE username = %s", (session["user"],))
        result = cursor.fetchone()
    return jsonify({
        "logged_in": True,
        "username": session["user"],
        "is_admin": bool(result[0]) if result else False,
        "can_access_panel": bool(result[1]) if result else False
    })

@users_bp.route("/user/qrcode")
@login_required
def user_qrcode():
    secret = session.get('pending_2fa_secret_user')
    username = session["user"]
    if not secret:
        abort(404)
    otp_uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@users_bp.route("/confirm_enable_2fa_user", methods=["POST"])
@login_required
def confirm_enable_2fa_user():
    username = session["user"]
    otp_code = request.form.get("otp_code", "").strip()
    secret = session.get('pending_2fa_secret_user')
    if not secret:
        return redirect(url_for("profil"))
    totp = pyotp.TOTP(secret)
    if not totp.verify(otp_code):
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
        return render_template(
            "enable_2fa_user.html",
            otp_uri=otp_uri,
            username=username,
            error="Code 2FA invalide."
        )
    # Code valide : on enregistre le secret en base
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET otp_secret = %s WHERE username = %s ", (secret, username))
        conn.commit()
    session.pop('pending_2fa_secret_user', None)
    return redirect(url_for("profil"))

@users_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))
