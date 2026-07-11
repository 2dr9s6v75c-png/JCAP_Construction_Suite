from core.database.repositories.base_repository import BaseRepository


class DepartmentRepository(BaseRepository):
    """
    PostgreSQL data-access repository for core.departments.

    Contains department database operations only.
    Business rules and permission checks belong to services.
    """

    @classmethod
    def get_by_id(
        cls,
        department_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                department_code,
                department_name,
                description,
                is_active,
                created_at,
                updated_at
            FROM core.departments
            WHERE id = %s
            """,
            (department_id,),
            cursor=cursor,
        )

        return cls._map_department(row)

    @classmethod
    def get_by_code(
        cls,
        department_code: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                department_code,
                department_name,
                description,
                is_active,
                created_at,
                updated_at
            FROM core.departments
            WHERE LOWER(department_code) = LOWER(%s)
            """,
            (department_code,),
            cursor=cursor,
        )

        return cls._map_department(row)

    @classmethod
    def get_by_name(
        cls,
        department_name: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                department_code,
                department_name,
                description,
                is_active,
                created_at,
                updated_at
            FROM core.departments
            WHERE LOWER(department_name) = LOWER(%s)
            """,
            (department_name,),
            cursor=cursor,
        )

        return cls._map_department(row)

    @classmethod
    def get_all(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                id,
                department_code,
                department_name,
                description,
                is_active,
                created_at,
                updated_at
            FROM core.departments
            ORDER BY department_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_department(row)
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
                id,
                department_code,
                department_name,
                description,
                is_active,
                created_at,
                updated_at
            FROM core.departments
            WHERE is_active = TRUE
            ORDER BY department_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_department(row)
            for row in rows
        ]

    @classmethod
    def department_code_exists(
        cls,
        department_code: str,
        *,
        exclude_department_id=None,
        cursor=None,
    ) -> bool:
        if exclude_department_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.departments
                    WHERE LOWER(department_code) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    department_code,
                    exclude_department_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.departments
                WHERE LOWER(department_code) = LOWER(%s)
            )
            """,
            (department_code,),
            cursor=cursor,
        )

    @classmethod
    def department_name_exists(
        cls,
        department_name: str,
        *,
        exclude_department_id=None,
        cursor=None,
    ) -> bool:
        if exclude_department_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.departments
                    WHERE LOWER(department_name) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    department_name,
                    exclude_department_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.departments
                WHERE LOWER(department_name) = LOWER(%s)
            )
            """,
            (department_name,),
            cursor=cursor,
        )

    @classmethod
    def count_departments(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.departments
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
            FROM core.departments
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
            INSERT INTO core.departments (
                department_code,
                department_name,
                description,
                is_active
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                data["department_code"],
                data["department_name"],
                data.get("description"),
                data.get("is_active", True),
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Department was not created."
            )

        return str(row[0])

    @classmethod
    def update(
        cls,
        department_id,
        data: dict,
        *,
        cursor=None,
    ) -> bool:
        allowed_columns = {
            "department_code",
            "department_name",
            "description",
            "is_active",
        }

        updates = []
        params = []

        for column, value in data.items():
            if column not in allowed_columns:
                raise ValueError(
                    f"Department column is not updateable: {column}"
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
        params.append(department_id)

        affected_rows = cls.execute(
            f"""
            UPDATE core.departments
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
        department_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.departments
            SET
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (department_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def disable(
        cls,
        department_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.departments
            SET
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (department_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @staticmethod
    def _map_department(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "department_code": row[1],
            "department_name": row[2],
            "description": row[3] or "",
            "is_active": bool(row[4]),
            "created_at": row[5],
            "updated_at": row[6],
        }