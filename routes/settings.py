from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash
import models
import config

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
def settings_page():
    docs_dir = models.get_setting("documents_dir", str(config.DOCUMENTS_DIR))
    return render_template("settings.html", docs_dir=docs_dir, default_dir=str(config.DOCUMENTS_DIR))


@settings_bp.route("/", methods=["POST"])
def save_settings():
    docs_dir = request.form.get("documents_dir", "").strip()
    if not docs_dir:
        docs_dir = str(config.DOCUMENTS_DIR)

    try:
        p = Path(docs_dir)
        p.mkdir(parents=True, exist_ok=True)
        models.set_setting("documents_dir", str(p.resolve()))
        flash(f"Storage path saved: {p.resolve()}", "success")
    except Exception as e:
        flash(f"Could not use that path: {e}", "danger")

    return redirect(url_for("settings.settings_page"))
