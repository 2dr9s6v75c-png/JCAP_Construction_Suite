from __future__ import annotations

from typing import Any

from core.database.repositories.base_repository import BaseRepository


class SiteRepository(BaseRepository):
    """
    PostgreSQL data-access repository for Site Master records.

    Business validation, permissions, transactions, code generation,
    and activity logging belong to SiteService.
    """

    _SELECT_COLUMNS = """
        s.id,
        s.site_code,
        s.site_name,
        s.project_id,
        p.project_code,
        p.project_name,
        p.client_id,
        c.client_code,
        c.client_name,
        s.remarks,
        s.is_active,
        s.created_at,
        s.created_by,
        s.updated_at,
        s.updated_by
    """

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        site_id: Any,
        *,
        cursor=None,
    ) -> dict | None:
        row = cls.fetch_one(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE s.id = %s
            """,
            (site_id,),
            cursor=cursor,
        )

        return cls._map_site(row)

    @classmethod
    def get_by_code(
        cls,
        site_code: str,
        *,
        cursor=None,
    ) -> dict | None:
        row = cls.fetch_one(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE LOWER(s.site_code) = LOWER(%s)
            """,
            (site_code,),
            cursor=cursor,
        )

        return cls._map_site(row)

    @classmethod
    def get_by_name(
        cls,
        site_name: str,
        *,
        project_id: Any | None = None,
        active_only: bool = False,
        cursor=None,
    ) -> dict | None:
        query = f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE LOWER(BTRIM(s.site_name))
                = LOWER(BTRIM(%s))
        """

        params: list[Any] = [site_name]

        if project_id is not None:
            query += """
                AND s.project_id = %s
            """
            params.append(project_id)

        if active_only:
            query += """
                AND s.is_active = TRUE
            """

        query += """
            ORDER BY s.is_active DESC, s.created_at DESC
            LIMIT 1
        """

        row = cls.fetch_one(
            query,
            params,
            cursor=cursor,
        )

        return cls._map_site(row)

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
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            {where_clause}
            ORDER BY
                s.is_active DESC,
                c.client_name,
                p.project_name,
                s.site_name,
                s.site_code
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_site(row)
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
    def get_by_project(
        cls,
        project_id: Any,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict]:
        status_clause, status_params = cls._build_status_filter(
            status_filter,
            table_alias="s",
            include_where=False,
        )

        rows = cls.fetch_all(
            f"""
            SELECT
                {cls._SELECT_COLUMNS}
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            WHERE s.project_id = %s
            {status_clause}
            ORDER BY
                s.is_active DESC,
                s.site_name,
                s.site_code
            """,
            [project_id, *status_params],
            cursor=cursor,
        )

        return [
            cls._map_site(row)
            for row in rows
        ]

    @classmethod
    def search(
        cls,
        search_text: str = "",
        status_filter: str = "Active",
        *,
        project_id: Any | None = None,
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
                    s.site_code ILIKE %s
                    OR s.site_name ILIKE %s
                    OR p.project_code ILIKE %s
                    OR p.project_name ILIKE %s
                    OR c.client_code ILIKE %s
                    OR c.client_name ILIKE %s
                    OR COALESCE(s.remarks, '') ILIKE %s
                )
                """
            )
            params.extend([search_pattern] * 7)

        if project_id is not None:
            conditions.append("s.project_id = %s")
            params.append(project_id)

        if client_id is not None:
            conditions.append("p.client_id = %s")
            params.append(client_id)

        normalized_status = cls._normalize_status_filter(
            status_filter
        )

        if normalized_status == "Active":
            conditions.append("s.is_active = TRUE")
        elif normalized_status == "Inactive":
            conditions.append("s.is_active = FALSE")

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
            FROM master.sites s
            INNER JOIN master.projects p
                ON p.id = s.project_id
            INNER JOIN master.clients c
                ON c.id = p.client_id
            {where_clause}
            ORDER BY
                s.is_active DESC,
                c.client_name,
                p.project_name,
                s.site_name,
                s.site_code
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_site(row)
            for row in rows
        ]

    # ============================================================
    # CREATE / UPDATE
    # ============================================================

    @classmethod
    def create(
        cls,
        *,
        site_code: str,
        site_name: str,
        project_id: Any,
        remarks: str | None,
        created_by: Any,
        cursor=None,
    ) -> dict:
        row = cls.execute_returning(
            """
            INSERT INTO master.sites (
                site_code,
                site_name,
                project_id,
                remarks,
                is_active,
                created_by,
                updated_by
            )
            VALUES (%s, %s, %s, %s, TRUE, %s, %s)
            RETURNING id
            """,
            (
                site_code,
                site_name,
                project_id,
                remarks,
                created_by,
                created_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Site Master record could not be created."
            )

        site = cls.get_by_id(
            row[0],
            cursor=cursor,
        )

        if site is None:
            raise RuntimeError(
                "The created Site Master record could not be loaded."
            )

        return site

    @classmethod
    def update(
        cls,
        site_id: Any,
        *,
        site_name: str,
        project_id: Any,
        remarks: str | None,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        row = cls.execute_returning(
            """
            UPDATE master.sites
            SET
                site_name = %s,
                project_id = %s,
                remarks = %s,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                site_name,
                project_id,
                remarks,
                updated_by,
                site_id,
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
        site_id: Any,
        *,
        is_active: bool,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        row = cls.execute_returning(
            """
            UPDATE master.sites
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
                site_id,
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
        site_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        return cls.set_active_status(
            site_id,
            is_active=False,
            updated_by=updated_by,
            cursor=cursor,
        )

    @classmethod
    def restore(
        cls,
        site_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        return cls.set_active_status(
            site_id,
            is_active=True,
            updated_by=updated_by,
            cursor=cursor,
        )

    # ============================================================
    # EXISTENCE CHECKS
    # ============================================================

    @classmethod
    def site_code_exists(
        cls,
        site_code: str,
        *,
        exclude_site_id: Any | None = None,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.sites
                WHERE LOWER(site_code) = LOWER(%s)
        """

        params: list[Any] = [site_code]

        if exclude_site_id is not None:
            query += """
                  AND id <> %s
            """
            params.append(exclude_site_id)

        query += """
            )
        """

        return cls.exists(
            query,
            params,
            cursor=cursor,
        )

    @classmethod
    def active_site_name_exists(
        cls,
        *,
        project_id: Any,
        site_name: str,
        exclude_site_id: Any | None = None,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.sites
                WHERE project_id = %s
                  AND LOWER(BTRIM(site_name))
                      = LOWER(BTRIM(%s))
                  AND is_active = TRUE
        """

        params: list[Any] = [
            project_id,
            site_name,
        ]

        if exclude_site_id is not None:
            query += """
                  AND id <> %s
            """
            params.append(exclude_site_id)

        query += """
            )
        """

        return cls.exists(
            query,
            params,
            cursor=cursor,
        )

    @classmethod
    def project_exists(
        cls,
        project_id: Any,
        *,
        active_only: bool = False,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.projects
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
            (project_id,),
            cursor=cursor,
        )

    # ============================================================
    # CODE GENERATION SUPPORT
    # ============================================================

    @classmethod
    def get_highest_code_number(
        cls,
        *,
        prefix: str = "SIT",
        cursor=None,
    ) -> int:
        """
        Return the highest numeric suffix currently used by site codes.

        Code-generation locking belongs to SiteService.
        """
        row = cls.fetch_one(
            """
            SELECT COALESCE(
                MAX(
                    CASE
                        WHEN site_code ~ %s
                        THEN SUBSTRING(
                            site_code
                            FROM '([0-9]+)$'
                        )::BIGINT
                        ELSE NULL
                    END
                ),
                0
            )
            FROM master.sites
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
        table_alias: str = "s",
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
    def _map_site(
        row,
    ) -> dict | None:
        if not row:
            return None

        return {
            "id": str(row[0]),
            "site_code": row[1] or "",
            "site_name": row[2] or "",
            "project_id": str(row[3]),
            "project_code": row[4] or "",
            "project_name": row[5] or "",
            "client_id": str(row[6]),
            "client_code": row[7] or "",
            "client_name": row[8] or "",
            "remarks": row[9] or "",
            "is_active": bool(row[10]),
            "created_at": row[11],
            "created_by": (
                str(row[12])
                if row[12] is not None
                else None
            ),
            "updated_at": row[13],
            "updated_by": (
                str(row[14])
                if row[14] is not None
                else None
            ),
        }