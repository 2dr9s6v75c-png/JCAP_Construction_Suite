import psycopg2
import psycopg2.extras

from config import settings

# Register UUID support once when this module is imported.
psycopg2.extras.register_uuid()


def get_connection():
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        return True, version[0]
    except Exception as e:
        return False, str(e)