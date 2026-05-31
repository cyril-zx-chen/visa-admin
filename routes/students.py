import shutil
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
import models
import utils
import config

students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/")
def list_students():
    students = models.get_all_students()
    completion = {}
    for s in students:
        subs = models.get_submissions_for_student(s["id"])
        required = [x for x in subs if x["is_required"]]
        optional = [x for x in subs if not x["is_required"]]
        req_done = sum(1 for x in required if x["status"] == "received")
        opt_done = sum(1 for x in optional if x["status"] == "received")
        last_activity = max(
            (x["received_at"] for x in subs if x["received_at"]),
            default=None
        )
        completion[s["id"]] = {
            "req_done": req_done,
            "req_total": len(required),
            "opt_done": opt_done,
            "opt_total": len(optional),
            "last_activity": last_activity,
        }
    return render_template("students/list.html", students=students, completion=completion)


@students_bp.route("/new", methods=["GET"])
def new_student_form():
    packages = models.get_all_packages()
    return render_template("students/new.html", packages=packages)


@students_bp.route("/new", methods=["POST"])
def create_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    package_id = request.form.get("package_id", "").strip()

    if not name or not email:
        flash("Name and email are required.", "danger")
        return redirect(url_for("students.new_student_form"))

    pkg_id = int(package_id) if package_id else None

    try:
        student_id = models.create_student(name, email, pkg_id)
        if pkg_id:
            slots = models.get_slots_for_package(pkg_id)
            for slot in slots:
                models.create_submission(student_id, slot["id"])
        utils.make_student_dir(name)
        flash(f'Student "{name}" added.', "success")
        return redirect(url_for("students.student_detail", student_id=student_id))
    except sqlite3.IntegrityError:
        flash(f'A student with email "{email}" already exists.', "danger")
        return redirect(url_for("students.new_student_form"))


@students_bp.route("/<int:student_id>/edit", methods=["GET"])
def edit_student_form(student_id):
    student = models.get_student(student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))
    packages = models.get_all_packages()
    return render_template("students/edit.html", student=student, packages=packages)


@students_bp.route("/<int:student_id>/edit", methods=["POST"])
def update_student(student_id):
    student = models.get_student(student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    package_id = request.form.get("package_id", "").strip()
    pkg_id = int(package_id) if package_id else None

    if not name or not email:
        flash("Name and email are required.", "danger")
        return redirect(url_for("students.edit_student_form", student_id=student_id))

    try:
        models.update_student(student_id, name, email, pkg_id)
        if name != student["name"]:
            utils.make_student_dir(name)
        flash(f'Student updated.', "success")
        return redirect(url_for("students.student_detail", student_id=student_id))
    except sqlite3.IntegrityError:
        flash(f'Email "{email}" is already used by another student.', "danger")
        return redirect(url_for("students.edit_student_form", student_id=student_id))


@students_bp.route("/import", methods=["GET"])
def import_form():
    return render_template("students/import.html", results=None)


@students_bp.route("/import", methods=["POST"])
def import_csv():
    file = request.files.get("file")
    skip_duplicates = request.form.get("skip_duplicates") == "1"

    if not file or file.filename == "":
        flash("Please select a CSV file.", "danger")
        return redirect(url_for("students.import_form"))

    rows = utils.parse_csv_import(file.stream)

    imported, skipped, errors = 0, 0, []

    all_pkgs = models.get_all_packages()
    pkg_by_name = {p["name"]: p for p in all_pkgs}

    conn = None
    try:
        from database import get_db
        conn = get_db()

        for i, row in enumerate(rows, start=2):
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            package_name = row.get("package_name", "").strip()

            if not name or not email:
                errors.append({"row": i, "reason": "Missing name or email."})
                continue

            if package_name not in pkg_by_name:
                errors.append({"row": i, "reason": f'Package "{package_name}" not found.'})
                continue

            pkg = pkg_by_name[package_name]

            existing = conn.execute(
                "SELECT id FROM students WHERE email = ?", (email,)
            ).fetchone()

            if existing:
                if skip_duplicates:
                    skipped += 1
                    continue
                else:
                    errors.append({"row": i, "reason": f'Email "{email}" already exists.'})
                    continue

            try:
                cur = conn.execute(
                    "INSERT INTO students (name, email, package_id) VALUES (?, ?, ?)",
                    (name, email, pkg["id"])
                )
                student_id = cur.lastrowid

                slots = conn.execute(
                    "SELECT id FROM document_slots WHERE package_id = ?", (pkg["id"],)
                ).fetchall()
                for slot in slots:
                    conn.execute(
                        "INSERT OR IGNORE INTO document_submissions (student_id, slot_id) VALUES (?, ?)",
                        (student_id, slot["id"])
                    )

                utils.make_student_dir(name)
                imported += 1

            except sqlite3.IntegrityError as e:
                errors.append({"row": i, "reason": str(e)})

        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Import failed: {e}", "danger")
        return redirect(url_for("students.import_form"))
    finally:
        if conn:
            conn.close()

    results = {"imported": imported, "skipped": skipped, "errors": errors}
    return render_template("students/import.html", results=results)


@students_bp.route("/<int:student_id>")
def student_detail(student_id):
    student = models.get_student(student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))
    submissions = models.get_submissions_for_student(student_id)
    required_total = sum(1 for s in submissions if s["is_required"])
    required_done = sum(1 for s in submissions if s["is_required"] and s["status"] == "received")
    progress = int(required_done / required_total * 100) if required_total else 0
    return render_template(
        "students/detail.html",
        student=student,
        submissions=submissions,
        required_total=required_total,
        required_done=required_done,
        progress=progress,
    )


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    student = models.get_student(student_id)
    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    delete_files = request.form.get("delete_files") == "1"
    if delete_files:
        folder = utils.get_documents_dir() / utils.to_folder_name(student["name"])
        if folder.exists():
            shutil.rmtree(folder)

    models.delete_student(student_id)
    flash(f'Student "{student["name"]}" deleted.', "success")
    return redirect(url_for("students.list_students"))
