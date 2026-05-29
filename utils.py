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
