from flask import Blueprint, render_template, url_for

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@errors_bp.app_errorhandler(403)
def forbidden(e):
    return render_template(
        "error.html",
        title="Accès refusé",
        message="Vous n'avez pas les droits nécessaires pour accéder à cette page.",
        redirect_url=url_for("index")
    ), 403

@errors_bp.app_errorhandler(429)
def ratelimit_handler(e):
    retry_after = getattr(e, "retry_after", None)
    return render_template(
        "429.html",
        title="Trop de tentatives",
        message="Trop de tentatives de connexion. Merci de patienter avant de réessayer.",
        retry_after=retry_after
    ), 429