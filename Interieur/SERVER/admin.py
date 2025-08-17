from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, send_file, abort
)
from werkzeug.security import generate_password_hash
from db import get_mysql_connection
from auth import admin_required
from sendmail import log_admin_action
from homeassistant import send_to_home_assistant
import pyotp
import qrcode
import io
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin(username):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
    return bool(user and user[0] == 1)

@admin_bp.route("/logs")
@admin_required
def admin_logs():
    if "user" not in session or not is_admin(session["user"]):
        return redirect(url_for("login"))
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT admin_username, action, target, timestamp FROM admin_logs ORDER BY id DESC LIMIT 100")
        logs = cursor.fetchall()
    return render_template("admin_logs.html", logs=logs)

def get_homeassistant_enabled():
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT homeassistant_enabled FROM settings WHERE id=1")
        result = cursor.fetchone()
        return bool(result[0]) if result else True

def set_homeassistant_enabled(enabled: bool):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE settings SET homeassistant_enabled=%s WHERE id=1",
            (int(enabled),)
        )
        conn.commit()

homeassistant_enabled = get_homeassistant_enabled()

@admin_bp.route("/toggle_homeassistant", methods=["POST"])
@admin_required
def toggle_homeassistant():
    current = get_homeassistant_enabled()
    set_homeassistant_enabled(not current)
    # Si on vient d'activer, on envoie la dernière mesure à Home Assistant
    if not current:
        try:
            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT device_id, temperature, humidity FROM measurements ORDER BY time DESC LIMIT 1")
                last = cursor.fetchone()
            if last:
                device_id, temperature, humidity = last
                send_to_home_assistant(device_id, temperature, humidity)
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi à Home Assistant : {e}")
    flash(
        "Envoi vers Home Assistant activé." if not current else "Envoi vers Home Assistant désactivé.",
        "info"
    )
    return redirect(url_for("admin.admin_panel"))

@admin_bp.route("/")
@admin_required
def admin_panel():
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, is_admin, can_access_panel, email, otp_secret, active
            FROM users
            ORDER BY id ASC
        """)
        users = cursor.fetchall()
    homeassistant_enabled = get_homeassistant_enabled()
    return render_template("admin_panel.html", users=users, homeassistant_enabled=homeassistant_enabled)

@admin_bp.route("/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    try:
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
    except Exception as e:
        logging.error(f"Erreur suppression utilisateur : {e}")
    log_admin_action(session["user"], "suppression utilisateur", f"user_id={user_id}")
    return redirect(url_for("admin_panel"))

@admin_bp.route("/update_user/<int:user_id>", methods=["POST"])
@admin_required
def update_user(user_id):
    new_password = request.form.get("new_password", "")
    email = request.form.get("email", "").strip()
    is_admin_val = 1 if request.form.get("is_admin") == "on" else 0
    can_access_panel = 1 if request.form.get("can_access_panel") == "on" else 0
    try:
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            if new_password:
                hashed = generate_password_hash(new_password)
                cursor.execute("""
                    UPDATE users 
                    SET password = %s, is_admin = %s, can_access_panel = %s, email = %s 
                    WHERE id = %s
                """, (hashed, is_admin_val, can_access_panel, email, user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET is_admin = %s, can_access_panel = %s, email = %s 
                    WHERE id = %s
                """, (is_admin_val, can_access_panel, email, user_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Erreur modification utilisateur : {e}")
    log_admin_action(session["user"], "modification utilisateur", f"user_id={user_id}")
    return redirect(url_for("admin_panel"))

@admin_bp.route("/enable_2fa/<int:user_id>", methods=["GET"])
@admin_required
def admin_enable_2fa(user_id):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, otp_secret FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return render_template("error.html", title="Utilisateur introuvable", message="Utilisateur non trouvé.", redirect_url=url_for("admin_panel")), 404
        username, otp_secret = user
        if otp_secret:
            return render_template("enable_2fa.html", otp_uri=pyotp.totp.TOTP(otp_secret).provisioning_uri(name=username, issuer_name="DHT-Logger"), username=username, user_id=user_id)
        secret = pyotp.random_base32()
        session['pending_2fa_secret'] = secret
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
    log_admin_action(session["user"], "activation 2FA", f"user_id={user_id}")
    return render_template("enable_2fa.html", otp_uri=otp_uri, username=username, user_id=user_id)

@admin_bp.route("/qrcode/<int:user_id>")
@admin_required
def admin_qrcode(user_id):
    secret = session.get('pending_2fa_secret')
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, otp_secret FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            abort(404)
        username, otp_secret = user
    if not secret:
        secret = otp_secret
    if not secret:
        abort(404)
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@admin_bp.route("/disable_2fa/<int:user_id>", methods=["POST"])
@admin_required
def admin_disable_2fa(user_id):
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET otp_secret = '' WHERE id = %s", (user_id,))
        conn.commit()
    log_admin_action(session["user"], "désactivation 2FA", f"user_id={user_id}")
    return redirect(url_for("admin_panel"))

@admin_bp.route("/confirm_enable_2fa/<int:user_id>", methods=["POST"])
@admin_required
def confirm_enable_2fa(user_id):
    otp_code = request.form.get("otp_code", "").strip()
    secret = session.get('pending_2fa_secret')
    if not secret:
        flash("Erreur : secret temporaire manquant.", "error")
        return redirect(url_for("admin_panel"))
    totp = pyotp.TOTP(secret)
    if not totp.verify(otp_code):
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        username = user[0] if user else ""
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="DHT-Logger")
        return render_template("enable_2fa.html", otp_uri=otp_uri, username=username, user_id=user_id, error="Code 2FA invalide.")
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET otp_secret = %s WHERE id = %s", (secret, user_id))
        conn.commit()
    session.pop('pending_2fa_secret', None)
    flash("Double authentification activée avec succès.", "success")
    return redirect(url_for("admin_panel"))