from core.database.repositories.base_repository import BaseRepository


class JobTitleRepository(BaseRepository):
    """
    PostgreSQL data-access repository for core.job_titles.

    Contains job-title database operations only.
    Business rules and permission checks belong to services.
    """

    @classmethod
    def get_by_id(
        cls,
        job_title_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                jt.id,
                jt.job_title_code,
                jt.job_title_name,
                jt.department_id,
                d.department_code,
                d.department_name,
                jt.description,
                jt.is_active,
                jt.created_at,
                jt.updated_at
            FROM core.job_titles jt
            LEFT JOIN core.departments d
                ON jt.department_id = d.id
            WHERE jt.id = %s
            """,
            (job_title_id,),
            cursor=cursor,
        )

        return cls._map_job_title(row)

    @classmethod
    def get_by_code(
        cls,
        job_title_code: str,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                jt.id,
                jt.job_title_code,
                jt.job_title_name,
                jt.department_id,
                d.department_code,
                d.department_name,
                jt.description,
                jt.is_active,
                jt.created_at,
                jt.updated_at
            FROM core.job_titles jt
            LEFT JOIN core.departments d
                ON jt.department_id = d.id
            WHERE LOWER(jt.job_title_code) = LOWER(%s)
            """,
            (job_title_code,),
            cursor=cursor,
        )

        return cls._map_job_title(row)

    @classmethod
    def get_all(
        cls,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                jt.id,
                jt.job_title_code,
                jt.job_title_name,
                jt.department_id,
                d.department_code,
                d.department_name,
                jt.description,
                jt.is_active,
                jt.created_at,
                jt.updated_at
            FROM core.job_titles jt
            LEFT JOIN core.departments d
                ON jt.department_id = d.id
            ORDER BY
                d.department_name,
                jt.job_title_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_job_title(row)
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
                jt.id,
                jt.job_title_code,
                jt.job_title_name,
                jt.department_id,
                d.department_code,
                d.department_name,
                jt.description,
                jt.is_active,
                jt.created_at,
                jt.updated_at
            FROM core.job_titles jt
            LEFT JOIN core.departments d
                ON jt.department_id = d.id
            WHERE jt.is_active = TRUE
            ORDER BY
                d.department_name,
                jt.job_title_name
            """,
            cursor=cursor,
        )

        return [
            cls._map_job_title(row)
            for row in rows
        ]

    @classmethod
    def get_by_department(
        cls,
        department_id,
        *,
        active_only=False,
        cursor=None,
    ) -> list[dict]:
        query = """
            SELECT
                jt.id,
                jt.job_title_code,
                jt.job_title_name,
                jt.department_id,
                d.department_code,
                d.department_name,
                jt.description,
                jt.is_active,
                jt.created_at,
                jt.updated_at
            FROM core.job_titles jt
            LEFT JOIN core.departments d
                ON jt.department_id = d.id
            WHERE jt.department_id = %s
        """

        if active_only:
            query += """
                AND jt.is_active = TRUE
            """

        query += """
            ORDER BY jt.job_title_name
        """

        rows = cls.fetch_all(
            query,
            (department_id,),
            cursor=cursor,
        )

        return [
            cls._map_job_title(row)
            for row in rows
        ]

    @classmethod
    def job_title_code_exists(
        cls,
        job_title_code: str,
        *,
        exclude_job_title_id=None,
        cursor=None,
    ) -> bool:
        if exclude_job_title_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.job_titles
                    WHERE LOWER(job_title_code) = LOWER(%s)
                      AND id <> %s
                )
                """,
                (
                    job_title_code,
                    exclude_job_title_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.job_titles
                WHERE LOWER(job_title_code) = LOWER(%s)
            )
            """,
            (job_title_code,),
            cursor=cursor,
        )

    @classmethod
    def job_title_name_exists(
        cls,
        job_title_name: str,
        department_id,
        *,
        exclude_job_title_id=None,
        cursor=None,
    ) -> bool:
        if exclude_job_title_id:
            return cls.exists(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM core.job_titles
                    WHERE LOWER(job_title_name) = LOWER(%s)
                      AND department_id = %s
                      AND id <> %s
                )
                """,
                (
                    job_title_name,
                    department_id,
                    exclude_job_title_id,
                ),
                cursor=cursor,
            )

        return cls.exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM core.job_titles
                WHERE LOWER(job_title_name) = LOWER(%s)
                  AND department_id = %s
            )
            """,
            (
                job_title_name,
                department_id,
            ),
            cursor=cursor,
        )

    @classmethod
    def count_job_titles(
        cls,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.job_titles
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
            FROM core.job_titles
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
            INSERT INTO core.job_titles (
                job_title_code,
                job_title_name,
                department_id,
                description,
                is_active
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                data["job_title_code"],
                data["job_title_name"],
                data.get("department_id"),
                data.get("description"),
                data.get("is_active", True),
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Job title was not created."
            )

        return str(row[0])

    @classmethod
    def update(
        cls,
        job_title_id,
        data: dict,
        *,
        cursor=None,
    ) -> bool:
        allowed_columns = {
            "job_title_code",
            "job_title_name",
            "department_id",
            "description",
            "is_active",
        }

        updates = []
        params = []

        for column, value in data.items():
            if column not in allowed_columns:
                raise ValueError(
                    f"Job title column is not updateable: {column}"
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
        params.append(job_title_id)

        affected_rows = cls.execute(
            f"""
            UPDATE core.job_titles
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
        job_title_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.job_titles
            SET
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (job_title_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @classmethod
    def disable(
        cls,
        job_title_id,
        *,
        cursor=None,
    ) -> bool:
        affected_rows = cls.execute(
            """
            UPDATE core.job_titles
            SET
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (job_title_id,),
            cursor=cursor,
        )

        return affected_rows > 0

    @staticmethod
    def _map_job_title(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "job_title_code": row[1],
            "job_title_name": row[2],
            "department_id": (
                str(row[3])
                if row[3]
                else None
            ),
            "department_code": row[4] or "",
            "department_name": row[5] or "",
            "description": row[6] or "",
            "is_active": bool(row[7]),
            "created_at": row[8],
            "updated_at": row[9],
        }