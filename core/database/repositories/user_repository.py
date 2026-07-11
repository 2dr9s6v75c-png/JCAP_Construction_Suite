from core.database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    PostgreSQL data-access repository for core.users.

    This repository contains database operations only.
    Business rules, permissions, password hashing, and activity logging
    belong to OrganizationService and other framework services.
    """

    @classmethod
    def get_by_id(
        cls,
        user_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                u.id,
                u.employee_number,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.role_id,
                r.role_name,
                u.department_id,
                d.department_code,
                d.department_name,
                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,
                u.email,
                u.phone,
                u.is_active,
                u.last_login_at,
                u.created_at,
                u.updated_at
            FROM core.users u
            LEFT JOIN core.roles r
                ON u.role_id = r.id
            LEFT JOIN core.departments d
                ON u.department_id = d.id
            LEFT JOIN core.job_titles jt
                ON u.job_title_id = jt.id
            WHERE u.id = %s
            """,
            (user_id,),
            cursor=cursor,
        )

        return cls._map_user(row)

    @classmethod
    def get_by_username(
        cls,
        username: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                u.id,
                u.employee_number,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.role_id,
                r.role_name,
                u.department_id,
                d.department_code,
                d.department_name,
                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,
                u.email,
                u.phone,
                u.is_active,
                u.last_login_at,
                u.created_at,
                u.updated_at
            FROM core.users u
            LEFT JOIN core.roles r
                ON u.role_id = r.id
            LEFT JOIN core.departments d
                ON u.department_id = d.id
            LEFT JOIN core.job_titles jt
                ON u.job_title_id = jt.id
            WHERE LOWER(u.username) = LOWER(%s)
            """,
            (username,),
            cursor=cursor,
        )

        return cls._map_user(row)

    @classmethod
    def get_by_employee_number(
        cls,
        employee_number: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                u.id,
                u.employee_number,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.role_id,
                r.role_name,
                u.department_id,
                d.department_code,
                d.department_name,
                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,
                u.email,
                u.phone,
                u.is_active,
                u.last_login_at,
                u.created_at,
                u.updated_at
            FROM core.users u
            LEFT JOIN core.roles r
                ON u.role_id = r.id
            LEFT JOIN core.departments d
                ON u.department_id = d.id
            LEFT JOIN core.job_titles jt
                ON u.job_title_id = jt.id
            WHERE LOWER(u.employee_number) = LOWER(%s)
            """,
            (employee_number,),
            cursor=cursor,
        )

        return cls._map_user(row)

    @classmethod
    def get_all(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                u.id,
                u.employee_number,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.role_id,
                r.role_name,
                u.department_id,
                d.department_code,
                d.department_name,
                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,
                u.email,
                u.phone,
                u.is_active,
                u.last_login_at,
                u.created_at,
                u.updated_at
            FROM core.users u
            LEFT JOIN core.roles r
                ON u.role_id = r.id
            LEFT JOIN core.departments d
                ON u.department_id = d.id
            LEFT JOIN core.job_titles jt
                ON u.job_title_id = jt.id
            ORDER BY
                u.full_name,
                u.username
            """,
            cursor=cursor,
        )

        return [
            cls._map_user(row)
            for row in rows
        ]

    @classmethod
    def get_active(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                u.id,
                u.employee_number,
                u.username,
                u.password_hash,
                u.full_name,
                u.role,
                u.role_id,
                r.role_name,
                u.department_id,
                d.department_code,
                d.department_name,
                u.job_title_id,
                jt.job_title_code,
                jt.job_title_name,
                u.email,
                u.phone,
                u.is_active,
                u.last_login_at,
                u.created_at,
                u.updated_at
            FROM core.users u
            LEFT JOIN core.roles r
                ON u.role_id = r.id
            LEFT JOIN core.departments d
                ON u.department_id = d.id
            LEFT JOIN core.job_titles jt
                ON u.job_title_id = jt.id
            WHERE u.is_active = TRUE
            ORDER BY
                u.full_name,
                u.username
            """,
            cursor=cursor,
        )

        return [
            cls._map_user(row)
            for row in rows
        ]

    @classmethod
    def username_exists(
        cls,
        username: str,
        *,
        exclude_user_id=None,
        cursor=None,
    ) -> bool:
        if exclude_user_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.users
                    WHERE LOWER(username) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    username,
                    exclude_user_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.users
                WHERE LOWER(username) = LOWER(%s)
            )
            """,
            (username,),
            cursor=cursor,
        )

    @classmethod
    def employee_number_exists(
        cls,
        employee_number: str,
        *,
        exclude_user_id=None,
        cursor=None,
    ) -> bool:
        if exclude_user_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.users
                    WHERE LOWER(employee_number) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    employee_number,
                    exclude_user_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.users
                WHERE LOWER(employee_number) = LOWER(%s)
            )
            """,
            (employee_number,),
            cursor=cursor,
        )

    @classmethod
    def count_users(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.users
            """,
            cursor=cursor,
        )

    @classmethod
    def count_active(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.users
            WHERE is_active = TRUE
            """,
            cursor=cursor,
        )

    @classmethod
    def create(
        cls,
        data: dict,
        *,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO core.users (
                employee_number,
                username,
                password_hash,
                full_name,
                role,
                role_id,
                department_id,
                job_title_id,
                email,
                phone,
                is_active,
                created_by,
                updated_by
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                data.get("employee_number"),
                data["username"],
                data["password_hash"],
                data["full_name"],
                data.get("legacy_role"),
                data.get("role_id"),
                data.get("department_id"),
                data.get("job_title_id"),
                data.get("email"),
                data.get("phone"),
                data.get("is_active", True),
                data.get("created_by"),
                data.get("updated_by"),
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "User account was not created."
            )

        return str(row[0])

    @classmethod
    def update(
        cls,
        user_id,
        data: dict,
        *,
        cursor=None,
    ) -> bool:
        allowed_columns = {
            "employee_number",
            "username",
            "password_hash",
            "full_name",
            "role",
            "role_id",
            "department_id",
            "job_title_id",
            "email",
            "phone",
            "is_active",
            "last_login_at",
            "updated_by",
        }

        updates = []
        params = []

        for column, value in data.items():
            if column not in allowed_columns:
                raise ValueError(
                    f"User column is not updateable: {column}"
                )

            updates.append(
                f"{column} = %s"
            )
            params.append(value)

        if not updates:
            return False

        updates.append(
            "updated_at = CURRENT_TIMESTAMP"
        )
        params.append(user_id)

        affected_rows = cls.execute(
            f"""
            UPDATE core.users
            SET
                {", ".join(updates)}
            WHERE id = %s
            """,
            params,
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def enable(
        cls,
        user_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.users
            SET
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (user_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def disable(
        cls,
        user_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.users
            SET
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (user_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def update_last_login(
        cls,
        user_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.users
            SET
                last_login_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (user_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @staticmethod
    def _map_user(row):
        if not row:
            return None

        legacy_role = row[5] or ""

        return {
            "id": str(row[0]),
            "employee_number": row[1] or "",
            "username": row[2],
            "password_hash": row[3],
            "full_name": row[4],

            # Legacy compatibility
            "role": legacy_role,
            "legacy_role": legacy_role,

            # New organization model
            "role_id": (
                str(row[6])
                if row[6]
                else None
            ),
            "role_name": row[7] or "",

            "department_id": (
                str(row[8])
                if row[8]
                else None
            ),
            "department_code": row[9] or "",
            "department_name": row[10] or "",

            "job_title_id": (
                str(row[11])
                if row[11]
                else None
            ),
            "job_title_code": row[12] or "",
            "job_title_name": row[13] or "",

            "email": row[14] or "",
            "phone": row[15] or "",
            "is_active": bool(row[16]),
            "last_login_at": row[17],
            "created_at": row[18],
            "updated_at": row[19],
        }  