from pathlib import Path
import os
import sys


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _project_root()
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "database.db"))).resolve()
DATABASE_SEED_PATH = Path(os.getenv("DATABASE_SEED_PATH", str(PROJECT_ROOT / "database.db"))).resolve()
API_PREFIX = os.getenv("API_PREFIX", "/api")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "").strip()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "carnes_luevanos")
MYSQL_USER = os.getenv("MYSQL_USER", "olivas_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
