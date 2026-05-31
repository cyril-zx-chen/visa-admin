import csv
import io
import re
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


def make_student_dir(student_name: str) -> Path:
    folder = get_documents_dir() / to_folder_name(student_name)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def stored_file_path(student_name: str, slot_name: str, original_filename: str) -> Path:
    ext = Path(original_filename).suffix.lower()
    safe_slot = re.sub(r"[^\w\-]", "", slot_name.strip().lower().replace(" ", "_"))
    folder = get_documents_dir() / to_folder_name(student_name)
    return folder / f"{safe_slot}{ext}"


def write_auto_backup() -> None:
    import json
    from models import get_setting, export_all_data
    backup_path = get_setting("backup_path")
    if not backup_path:
        return
    path = Path(backup_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = export_all_data()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_backup_file() -> dict | None:
    import json
    from models import get_setting
    backup_path = get_setting("backup_path")
    if not backup_path:
        return None
    path = Path(backup_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def backup_file_info() -> dict:
    from models import get_setting
    backup_path = get_setting("backup_path")
    if not backup_path:
        return {"configured": False, "path": None, "exists": False, "exported_at": None}
    path = Path(backup_path)
    exists = path.exists()
    exported_at = None
    if exists:
        try:
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            exported_at = data.get("exported_at")
        except Exception:
            pass
    return {"configured": True, "path": str(path), "exists": exists, "exported_at": exported_at}


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
