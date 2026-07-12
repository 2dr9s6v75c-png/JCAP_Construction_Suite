from core.database.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository):
    """
    PostgreSQL data-access repository for permissions
    and role-permission assignments.

    Business permission decisions belong to PermissionService
    and OrganizationService.

    This repository only reads and modifies permission data.
    """

    # ============================================================
    # PERMISSION READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        permission_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                permission_name,
                description
            FROM core.permissions
            WHERE id = %s
            """,
            (permission_id,),
            cursor=cursor,
        )

        return cls._map_permission(row)

    @classmethod
    def get_by_name(
        cls,
        permission_name: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                id,
                permission_name,
                description
            FROM core.permissions
            WHERE LOWER(permission_name) = LOWER(%s)
            """,
            (permission_name,),
            cursor=cursor,
        )

        return cls._map_permission(row)

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
                permission_name,
                description
            FROM core.permissions
            ORDER BY permission_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_permission(row)
            for row in rows
        ]

    @classmethod
    def get_all_permissions(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        """
        Explicit matrix-friendly alias for get_all().

        Retained separately so Administration UI code clearly
        communicates that it is loading the permission registry.
        """

        return cls.get_all(
            cursor=cursor
        )

    @classmethod
    def get_by_role(
        cls,
        role_id,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                p.id,
                p.permission_name,
                p.description
            FROM core.permissions p
            INNER JOIN core.role_permissions rp
                ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.permission_name
            """,
            (role_id,),
            cursor=cursor,
        )

        return [
            cls._map_permission(row)
            for row in rows
        ]

    # ============================================================
    # MATRIX READ OPERATIONS
    # ============================================================

    @classmethod
    def get_permission_matrix(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        """
        Return every permission with all active role assignments.

        Result example:

            {
                "id": "...",
                "permission_name": "material_requests.create",
                "description": "Create Material Requests",
                "role_ids": ["...", "..."],
            }

        The Administration UI may use this to construct a visual
        permission matrix without issuing one query per permission.
        """

        rows = cls.fetch_all(
            """
            SELECT
                p.id,
                p.permission_name,
                p.description,
                r.id,
                r.role_name
            FROM core.permissions p
            LEFT JOIN core.role_permissions rp
                ON rp.permission_id = p.id
            LEFT JOIN core.roles r
                ON r.id = rp.role_id
            ORDER BY
                p.permission_name,
                r.role_name
            """,
            cursor=cursor,
        )

        permissions = {}

        for row in rows:
            permission_id = str(row[0])

            if permission_id not in permissions:
                permissions[permission_id] = {
                    "id": permission_id,
                    "permission_name": row[1],
                    "description": row[2] or "",
                    "role_ids": [],
                    "roles": [],
                }

            role_id = row[3]
            role_name = row[4]

            if role_id:
                role_id = str(role_id)

                permissions[
                    permission_id
                ]["role_ids"].append(
                    role_id
                )

                permissions[
                    permission_id
                ]["roles"].append(
                    {
                        "id": role_id,
                        "role_name": role_name,
                    }
                )

        return list(
            permissions.values()
        )

    @classmethod
    def get_all_roles_with_permissions(
        cls,
        *,
        active_roles_only=True,
        cursor=None,
    ) -> list[dict]:
        """
        Return roles together with their assigned permissions.

        This is optimized for the role-focused Administration UI.

        Result example:

            {
                "id": "...",
                "role_name": "Purchasing Officer",
                "description": "...",
                "is_active": True,
                "permissions": [
                    {
                        "id": "...",
                        "permission_name": "...",
                        "description": "...",
                    }
                ],
            }
        """

        query = """
            SELECT
                r.id,
                r.role_name,
                r.description,
                r.is_active,
                p.id,
                p.permission_name,
                p.description
            FROM core.roles r
            LEFT JOIN core.role_permissions rp
                ON rp.role_id = r.id
            LEFT JOIN core.permissions p
                ON p.id = rp.permission_id
        """

        params = ()

        if active_roles_only:
            query += """
                WHERE r.is_active = TRUE
            """

        query += """
            ORDER BY
                r.role_name,
                p.permission_name
        """

        rows = cls.fetch_all(
            query,
            params,
            cursor=cursor,
        )

        roles = {}

        for row in rows:
            role_id = str(row[0])

            if role_id not in roles:
                roles[role_id] = {
                    "id": role_id,
                    "role_name": row[1],
                    "description": row[2] or "",
                    "is_active": bool(row[3]),
                    "permissions": [],
                    "permission_ids": [],
                }

            permission_id = row[4]

            if permission_id:
                permission_id = str(
                    permission_id
                )

                roles[
                    role_id
                ]["permission_ids"].append(
                    permission_id
                )

                roles[
                    role_id
                ]["permissions"].append(
                    {
                        "id": permission_id,
                        "permission_name": row[5],
                        "description": row[6] or "",
                    }
                )

        return list(
            roles.values()
        )

    # ============================================================
    # EXISTENCE AND PERMISSION CHECKS
    # ============================================================

    @classmethod
    def permission_name_exists(
        cls,
        permission_name: str,
        *,
        exclude_permission_id=None,
        cursor=None,
    ) -> bool:
        if exclude_permission_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.permissions
                    WHERE LOWER(permission_name) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    permission_name,
                    exclude_permission_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.permissions
                WHERE LOWER(permission_name) = LOWER(%s)
            )
            """,
            (permission_name,),
            cursor=cursor,
        )

    @classmethod
    def role_has_permission(
        cls,
        role_id,
        permission_id,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.role_permissions
                WHERE role_id = %s
                  AND permission_id = %s
            )
            """,
            (
                role_id,
                permission_id,
            ),
            cursor=cursor,
        )

    @classmethod
    def role_has_permission_name(
        cls,
        role_id,
        permission_name: str,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.role_permissions rp
                INNER JOIN core.permissions p
                    ON p.id = rp.permission_id
                WHERE rp.role_id = %s
                  AND LOWER(p.permission_name) = LOWER(%s)
            )
            """,
            (
                role_id,
                permission_name,
            ),
            cursor=cursor,
        )

    # ============================================================
    # COUNTS
    # ============================================================

    @classmethod
    def count_permissions(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.permissions
            """,
            cursor=cursor,
        )

    @classmethod
    def count_by_role(
        cls,
        role_id,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.role_permissions
            WHERE role_id = %s
            """,
            (role_id,),
            cursor=cursor,
        )

    # ============================================================
    # PERMISSION REGISTRY WRITE OPERATIONS
    # ============================================================

    @classmethod
    def create(
        cls,
        data: dict,
        *,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO core.permissions (
                permission_name,
                description
            )
            VALUES (
                %s,
                %s
            )
            RETURNING id
            """,
            (
                data["permission_name"],
                data.get("description"),
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Permission was not created."
            )

        return str(row[0])

    @classmethod
    def update(
        cls,
        permission_id,
        data: dict,
        *,
        cursor=None,
    ) -> bool:
        allowed_columns = {
            "permission_name",
            "description",
        }

        updates = []
        params = []

        for column, value in data.items():
            if column not in allowed_columns:
                raise ValueError(
                    (
                        "Permission column is not "
                        f"updateable: {column}"
                    )
                )

            updates.append(
                f"{column} = %s"
            )

            params.append(
                value
            )

        if not updates:
            return False

        params.append(
            permission_id
        )

        affected_rows = cls.execute(
            f"""
            UPDATE core.permissions
            SET
                {", ".join(updates)}
            WHERE id = %s
            """,
            params,
            cursor=cursor,
        )

        return affected_rows > 0

    # ============================================================
    # ROLE PERMISSION ASSIGNMENTS
    # ============================================================

    @classmethod
    def assign_permission(
        cls,
        role_id,
        permission_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            INSERT INTO core.role_permissions (
                role_id,
                permission_id
            )
            VALUES (
                %s,
                %s
            )
            ON CONFLICT (
                role_id,
                permission_id
            )
            DO NOTHING
            """,
            (
                role_id,
                permission_id,
            ),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def remove_permission(
        cls,
        role_id,
        permission_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            DELETE FROM core.role_permissions
            WHERE role_id = %s
              AND permission_id = %s
            """,
            (
                role_id,
                permission_id,
            ),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def replace_role_permissions(
        cls,
        role_id,
        permission_ids,
        *,
        cursor=None,
    ) -> bool:
        """
        Replace all permissions assigned to a role.

        For atomic behavior, OrganizationService should call this
        method with a shared transaction cursor.
        """

        cls.execute(
            """
            DELETE FROM core.role_permissions
            WHERE role_id = %s
            """,
            (role_id,),
            cursor=cursor,
        )

        for permission_id in permission_ids:
            cls.assign_permission(
                role_id,
                permission_id,
                cursor=cursor,
            )

        return True

    # ============================================================
    # ROW MAPPING
    # ============================================================

    @staticmethod
    def _map_permission(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "permission_name": row[1],
            "description": row[2] or "",
        }