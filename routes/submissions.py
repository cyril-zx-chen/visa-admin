from pathlib import Path
from flask import Blueprint, request, redirect, url_for, flash, send_file, abort
from werkzeug.utils import secure_filename
import models
import utils
import config

submissions_bp = Blueprint("submissions", __name__, url_prefix="/submissions")


def _get_sub_student_slot(sub_id):
    from database import get_db
    conn = get_db()
    row = conn.execute("""
        SELECT ds.*, st.name AS student_name, sl.name AS slot_name,
               sl.preferred_name AS slot_preferred_name
        FROM document_submissions ds
        JOIN students st ON st.id = ds.student_id
        JOIN document_slots sl ON sl.id = ds.slot_id
        WHERE ds.id = ?
    """, (sub_id,)).fetchone()
    conn.close()
    return row


@submissions_bp.route("/<int:sub_id>/upload", methods=["POST"])
def upload_file(sub_id):
    row = _get_sub_student_slot(sub_id)
    if row is None:
        abort(404)

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("students.student_detail", student_id=row["student_id"]))

    utils.make_student_dir(row["student_name"])
    dest = utils.stored_file_path(
        row["student_name"], row["slot_name"], file.filename,
        preferred_name=row["slot_preferred_name"]
    )
    file.save(str(dest))

    display_name = secure_filename(file.filename)
    rel_path = str(dest.relative_to(config.BASE_DIR))
    models.set_submission_received(sub_id, display_name, rel_path)

    flash(f'"{display_name}" uploaded for {row["slot_name"]}.', "success")
    return redirect(url_for("students.student_detail", student_id=row["student_id"]))


@submissions_bp.route("/<int:sub_id>/mark-received", methods=["POST"])
def mark_received(sub_id):
    row = _get_sub_student_slot(sub_id)
    if row is None:
        abort(404)
    models.mark_received_no_file(sub_id)
    flash(f'"{row["slot_name"]}" marked as received.', "success")
    return redirect(url_for("students.student_detail", student_id=row["student_id"]))


@submissions_bp.route("/<int:sub_id>/mark-pending", methods=["POST"])
def mark_pending(sub_id):
    row = _get_sub_student_slot(sub_id)
    if row is None:
        abort(404)
    models.set_submission_pending(sub_id)
    flash(f'"{row["slot_name"]}" reverted to pending.', "warning")
    return redirect(url_for("students.student_detail", student_id=row["student_id"]))


@submissions_bp.route("/<int:sub_id>/notes", methods=["POST"])
def update_notes(sub_id):
    row = _get_sub_student_slot(sub_id)
    if row is None:
        abort(404)
    notes = request.form.get("notes", "").strip()
    models.set_submission_notes(sub_id, notes)
    flash("Notes saved.", "success")
    return redirect(url_for("students.student_detail", student_id=row["student_id"]))


@submissions_bp.route("/<int:sub_id>/download")
def download_file(sub_id):
    sub = models.get_submission(sub_id)
    if sub is None or not sub["stored_path"]:
        abort(404)
    file_path = config.BASE_DIR / sub["stored_path"]
    if not file_path.exists():
        abort(404)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=sub["filename"] or file_path.name,
    )
