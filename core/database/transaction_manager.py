"""
Database Transaction Manager.

Coordinates multiple repository and service operations inside one
PostgreSQL transaction.
"""

from __future__ import annotations

from typing import Any

from core.database.connection import get_connection


class TransactionManager:
    """
    Manage one PostgreSQL transaction as a context manager.

    Usage:

        with TransactionManager() as cursor:
            RepositoryA.update(..., cursor=cursor)
            RepositoryB.create(..., cursor=cursor)

    The transaction commits when the managed block succeeds, rolls back
    when it raises an exception, and always closes its resources.
    Exceptions are never suppressed.
    """

    def __init__(self) -> None:
        self._connection: Any | None = None
        self._cursor: Any | None = None

    @property
    def connection(self):
        if self._connection is None:
            raise RuntimeError(
                "TransactionManager has no active database connection."
            )
        return self._connection

    @property
    def cursor(self):
        if self._cursor is None:
            raise RuntimeError(
                "TransactionManager has no active database cursor."
            )
        return self._cursor

    def __enter__(self):
        if self._connection is not None or self._cursor is not None:
            raise RuntimeError(
                "TransactionManager instances cannot be entered twice."
            )

        self._connection = get_connection()

        try:
            self._cursor = self._connection.cursor()
        except Exception:
            self._connection.close()
            self._connection = None
            raise

        return self._cursor

    def __exit__(
        self,
        exception_type,
        exception_value,
        traceback,
    ) -> bool:
        try:
            if self._connection is not None:
                if exception_type is None:
                    self._connection.commit()
                else:
                    self._connection.rollback()
        finally:
            if self._cursor is not None:
                self._cursor.close()

            if self._connection is not None:
                self._connection.close()

            self._cursor = None
            self._connection = None

        return False