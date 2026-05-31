import json
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash
import models
import utils
import config

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
def settings_page():
    docs_dir    = models.get_setting("documents_dir", str(config.DOCUMENTS_DIR))
    backup_info = utils.backup_file_info()
    return render_template(
        "settings.html",
        docs_dir=docs_dir,
        default_dir=str(config.DOCUMENTS_DIR),
        backup_info=backup_info,
    )


@settings_bp.route("/", methods=["POST"])
def save_settings():
    docs_dir = request.form.get("documents_dir", "").strip() or str(config.DOCUMENTS_DIR)
    try:
        p = Path(docs_dir)
        p.mkdir(parents=True, exist_ok=True)
        models.set_setting("documents_dir", str(p.resolve()))
        flash("Settings saved.", "success")
    except Exception as e:
        flash(f"Invalid storage path: {e}", "danger")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/export-to-path", methods=["POST"])
def export_to_path():
    dest = request.form.get("export_path", "").strip()
    if not dest:
        dest = str(utils.default_backup_path())
    try:
        utils.write_backup_to(dest)
        flash(f"Backup exported to: {dest}", "success")
    except Exception as e:
        flash(f"Export failed: {e}", "danger")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/restore-from-path", methods=["POST"])
def restore_from_path():
    replace = request.form.get("replace_existing") == "1"
    data = utils.read_backup_file()
    if data is None:
        flash(f"Backup file not found at: {utils.default_backup_path()}", "danger")
        return redirect(url_for("settings.settings_page"))
    try:
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


@settings_bp.route("/restore-from-upload", methods=["POST"])
def restore_from_upload():
    file = request.files.get("backup_file")
    if not file or file.filename == "":
        flash("Please select a backup JSON file.", "danger")
        return redirect(url_for("settings.settings_page"))
    replace = request.form.get("replace_existing_upload") == "1"
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
