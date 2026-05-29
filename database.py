import sqlite3
import config


def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS visa_packages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS document_slots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL REFERENCES visa_packages(id) ON DELETE CASCADE,
            name       TEXT    NOT NULL,
            is_required INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            UNIQUE(package_id, name)
        );

        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            package_id INTEGER REFERENCES visa_packages(id) ON DELETE SET NULL,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS document_submissions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            slot_id     INTEGER NOT NULL REFERENCES document_slots(id) ON DELETE CASCADE,
            status      TEXT    NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','received')),
            filename    TEXT,
            stored_path TEXT,
            received_at TEXT,
            notes       TEXT,
            UNIQUE(student_id, slot_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
