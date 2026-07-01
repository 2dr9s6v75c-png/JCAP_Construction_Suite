from core.database.connection import get_connection
from core.security.password_service import verify_password


def authenticate_user(username: str, password: str):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, username, password_hash, full_name, role, is_active
            FROM core.users
            WHERE username = %s
            """,
            (username,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return False, "Invalid username or password", None

        user_id, db_username, password_hash, full_name, role, is_active = user

        if not is_active:
            return False, "User account is inactive", None

        if not verify_password(password, password_hash):
            return False, "Invalid username or password", None

        user_data = {
            "id": user_id,
            "username": db_username,
            "full_name": full_name,
            "role": role
        }

        return True, "Login successful", user_data

    except Exception as e:
        return False, str(e), None