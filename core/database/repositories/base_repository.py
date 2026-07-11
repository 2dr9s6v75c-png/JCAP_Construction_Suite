from typing import Any

from core.database.connection import get_connection


class BaseRepository:
    """
    Base PostgreSQL repository for the JCAP Construction Suite.

    Repository methods may:

    1. Use their own database connection automatically.
    2. Join an existing transaction by receiving a shared cursor.

    Important:
    - When a shared cursor is supplied, BaseRepository does not commit,
      rollback, close the cursor, or close the connection.
    - The service that owns the transaction is responsible for commit
      and rollback.
    """

    @classmethod
    def fetch_one(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ):
        """
        Execute a SELECT query and return one raw database row.

        Returns:
            tuple | None

        Row-to-dictionary mapping belongs to the specific repository.
        """
        params = cls._normalize_params(params)

        if cursor is not None:
            cursor.execute(query, params)
            return cursor.fetchone()

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, params)
            return cur.fetchone()

        finally:
            cur.close()
            conn.close()

    @classmethod
    def fetch_all(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ) -> list:
        """
        Execute a SELECT query and return all raw database rows.

        Always returns a list.
        """
        params = cls._normalize_params(params)

        if cursor is not None:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return list(rows or [])

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            return list(rows or [])

        finally:
            cur.close()
            conn.close()

    @classmethod
    def execute(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ) -> int:
        """
        Execute INSERT, UPDATE, or DELETE SQL.

        Returns:
            Number of affected rows.

        If a shared cursor is supplied:
            - no commit is performed.

        If no shared cursor is supplied:
            - BaseRepository manages the transaction.
        """
        params = cls._normalize_params(params)

        if cursor is not None:
            cursor.execute(query, params)
            return cursor.rowcount

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, params)
            affected_rows = cur.rowcount

            conn.commit()

            return affected_rows

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    @classmethod
    def execute_returning(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ):
        """
        Execute SQL containing a PostgreSQL RETURNING clause.

        Returns:
            tuple | None

        Example:

            INSERT INTO ...
            RETURNING id
        """
        params = cls._normalize_params(params)

        if cursor is not None:
            cursor.execute(query, params)
            return cursor.fetchone()

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(query, params)
            row = cur.fetchone()

            conn.commit()

            return row

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    @classmethod
    def exists(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ) -> bool:
        """
        Execute an existence query.

        The SQL should normally return one boolean value.

        Example:

            SELECT EXISTS (
                SELECT 1
                FROM core.users
                WHERE username = %s
            )
        """
        row = cls.fetch_one(
            query,
            params,
            cursor=cursor,
        )

        if not row:
            return False

        return bool(row[0])

    @classmethod
    def count(
        cls,
        query: str,
        params: tuple | list | None = None,
        *,
        cursor=None,
    ) -> int:
        """
        Execute a COUNT query and return an integer.

        Example:

            SELECT COUNT(*)
            FROM core.users
        """
        row = cls.fetch_one(
            query,
            params,
            cursor=cursor,
        )

        if not row:
            return 0

        return int(row[0] or 0)

    @staticmethod
    def _normalize_params(
        params: tuple | list | None,
    ) -> tuple | list:
        """
        Normalize SQL parameters.

        psycopg accepts tuples and lists for parameterized queries.
        An empty tuple is used when no parameters are supplied.
        """
        if params is None:
            return ()

        if not isinstance(params, (tuple, list)):
            raise TypeError(
                "SQL parameters must be a tuple, list, or None."
            )

        return params