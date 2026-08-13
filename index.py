import os
import sys
from pathlib import Path


def _application_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APPLICATION_ROOT = _application_root()
DATABASE_PATH = APPLICATION_ROOT / "database.db"
VENDOR_PATH = APPLICATION_ROOT / "vendor"

if VENDOR_PATH.is_dir() and str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

# Toda la aplicación y la API trabajan desde una única raíz y una sola DB.
os.chdir(APPLICATION_ROOT)
os.environ["DATABASE_PATH"] = str(DATABASE_PATH)
os.environ["DATABASE_SEED_PATH"] = str(DATABASE_PATH)

from manager import main


if __name__ == "__main__":
    main()

