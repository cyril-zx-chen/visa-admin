import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import config


def to_folder_name(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^\w\-]", "", name)
    return name or "unknown"


def get_documents_dir() -> Path:
    from models import get_setting
    custom = get_setting("documents_dir")
    if custom:
        p = Path(custom)
        p.mkdir(parents=True, exist_ok=True)
        return p
    return config.DOCUMENTS_DIR


def default_backup_path() -> Path:
    return get_documents_dir() / "visa_admin_backup.json"


def make_student_dir(student_name: str) -> Path:
    folder = get_documents_dir() / to_folder_name(student_name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def stored_file_path(student_name: str, slot_name: str, original_filename: str,
                     preferred_name: str | None = None) -> Path:
    ext = Path(original_filename).suffix.lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")
    base = preferred_name if preferred_name and preferred_name.strip() else slot_name
    safe = re.sub(r"[^\w\-]", "", base.strip().lower().replace(" ", "_"))
    folder = get_documents_dir() / to_folder_name(student_name)
    return folder / f"{safe}_{timestamp}{ext}"


def write_auto_backup() -> None:
    from models import export_all_data
    path = default_backup_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = export_all_data()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_backup_to(dest: str | Path) -> None:
    from models import export_all_data
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = export_all_data()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def backup_file_info() -> dict:
    path = default_backup_path()
    exists = path.exists()
    exported_at = None
    if exists:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            exported_at = data.get("exported_at")
        except Exception:
            pass
    return {"path": str(path), "exists": exists, "exported_at": exported_at}


def read_backup_file() -> dict | None:
    path = default_backup_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def parse_csv_import(file_stream) -> list[dict]:
    text = file_stream.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        normalised = {k.strip().lower(): v.strip() for k, v in row.items()}
        rows.append(normalised)
    return rows
