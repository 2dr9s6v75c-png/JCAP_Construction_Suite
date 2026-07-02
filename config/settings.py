from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "JCAP Construction Suite")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "jcap_construction_suite")
DB_USER = os.getenv("DB_USER", "jcap_app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DOCUMENT_ROOT = os.getenv(
    "DOCUMENT_ROOT",
    r"\\192.168.50.39\JCAP Main Office Shared Folder\JCAP Purchasing\JCAP Quotation for Project Bidding"
)