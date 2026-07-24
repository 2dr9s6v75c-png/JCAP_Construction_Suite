from __future__ import annotations

from typing import Any

from core.database.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    """
    PostgreSQL data-access repository for Project Master records.

    Business validation, permissions, transactions, code generation,
    and activity logging belong to ProjectService.
    """

    _SELECT_COLUMNS = """
        p.id,
        p.project_code,
        p.project_name,
        p.client_id,
        c.client_code,
        c.client_name,
        p.remarks,
        p.is_active,
        p.created_at,
        p.created_by,
        p.updated_at,
        p.updated_by
    """

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        project_id: Any,
        *,
        cursor=None,
    ) -> dict | None:
        row = cls.fetch_one(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE p.id = %s
            """,
            (project_id,),
            cursor=cursor,
        )

        return cls._map_project(row)

    @classmethod
    def get_by_code(
        cls,
        project_code: str,
        *,
        cursor=None,
    ) -> dict | None:
        row = cls.fetch_one(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE LOWER(p.project_code) = LOWER(%s)
            """,
            (project_code,),
            cursor=cursor,
        )

        return cls._map_project(row)

    @classmethod
    def get_by_name(
        cls,
        project_name: str,
        *,
        client_id: Any | None = None,
        active_only: bool = False,
        cursor=None,
    ) -> dict | None:
        query = f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE LOWER(BTRIM(p.project_name))
                = LOWER(BTRIM(%s))
        """

        params: list[Any] = [project_name]

        if client_id is not None:
            query += """
                AND p.client_id = %s
            """
            params.append(client_id)

        if active_only:
            query += """
                AND p.is_active = TRUE
            """

        query += """
            ORDER BY p.is_active DESC, p.created_at DESC
            LIMIT 1
        """

        row = cls.fetch_one(
            query,
            params,
            cursor=cursor,
        )

        return cls._map_project(row)

    @classmethod
    def get_all(
        cls,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict]:
        where_clause, params = cls._build_status_filter(
            status_filter
        )

        rows = cls.fetch_all(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            {where_clause}
            ORDER BY
                p.is_active DESC,
                p.project_name,
                p.project_code
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_project(row)
            for row in rows
        ]

    @classmethod
    def get_active(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        return cls.get_all(
            status_filter="Active",
            cursor=cursor,
        )

    @classmethod
    def get_by_client(
        cls,
        client_id: Any,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict]:
        status_clause, status_params = cls._build_status_filter(
            status_filter,
            table_alias="p",
            include_where=False,
        )

        rows = cls.fetch_all(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE p.client_id = %s
            {status_clause}
            ORDER BY
                p.is_active DESC,
                p.project_name,
                p.project_code
            """,
            [client_id, *status_params],
            cursor=cursor,
        )

        return [
            cls._map_project(row)
            for row in rows
        ]

    @classmethod
    def search(
        cls,
        search_text: str = "",
        status_filter: str = "Active",
        *,
        client_id: Any | None = None,
        cursor=None,
    ) -> list[dict]:
        clean_search = str(search_text or "").strip()
        conditions: list[str] = []
        params: list[Any] = []

        if clean_search:
            search_pattern = f"%{clean_search}%"
            conditions.append(
                """
                (
                    p.project_code ILIKE %s
                    OR p.project_name ILIKE %s
                    OR c.client_code ILIKE %s
                    OR c.client_name ILIKE %s
                    OR COALESCE(p.remarks, '') ILIKE %s
                )
                """
            )
            params.extend([search_pattern] * 5)

        if client_id is not None:
            conditions.append("p.client_id = %s")
            params.append(client_id)

        normalized_status = cls._normalize_status_filter(
            status_filter
        )

        if normalized_status == "Active":
            conditions.append("p.is_active = TRUE")
        elif normalized_status == "Inactive":
            conditions.append("p.is_active = FALSE")

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE "
                + " AND ".join(
                    f"({condition.strip()})"
                    for condition in conditions
                )
            )

        rows = cls.fetch_all(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.projects p
            INNER JOIN master.clients c
                ON c.id = p.client_id
            {where_clause}
            ORDER BY
                p.is_active DESC,
                p.project_name,
                p.project_code
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_project(row)
            for row in rows
        ]

    # ============================================================
    # CREATE / UPDATE
    # ============================================================

    @classmethod
    def create(
        cls,
        *,
        project_code: str,
        project_name: str,
        client_id: Any,
        remarks: str | None,
        created_by: Any,
        cursor=None,
    ) -> dict:
        row = cls.execute_returning(
            """
            INSERT INTO master.projects (
                project_code,
                project_name,
                client_id,
                remarks,
                is_active,
                created_by,
                updated_by
            )
            VALUES (%s, %s, %s, %s, TRUE, %s, %s)
            RETURNING id
            """,
            (
                project_code,
                project_name,
                client_id,
                remarks,
                created_by,
                created_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Project Master record could not be created."
            )

        project = cls.get_by_id(
            row[0],
            cursor=cursor,
        )

        if project is None:
            raise RuntimeError(
                "The created Project Master record could not be loaded."
            )

        return project

    @classmethod
    def update(
        cls,
        project_id: Any,
        *,
        project_name: str,
        client_id: Any,
        remarks: str | None,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        row = cls.execute_returning(
            """
            UPDATE master.projects
            SET
                project_name = %s,
                client_id = %s,
                remarks = %s,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                project_name,
                client_id,
                remarks,
                updated_by,
                project_id,
            ),
            cursor=cursor,
        )

        if not row:
            return None

        return cls.get_by_id(
            row[0],
            cursor=cursor,
        )

    @classmethod
    def set_active_status(
        cls,
        project_id: Any,
        *,
        is_active: bool,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        row = cls.execute_returning(
            """
            UPDATE master.projects
            SET
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                bool(is_active),
                updated_by,
                project_id,
            ),
            cursor=cursor,
        )

        if not row:
            return None

        return cls.get_by_id(
            row[0],
            cursor=cursor,
        )

    @classmethod
    def deactivate(
        cls,
        project_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        return cls.set_active_status(
            project_id,
            is_active=False,
            updated_by=updated_by,
            cursor=cursor,
        )

    @classmethod
    def restore(
        cls,
        project_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        return cls.set_active_status(
            project_id,
            is_active=True,
            updated_by=updated_by,
            cursor=cursor,
        )

    # ============================================================
    # EXISTENCE CHECKS
    # ============================================================

    @classmethod
    def project_code_exists(
        cls,
        project_code: str,
        *,
        exclude_project_id: Any | None = None,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.projects
                WHERE LOWER(project_code) = LOWER(%s)
        """

        params: list[Any] = [project_code]

        if exclude_project_id is not None:
            query += """
                  AND id <> %s
            """
            params.append(exclude_project_id)

        query += """
            )
        """

        return cls.exists(
            query,
            params,
            cursor=cursor,
        )

    @classmethod
    def active_project_name_exists(
        cls,
        *,
        client_id: Any,
        project_name: str,
        exclude_project_id: Any | None = None,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.projects
                WHERE client_id = %s
                  AND LOWER(BTRIM(project_name))
                      = LOWER(BTRIM(%s))
                  AND is_active = TRUE
        """

        params: list[Any] = [
            client_id,
            project_name,
        ]

        if exclude_project_id is not None:
            query += """
                  AND id <> %s
            """
            params.append(exclude_project_id)

        query += """
            )
        """

        return cls.exists(
            query,
            params,
            cursor=cursor,
        )

    @classmethod
    def client_exists(
        cls,
        client_id: Any,
        *,
        active_only: bool = False,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.clients
                WHERE id = %s
        """

        if active_only:
            query += """
                  AND is_active = TRUE
            """

        query += """
            )
        """

        return cls.exists(
            query,
            (client_id,),
            cursor=cursor,
        )

    # ============================================================
    # CODE GENERATION SUPPORT
    # ============================================================

    @classmethod
    def get_highest_code_number(
        cls,
        *,
        prefix: str = "PRJ",
        cursor=None,
    ) -> int:
        """
        Return the highest numeric suffix currently used by project codes.

        Code-generation locking belongs to ProjectService.
        """
        row = cls.fetch_one(
            """
            SELECT COALESCE(
                MAX(
                    CASE
                        WHEN project_code ~ %s
                        THEN SUBSTRING(
                            project_code
                            FROM '([0-9]+)$'
                        )::BIGINT
                        ELSE NULL
                    END
                ),
                0
            )
            FROM master.projects
            """,
            (rf"^{prefix}-[0-9]+$",),
            cursor=cursor,
        )

        if not row:
            return 0

        return int(row[0] or 0)

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @classmethod
    def _build_status_filter(
        cls,
        status_filter: str,
        *,
        table_alias: str = "p",
        include_where: bool = True,
    ) -> tuple[str, list[Any]]:
        normalized = cls._normalize_status_filter(
            status_filter
        )

        prefix = "WHERE" if include_where else "AND"

        if normalized == "Active":
            return (
                f"{prefix} {table_alias}.is_active = TRUE",
                [],
            )

        if normalized == "Inactive":
            return (
                f"{prefix} {table_alias}.is_active = FALSE",
                [],
            )

        return "", []

    @staticmethod
    def _normalize_status_filter(
        status_filter: str,
    ) -> str:
        normalized = str(
            status_filter or "Active"
        ).strip().lower()

        values = {
            "active": "Active",
            "inactive": "Inactive",
            "all": "All",
        }

        if normalized not in values:
            raise ValueError(
                "Status filter must be Active, Inactive, or All."
            )

        return values[normalized]

    @staticmethod
    def _map_project(
        row,
    ) -> dict | None:
        if not row:
            return None

        return {
            "id": str(row[0]),
            "project_code": row[1] or "",
            "project_name": row[2] or "",
            "client_id": str(row[3]),
            "client_code": row[4] or "",
            "client_name": row[5] or "",
            "remarks": row[6] or "",
            "is_active": bool(row[7]),
            "created_at": row[8],
            "created_by": (
                str(row[9])
                if row[9] is not None
                else None
            ),
            "updated_at": row[10],
            "updated_by": (
                str(row[11])
                if row[11] is not None
                else None
            ),
        }