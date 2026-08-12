import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _application_directory() -> Path:
    """Return the directory containing the runtime .env file."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_DIRECTORY = _application_directory()
ENV_FILE = APP_DIRECTORY / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)

APP_NAME = os.getenv("APP_NAME", "JCAP Construction Suite")
APP_VERSION = os.getenv("APP_VERSION", "0.9.0")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "jcap_construction_suite")
DB_USER = os.getenv("DB_USER", "jcap_app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DOCUMENT_ROOT = os.getenv(
    "DOCUMENT_ROOT",
    (
        r"\\192.168.50.39\JCAP Main Office Shared Folder"
        r"\JCAP Purchasing"
        r"\JCAP Quotation for Project Bidding"
    ),
)