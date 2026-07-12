from core.database.connection import get_connection
from core.security.password_service import verify_password


def authenticate_user(
    username: str,
    password: str,
):
    """
    Authenticate a JCAP Construction Suite user.

    Returns a fully hydrated authenticated-user dictionary so the
    application can use database-driven RBAC permissions.

    Return format:

        (
            success: bool,
            message: str,
            user_data: dict | None,
        )
    """

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                u.id,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.is_active,
                u.employee_number,

                u.role_id,
                r.role_name,

                u.department_id,
                d.department_code,
                d.department_name,

                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,

                u.email,
                u.phone

            FROM core.users u

            LEFT JOIN core.roles r
                ON r.id = u.role_id

            LEFT JOIN core.departments d
                ON d.id = u.department_id

            LEFT JOIN core.job_titles jt
                ON jt.id = u.job_title_id

            WHERE LOWER(u.username) = LOWER(%s)
            LIMIT 1
            """,
            (
                username.strip(),
            ),
        )

        user = cur.fetchone()

        if not user:
            return (
                False,
                "Invalid username or password",
                None,
            )

        (
            user_id,
            db_username,
            password_hash,
            full_name,
            legacy_role,
            is_active,
            employee_number,
            role_id,
            role_name,
            department_id,
            department_code,
            department_name,
            job_title_id,
            job_title_code,
            job_title_name,
            email,
            phone,
        ) = user

        # ========================================================
        # ACCOUNT STATUS
        # ========================================================

        if not is_active:
            return (
                False,
                "User account is inactive",
                None,
            )

        # ========================================================
        # PASSWORD VERIFICATION
        # ========================================================

        if not verify_password(
            password,
            password_hash,
        ):
            return (
                False,
                "Invalid username or password",
                None,
            )

        # ========================================================
        # AUTHENTICATED SESSION USER
        # ========================================================

        user_data = {
            "id": str(user_id),
            "employee_number": employee_number,
            "username": db_username,
            "full_name": full_name,

            # Legacy role compatibility
            "role": legacy_role,
            "legacy_role": legacy_role,

            # RBAC v1
            "role_id": (
                str(role_id)
                if role_id
                else None
            ),
            "role_name": role_name,

            # Organization assignment
            "department_id": (
                str(department_id)
                if department_id
                else None
            ),
            "department_code": department_code,
            "department_name": department_name,

            "job_title_id": (
                str(job_title_id)
                if job_title_id
                else None
            ),
            "job_title_code": job_title_code,
            "job_title_name": job_title_name,

            # Contact information
            "email": email,
            "phone": phone,

            "is_active": bool(is_active),
        }

        return (
            True,
            "Login successful",
            user_data,
        )

    except Exception as error:
        return (
            False,
            str(error),
            None,
        )

    finally:
        if cur is not None:
            cur.close()

        if conn is not None:
            conn.close()