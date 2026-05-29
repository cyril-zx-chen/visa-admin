import sqlite3
from datetime import datetime, timezone
from database import get_db


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

def get_all_packages():
    conn = get_db()
    rows = conn.execute("SELECT * FROM visa_packages ORDER BY name").fetchall()
    conn.close()
    return rows


def get_package(pkg_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM visa_packages WHERE id = ?", (pkg_id,)).fetchone()
    conn.close()
    return row


def create_package(name):
    conn = get_db()
    cur = conn.execute("INSERT INTO visa_packages (name) VALUES (?)", (name,))
    conn.commit()
    pkg_id = cur.lastrowid
    conn.close()
    return pkg_id


def delete_package(pkg_id):
    conn = get_db()
    conn.execute("DELETE FROM visa_packages WHERE id = ?", (pkg_id,))
    conn.commit()
    conn.close()


def get_package_with_slots(pkg_id):
    conn = get_db()
    pkg = conn.execute("SELECT * FROM visa_packages WHERE id = ?", (pkg_id,)).fetchone()
    slots = conn.execute(
        "SELECT * FROM document_slots WHERE package_id = ? ORDER BY sort_order, name",
        (pkg_id,)
    ).fetchall()
    conn.close()
    return pkg, slots


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------

def get_slots_for_package(pkg_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM document_slots WHERE package_id = ? ORDER BY sort_order, name",
        (pkg_id,)
    ).fetchall()
    conn.close()
    return rows


def add_slot(pkg_id, name, is_required):
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_order FROM document_slots WHERE package_id = ?",
        (pkg_id,)
    ).fetchone()
    next_order = row["next_order"]
    cur = conn.execute(
        "INSERT INTO document_slots (package_id, name, is_required, sort_order) VALUES (?, ?, ?, ?)",
        (pkg_id, name, 1 if is_required else 0, next_order)
    )
    conn.commit()
    slot_id = cur.lastrowid
    conn.close()
    return slot_id


def delete_slot(slot_id):
    conn = get_db()
    conn.execute("DELETE FROM document_slots WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()


def toggle_slot_required(slot_id):
    conn = get_db()
    conn.execute(
        "UPDATE document_slots SET is_required = 1 - is_required WHERE id = ?",
        (slot_id,)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

def get_all_students():
    conn = get_db()
    rows = conn.execute("""
        SELECT s.*, vp.name AS package_name
        FROM students s
        LEFT JOIN visa_packages vp ON vp.id = s.package_id
        ORDER BY s.name
    """).fetchall()
    conn.close()
    return rows


def get_student(student_id):
    conn = get_db()
    row = conn.execute("""
        SELECT s.*, vp.name AS package_name
        FROM students s
        LEFT JOIN visa_packages vp ON vp.id = s.package_id
        WHERE s.id = ?
    """, (student_id,)).fetchone()
    conn.close()
    return row


def create_student(name, email, package_id):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO students (name, email, package_id) VALUES (?, ?, ?)",
        (name, email, package_id)
    )
    conn.commit()
    student_id = cur.lastrowid
    conn.close()
    return student_id


def delete_student(student_id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def get_students_for_package(pkg_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students WHERE package_id = ? ORDER BY name",
        (pkg_id,)
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

def get_submissions_for_student(student_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT ds.*, sl.name AS slot_name, sl.is_required, sl.sort_order
        FROM document_submissions ds
        JOIN document_slots sl ON sl.id = ds.slot_id
        WHERE ds.student_id = ?
        ORDER BY sl.sort_order, sl.name
    """, (student_id,)).fetchall()
    conn.close()
    return rows


def get_submission(sub_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM document_submissions WHERE id = ?", (sub_id,)
    ).fetchone()
    conn.close()
    return row


def create_submission(student_id, slot_id):
    conn = get_db()
    cur = conn.execute(
        "INSERT OR IGNORE INTO document_submissions (student_id, slot_id) VALUES (?, ?)",
        (student_id, slot_id)
    )
    conn.commit()
    sub_id = cur.lastrowid
    conn.close()
    return sub_id


def set_submission_received(sub_id, filename, stored_path):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "UPDATE document_submissions SET status='received', filename=?, stored_path=?, received_at=? WHERE id=?",
        (filename, stored_path, now, sub_id)
    )
    conn.commit()
    conn.close()


def set_submission_pending(sub_id):
    conn = get_db()
    conn.execute(
        "UPDATE document_submissions SET status='pending', filename=NULL, stored_path=NULL, received_at=NULL WHERE id=?",
        (sub_id,)
    )
    conn.commit()
    conn.close()


def set_submission_notes(sub_id, notes):
    conn = get_db()
    conn.execute(
        "UPDATE document_submissions SET notes=? WHERE id=?",
        (notes, sub_id)
    )
    conn.commit()
    conn.close()


def mark_received_no_file(sub_id):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "UPDATE document_submissions SET status='received', received_at=? WHERE id=?",
        (now, sub_id)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def get_dashboard_data():
    conn = get_db()

    packages = conn.execute("SELECT * FROM visa_packages ORDER BY name").fetchall()
    all_slots = conn.execute(
        "SELECT * FROM document_slots ORDER BY package_id, sort_order, name"
    ).fetchall()
    all_students = conn.execute("""
        SELECT s.*, vp.name AS package_name
        FROM students s
        LEFT JOIN visa_packages vp ON vp.id = s.package_id
        ORDER BY s.name
    """).fetchall()
    all_submissions = conn.execute(
        "SELECT * FROM document_submissions"
    ).fetchall()
    conn.close()

    slots_by_pkg = {}
    for slot in all_slots:
        slots_by_pkg.setdefault(slot["package_id"], []).append(slot)

    students_by_pkg = {}
    for student in all_students:
        pkg_id = student["package_id"]
        students_by_pkg.setdefault(pkg_id, []).append(student)

    subs_by_student_slot = {}
    for sub in all_submissions:
        subs_by_student_slot[(sub["student_id"], sub["slot_id"])] = sub

    data = {}
    for pkg in packages:
        data[pkg["id"]] = {
            "package": pkg,
            "slots": slots_by_pkg.get(pkg["id"], []),
            "students": students_by_pkg.get(pkg["id"], []),
            "submissions": subs_by_student_slot,
        }

    unassigned = students_by_pkg.get(None, [])
    return data, unassigned
