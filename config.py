from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "visa_admin.db"
DOCUMENTS_DIR = BASE_DIR / "documents"
SECRET_KEY = "change-me-local-only-tool"
MAX_CONTENT_LENGTH = 50 * 1024 * 1024
