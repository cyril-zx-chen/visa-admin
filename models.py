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


# ---------------------------------------------------------------------------
# Backup / Restore
# ---------------------------------------------------------------------------

def export_all_data() -> dict:
    conn = get_db()

    packages = [dict(r) for r in conn.execute("SELECT * FROM visa_packages ORDER BY name").fetchall()]
    slots    = [dict(r) for r in conn.execute("SELECT * FROM document_slots ORDER BY package_id, sort_order").fetchall()]
    students = [dict(r) for r in conn.execute("SELECT * FROM students ORDER BY name").fetchall()]
    subs     = [dict(r) for r in conn.execute("SELECT * FROM document_submissions").fetchall()]
    settings = [dict(r) for r in conn.execute("SELECT * FROM settings").fetchall()]

    conn.close()

    pkg_map  = {p["id"]: p["name"] for p in packages}
    slot_map = {s["id"]: {"package_name": pkg_map.get(s["package_id"], ""), "slot_name": s["name"]} for s in slots}

    for s in slots:
        s["package_name"] = pkg_map.get(s["package_id"], "")

    for st in students:
        st["package_name"] = pkg_map.get(st["package_id"], "")
        st["submissions"] = []

    student_map = {s["id"]: s for s in students}
    for sub in subs:
        sid = sub["student_id"]
        if sid in student_map:
            info = slot_map.get(sub["slot_id"], {})
            sub["slot_name"]    = info.get("slot_name", "")
            sub["package_name"] = info.get("package_name", "")
            student_map[sid]["submissions"].append(sub)

    return {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "settings": settings,
        "visa_packages": [
            {
                "name": p["name"],
                "created_at": p["created_at"],
                "slots": [
                    {"name": s["name"], "is_required": s["is_required"], "sort_order": s["sort_order"]}
                    for s in slots if s["package_id"] == p["id"]
                ],
            }
            for p in packages
        ],
        "students": [
            {
                "name":         st["name"],
                "email":        st["email"],
                "package_name": st["package_name"],
                "created_at":   st["created_at"],
                "submissions": [
                    {
                        "slot_name":   sub["slot_name"],
                        "status":      sub["status"],
                        "filename":    sub["filename"],
                        "stored_path": sub["stored_path"],
                        "received_at": sub["received_at"],
                        "notes":       sub["notes"],
                    }
                    for sub in st["submissions"]
                ],
            }
            for st in students
        ],
    }


def import_all_data(data: dict, replace: bool = False) -> dict:
    conn = get_db()
    imported = {"packages": 0, "slots": 0, "students": 0, "submissions": 0, "errors": []}

    try:
        if replace:
            conn.execute("DELETE FROM document_submissions")
            conn.execute("DELETE FROM students")
            conn.execute("DELETE FROM document_slots")
            conn.execute("DELETE FROM visa_packages")
            conn.execute("DELETE FROM settings")

        # Settings
        for s in data.get("settings", []):
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                         (s["key"], s["value"]))

        # Packages + slots
        pkg_id_map = {}
        for pkg in data.get("visa_packages", []):
            existing = conn.execute("SELECT id FROM visa_packages WHERE name = ?", (pkg["name"],)).fetchone()
            if existing:
                pkg_id_map[pkg["name"]] = existing["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO visa_packages (name, created_at) VALUES (?, ?)",
                    (pkg["name"], pkg.get("created_at", datetime.now(timezone.utc).isoformat()))
                )
                pkg_id_map[pkg["name"]] = cur.lastrowid
                imported["packages"] += 1

            pkg_id = pkg_id_map[pkg["name"]]
            for slot in pkg.get("slots", []):
                exists = conn.execute(
                    "SELECT id FROM document_slots WHERE package_id = ? AND name = ?",
                    (pkg_id, slot["name"])
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO document_slots (package_id, name, is_required, sort_order) VALUES (?,?,?,?)",
                        (pkg_id, slot["name"], slot.get("is_required", 1), slot.get("sort_order", 0))
                    )
                    imported["slots"] += 1

        # Students + submissions
        for st in data.get("students", []):
            existing = conn.execute("SELECT id FROM students WHERE email = ?", (st["email"],)).fetchone()
            if existing:
                student_id = existing["id"]
            else:
                pkg_id = pkg_id_map.get(st.get("package_name", ""))
                cur = conn.execute(
                    "INSERT INTO students (name, email, package_id, created_at) VALUES (?,?,?,?)",
                    (st["name"], st["email"], pkg_id,
                     st.get("created_at", datetime.now(timezone.utc).isoformat()))
                )
                student_id = cur.lastrowid
                imported["students"] += 1

            pkg_name = st.get("package_name", "")
            pkg_id   = pkg_id_map.get(pkg_name)

            for sub in st.get("submissions", []):
                slot_row = None
                if pkg_id:
                    slot_row = conn.execute(
                        "SELECT id FROM document_slots WHERE package_id = ? AND name = ?",
                        (pkg_id, sub["slot_name"])
                    ).fetchone()
                if not slot_row:
                    continue
                conn.execute("""
                    INSERT OR REPLACE INTO document_submissions
                        (student_id, slot_id, status, filename, stored_path, received_at, notes)
                    VALUES (?,?,?,?,?,?,?)
                """, (student_id, slot_row["id"], sub.get("status", "pending"),
                      sub.get("filename"), sub.get("stored_path"),
                      sub.get("received_at"), sub.get("notes")))
                imported["submissions"] += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return imported
