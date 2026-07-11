from core.database.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository):
    """
    PostgreSQL data-access repository for core.roles.

    Contains role database operations only.
    Permission rules and business validation belong to services.
    """

    @classmethod
    def get_by_id(
        cls,
        role_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                role_name,
                description,
                is_active,
                created_at
            FROM core.roles
            WHERE id = %s
            """,
            (role_id,),
            cursor=cursor,
        )

        return cls._map_role(row)

    @classmethod
    def get_by_name(
        cls,
        role_name: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                role_name,
                description,
                is_active,
                created_at
            FROM core.roles
            WHERE LOWER(role_name) = LOWER(%s)
            """,
            (role_name,),
            cursor=cursor,
        )

        return cls._map_role(row)

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
                role_name,
                description,
                is_active,
                created_at
            FROM core.roles
            ORDER BY role_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_role(row)
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
                role_name,
                description,
                is_active,
                created_at
            FROM core.roles
            WHERE is_active = TRUE
            ORDER BY role_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_role(row)
            for row in rows
        ]

    @classmethod
    def role_name_exists(
        cls,
        role_name: str,
        *,
        exclude_role_id=None,
        cursor=None,
    ) -> bool:
        if exclude_role_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.roles
                    WHERE LOWER(role_name) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    role_name,
                    exclude_role_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.roles
                WHERE LOWER(role_name) = LOWER(%s)
            )
            """,
            (role_name,),
            cursor=cursor,
        )

    @classmethod
    def count_roles(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.roles
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
            FROM core.roles
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
            INSERT INTO core.roles (
                role_name,
                description,
                is_active
            )
            VALUES (
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                data["role_name"],
                data.get("description"),
                data.get("is_active", True),
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Role was not created."
            )

        return str(row[0])

    @classmethod
    def update(
        cls,
        role_id,
        data: dict,
        *,
        cursor=None,
    ) -> bool:
        allowed_columns = {
            "role_name",
            "description",
            "is_active",
        }

        updates = []
        params = []

        for column, value in data.items():
            if column not in allowed_columns:
                raise ValueError(
                    f"Role column is not updateable: {column}"
                )

            updates.append(
                f"{column} = %s"
            )
            params.append(value)

        if not updates:
            return False

        params.append(role_id)

        affected_rows = cls.execute(
            f"""
            UPDATE core.roles
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
        role_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.roles
            SET is_active = TRUE
            WHERE id = %s
            """,
            (role_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def disable(
        cls,
        role_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.roles
            SET is_active = FALSE
            WHERE id = %s
            """,
            (role_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @staticmethod
    def _map_role(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "role_name": row[1],
            "description": row[2] or "",
            "is_active": bool(row[3]),
            "created_at": row[4],
        }