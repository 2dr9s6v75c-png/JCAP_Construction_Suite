from datetime import datetime
from core.database.connection import get_connection


def generate_document_number(document_type: str) -> str:
    year = datetime.now().year

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO system.document_sequences (
                document_type,
                year,
                last_number
            )
            VALUES (%s, %s, 1)
            ON CONFLICT (document_type, year)
            DO UPDATE SET last_number = system.document_sequences.last_number + 1
            RETURNING last_number
            """,
            (document_type, year)
        )

        next_number = cur.fetchone()[0]
        conn.commit()

        return f"{document_type}-{year}-{next_number:06d}"

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()