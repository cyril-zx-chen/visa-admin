import io
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
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


@settings_bp.route("/export")
def export_data():
    data = models.export_all_data()
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"visa_admin_backup_{timestamp}.json"
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@settings_bp.route("/import", methods=["POST"])
def import_data():
    file = request.files.get("backup_file")
    if not file or file.filename == "":
        flash("Please select a backup JSON file.", "danger")
        return redirect(url_for("settings.settings_page"))

    replace = request.form.get("replace_existing") == "1"

    try:
        data = json.loads(file.stream.read().decode("utf-8"))
        if data.get("version") != 1:
            flash("Unrecognised backup format.", "danger")
            return redirect(url_for("settings.settings_page"))
        result = models.import_all_data(data, replace=replace)
        flash(
            f"Restore complete — "
            f"{result['packages']} package(s), "
            f"{result['slots']} slot(s), "
            f"{result['students']} student(s), "
            f"{result['submissions']} submission(s) imported.",
            "success",
        )
    except Exception as e:
        flash(f"Restore failed: {e}", "danger")

    return redirect(url_for("settings.settings_page"))
