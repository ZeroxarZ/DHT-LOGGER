from functools import wraps
from flask import session, redirect, url_for, render_template
from db import get_mysql_connection

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        with get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE username = %s", (session["user"],))
            user = cursor.fetchone()
        if not user or user[0] != 1:
            return render_template("error.html",
                       title="Accès refusé",
                       message="Vous n'avez pas les droits nécessaires pour accéder à cette page.",
                       redirect_url=url_for("index")), 403
        return f(*args, **kwargs)
    return decorated_function