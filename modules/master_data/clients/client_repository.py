from typing import Any

from core.database.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository):
    """
    PostgreSQL repository for Client Master records.

    Responsibilities:
    - Read and write records in master.clients.
    - Convert raw database rows into dictionaries.
    - Support standalone operations and shared transactions.
    """

    COLUMNS = """
        c.id,
        c.client_code,
        c.client_name,
        c.contact_person,
        c.phone,
        c.email,
        c.address,
        c.remarks,
        c.is_active,
        c.created_by,
        c.created_at,
        c.updated_by,
        c.updated_at
    """

    @classmethod
    def create(
        cls,
        *,
        client_code: str,
        client_name: str,
        created_by: Any,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        remarks: str | None = None,
        cursor=None,
    ) -> dict:
        """
        Create a Client Master record and return the saved record.
        """
        query = """
            INSERT INTO master.clients (
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                created_by
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING
                id,
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                is_active,
                created_by,
                created_at,
                updated_by,
                updated_at
        """

        row = cls.execute_returning(
            query,
            (
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                created_by,
            ),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def update(
        cls,
        client_id: Any,
        *,
        client_name: str,
        updated_by: Any,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        remarks: str | None = None,
        cursor=None,
    ) -> dict | None:
        """
        Update an existing Client Master record.

        The system-generated client code is not changed.
        """
        query = """
            UPDATE master.clients
            SET
                client_name = %s,
                contact_person = %s,
                phone = %s,
                email = %s,
                address = %s,
                remarks = %s,
                updated_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING
                id,
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                is_active,
                created_by,
                created_at,
                updated_by,
                updated_at
        """

        row = cls.execute_returning(
            query,
            (
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                updated_by,
                client_id,
            ),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def get_by_id(
        cls,
        client_id: Any,
        *,
        cursor=None,
    ) -> dict | None:
        query = f"""
            SELECT
                {cls.COLUMNS}
            FROM master.clients c
            WHERE c.id = %s
        """

        row = cls.fetch_one(
            query,
            (client_id,),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def get_by_code(
        cls,
        client_code: str,
        *,
        cursor=None,
    ) -> dict | None:
        query = f"""
            SELECT
                {cls.COLUMNS}
            FROM master.clients c
            WHERE UPPER(BTRIM(c.client_code)) =
                  UPPER(BTRIM(%s))
        """

        row = cls.fetch_one(
            query,
            (client_code,),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def get_all(
        cls,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict]:
        """
        Retrieve clients using one of these filters:

        Active
        Inactive
        All
        """
        where_clause, params = cls._status_filter_clause(
            status_filter
        )

        query = f"""
            SELECT
                {cls.COLUMNS}
            FROM master.clients c
            {where_clause}
            ORDER BY
                c.is_active DESC,
                LOWER(c.client_name),
                c.client_code
        """

        rows = cls.fetch_all(
            query,
            params,
            cursor=cursor,
        )

        return [
            cls._row_to_dict(row)
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
    def search(
        cls,
        search_text: str = "",
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict]:
        """
        Search by client code, client name, contact person,
        telephone number, email, or address.
        """
        clean_search = str(search_text or "").strip()
        where_clause, status_params = cls._status_filter_clause(
            status_filter
        )

        conditions = []
        params = list(status_params)

        if where_clause:
            conditions.append(
                where_clause.replace("WHERE ", "", 1)
            )

        if clean_search:
            search_pattern = f"%{clean_search}%"

            conditions.append(
                """
                (
                    c.client_code ILIKE %s
                    OR c.client_name ILIKE %s
                    OR COALESCE(c.contact_person, '') ILIKE %s
                    OR COALESCE(c.phone, '') ILIKE %s
                    OR COALESCE(c.email, '') ILIKE %s
                    OR COALESCE(c.address, '') ILIKE %s
                )
                """
            )

            params.extend([search_pattern] * 6)

        final_where = ""

        if conditions:
            final_where = (
                "WHERE "
                + " AND ".join(conditions)
            )

        query = f"""
            SELECT
                {cls.COLUMNS}
            FROM master.clients c
            {final_where}
            ORDER BY
                c.is_active DESC,
                LOWER(c.client_name),
                c.client_code
        """

        rows = cls.fetch_all(
            query,
            tuple(params),
            cursor=cursor,
        )

        return [
            cls._row_to_dict(row)
            for row in rows
        ]

    @classmethod
    def deactivate(
        cls,
        client_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        """
        Soft-delete a client by setting is_active to FALSE.
        """
        query = """
            UPDATE master.clients
            SET
                is_active = FALSE,
                updated_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND is_active = TRUE
            RETURNING
                id,
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                is_active,
                created_by,
                created_at,
                updated_by,
                updated_at
        """

        row = cls.execute_returning(
            query,
            (
                updated_by,
                client_id,
            ),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def activate(
        cls,
        client_id: Any,
        *,
        updated_by: Any,
        cursor=None,
    ) -> dict | None:
        """
        Restore an inactive client by setting is_active to TRUE.
        """
        query = """
            UPDATE master.clients
            SET
                is_active = TRUE,
                updated_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND is_active = FALSE
            RETURNING
                id,
                client_code,
                client_name,
                contact_person,
                phone,
                email,
                address,
                remarks,
                is_active,
                created_by,
                created_at,
                updated_by,
                updated_at
        """

        row = cls.execute_returning(
            query,
            (
                updated_by,
                client_id,
            ),
            cursor=cursor,
        )

        return cls._row_to_dict(row)

    @classmethod
    def name_exists(
        cls,
        client_name: str,
        *,
        exclude_client_id: Any | None = None,
        active_only: bool = True,
        cursor=None,
    ) -> bool:
        """
        Check whether a matching client name already exists.

        Matching is case-insensitive and ignores outer spaces.
        """
        conditions = [
            """
            LOWER(BTRIM(client_name)) =
            LOWER(BTRIM(%s))
            """
        ]

        params: list[Any] = [client_name]

        if exclude_client_id:
            conditions.append("id <> %s")
            params.append(exclude_client_id)

        if active_only:
            conditions.append("is_active = TRUE")

        query = f"""
            SELECT EXISTS (
                SELECT 1
                FROM master.clients
                WHERE {" AND ".join(conditions)}
            )
        """

        return cls.exists(
            query,
            tuple(params),
            cursor=cursor,
        )

    @classmethod
    def code_exists(
        cls,
        client_code: str,
        *,
        cursor=None,
    ) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM master.clients
                WHERE UPPER(BTRIM(client_code)) =
                      UPPER(BTRIM(%s))
            )
        """

        return cls.exists(
            query,
            (client_code,),
            cursor=cursor,
        )

    @classmethod
    def get_highest_code_number(
        cls,
        *,
        cursor=None,
    ) -> int:
        """
        Return the largest numeric portion of a CLI code.

        Examples:
            CLI-000001 -> 1
            CLI-000125 -> 125
        """
        query = """
            SELECT COALESCE(
                MAX(
                    CAST(
                        SUBSTRING(
                            client_code
                            FROM '^CLI-([0-9]+)$'
                        )
                        AS INTEGER
                    )
                ),
                0
            )
            FROM master.clients
            WHERE client_code ~ '^CLI-[0-9]+$'
        """

        row = cls.fetch_one(
            query,
            cursor=cursor,
        )

        if not row:
            return 0

        return int(row[0] or 0)

    @staticmethod
    def _status_filter_clause(
        status_filter: str,
    ) -> tuple[str, tuple]:
        normalized_filter = (
            str(status_filter or "Active")
            .strip()
            .lower()
        )

        if normalized_filter == "all":
            return "", ()

        if normalized_filter == "inactive":
            return "WHERE c.is_active = FALSE", ()

        return "WHERE c.is_active = TRUE", ()

    @staticmethod
    def _row_to_dict(
        row,
    ) -> dict | None:
        if not row:
            return None

        return {
            "id": row[0],
            "client_code": row[1],
            "client_name": row[2],
            "contact_person": row[3],
            "phone": row[4],
            "email": row[5],
            "address": row[6],
            "remarks": row[7],
            "is_active": row[8],
            "created_by": row[9],
            "created_at": row[10],
            "updated_by": row[11],
            "updated_at": row[12],
        }