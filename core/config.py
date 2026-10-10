import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

_db = Path(os.environ.get("DB_PATH", "bama.db"))
DB_PATH = _db if _db.is_absolute() else PROJECT_ROOT / _db