"""
JCAP Construction Suite
Fake Base Repository

Provides reusable in-memory storage and call tracking for repository test doubles.
It is designed for inheritance by module-specific fake repositories.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any, Generic, TypeVar
from uuid import UUID

RecordT = TypeVar("RecordT")
KeyT = TypeVar("KeyT")


class FakeBaseRepository(Generic[KeyT, RecordT]):
    """
    Reusable in-memory repository test double.

    Features:
    - Isolated record storage
    - Deterministic CRUD behavior
    - Method call history
    - Configurable method results
    - Configurable method exceptions
    - Reset support for test isolation
    """

    def __init__(
        self,
        records: Mapping[KeyT, RecordT] | Iterable[tuple[KeyT, RecordT]] | None = None,
    ) -> None:
        self._initial_records: dict[KeyT, RecordT] = self._normalize_records(records)
        self._records: dict[KeyT, RecordT] = deepcopy(self._initial_records)
        self._calls: dict[str, list[dict[str, Any]]] = {}
        self._configured_results: dict[str, Any] = {}
        self._configured_exceptions: dict[str, Exception] = {}

    @staticmethod
    def _normalize_records(
        records: Mapping[KeyT, RecordT] | Iterable[tuple[KeyT, RecordT]] | None,
    ) -> dict[KeyT, RecordT]:
        """Normalize optional seed data into a dictionary."""
        if records is None:
            return {}

        if isinstance(records, Mapping):
            return dict(records)

        return dict(records)

    @property
    def records(self) -> dict[KeyT, RecordT]:
        """Return a deep copy of all stored records."""
        return deepcopy(self._records)

    def seed(
        self,
        key: KeyT,
        record: RecordT,
        *,
        overwrite: bool = True,
    ) -> None:
        """Insert seed data directly into the in-memory store."""
        if not overwrite and key in self._records:
            raise KeyError(f"Record with key {key!r} already exists.")

        self._records[key] = deepcopy(record)

    def seed_many(
        self,
        records: Mapping[KeyT, RecordT] | Iterable[tuple[KeyT, RecordT]],
        *,
        overwrite: bool = True,
    ) -> None:
        """Insert multiple records directly into the in-memory store."""
        for key, record in self._normalize_records(records).items():
            self.seed(key, record, overwrite=overwrite)

    def get_stored(self, key: KeyT) -> RecordT | None:
        """Return a deep copy of a stored record without tracking a call."""
        record = self._records.get(key)
        return deepcopy(record)

    def store(
        self,
        key: KeyT,
        record: RecordT,
        *,
        overwrite: bool = True,
    ) -> RecordT:
        """Store a record and return a safe copy."""
        if not overwrite and key in self._records:
            raise KeyError(f"Record with key {key!r} already exists.")

        self._records[key] = deepcopy(record)
        return deepcopy(self._records[key])

    def remove_stored(self, key: KeyT) -> RecordT | None:
        """Remove and return a stored record without tracking a call."""
        record = self._records.pop(key, None)
        return deepcopy(record)

    def clear_storage(self) -> None:
        """Remove all records from the in-memory store."""
        self._records.clear()

    def record_call(self, method_name: str, **arguments: Any) -> None:
        """
        Record one repository method invocation.

        Cursor objects are intentionally preserved by identity. Other arguments
        are deep-copied so later mutation by the caller cannot alter call history.
        """
        normalized_name = self._validate_method_name(method_name)
        self._calls.setdefault(normalized_name, []).append(
            self._copy_call_arguments(arguments)
        )

    def calls_for(self, method_name: str) -> list[dict[str, Any]]:
        """
        Return safe copies of recorded calls.

        Cursor identity remains unchanged so cursor-forwarding tests can use
        assertIs() or direct equality with opaque cursor sentinels.
        """
        normalized_name = self._validate_method_name(method_name)
        return [
            self._copy_call_arguments(arguments)
            for arguments in self._calls.get(normalized_name, [])
        ]

    def call_count(self, method_name: str) -> int:
        """Return the number of recorded calls for a method."""
        normalized_name = self._validate_method_name(method_name)
        return len(self._calls.get(normalized_name, []))

    def was_called(self, method_name: str) -> bool:
        """Return whether a method was called at least once."""
        return self.call_count(method_name) > 0

    def last_call(self, method_name: str) -> dict[str, Any] | None:
        """Return the most recent recorded call for a method."""
        calls = self.calls_for(method_name)
        return calls[-1] if calls else None

    def clear_calls(self, method_name: str | None = None) -> None:
        """Clear call history for one method or for all methods."""
        if method_name is None:
            self._calls.clear()
            return

        normalized_name = self._validate_method_name(method_name)
        self._calls.pop(normalized_name, None)

    def configure_result(self, method_name: str, result: Any) -> None:
        """Configure a predefined result for a repository method."""
        normalized_name = self._validate_method_name(method_name)
        self._configured_results[normalized_name] = deepcopy(result)
        self._configured_exceptions.pop(normalized_name, None)

    def configured_result(
        self,
        method_name: str,
        default: Any = None,
    ) -> Any:
        """Return a configured method result or the supplied default."""
        normalized_name = self._validate_method_name(method_name)

        if normalized_name not in self._configured_results:
            return deepcopy(default)

        return deepcopy(self._configured_results[normalized_name])

    def has_configured_result(self, method_name: str) -> bool:
        """Return whether a method has a configured result."""
        normalized_name = self._validate_method_name(method_name)
        return normalized_name in self._configured_results

    def configure_exception(
        self,
        method_name: str,
        exception: Exception,
    ) -> None:
        """Configure an exception to be raised for a repository method."""
        if not isinstance(exception, Exception):
            raise TypeError("exception must be an Exception instance.")

        normalized_name = self._validate_method_name(method_name)
        self._configured_exceptions[normalized_name] = exception
        self._configured_results.pop(normalized_name, None)

    def raise_if_configured(self, method_name: str) -> None:
        """Raise the configured exception for a method, when present."""
        normalized_name = self._validate_method_name(method_name)
        exception = self._configured_exceptions.get(normalized_name)

        if exception is not None:
            raise exception

    def clear_configuration(self, method_name: str | None = None) -> None:
        """Clear configured results and exceptions."""
        if method_name is None:
            self._configured_results.clear()
            self._configured_exceptions.clear()
            return

        normalized_name = self._validate_method_name(method_name)
        self._configured_results.pop(normalized_name, None)
        self._configured_exceptions.pop(normalized_name, None)

    def reset(self, *, restore_seed_data: bool = True) -> None:
        """Reset call history, configured behavior, and repository storage."""
        self.clear_calls()
        self.clear_configuration()

        if restore_seed_data:
            self._records = deepcopy(self._initial_records)
        else:
            self._records.clear()

    @staticmethod
    def ensure_uuid(value: UUID | str, field_name: str = "id") -> UUID:
        """Convert a UUID-compatible value into a UUID instance."""
        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as exc:
                raise ValueError(
                    f"{field_name} must contain a valid UUID value."
                ) from exc

        raise TypeError(
            f"{field_name} must be a UUID or UUID string, "
            f"not {type(value).__name__}."
        )

    @staticmethod
    def _copy_call_arguments(
        arguments: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Copy recorded arguments while preserving cursor identity.

        Database cursors and test cursor sentinels are opaque identity-bearing
        objects. Deep-copying them produces a different object and invalidates
        cursor-forwarding assertions.
        """
        copied: dict[str, Any] = {}

        for argument_name, value in arguments.items():
            copied[argument_name] = (
                value
                if argument_name == "cursor"
                else deepcopy(value)
            )

        return copied

    @staticmethod
    def _validate_method_name(method_name: str) -> str:
        """Validate and normalize a repository method name."""
        if not isinstance(method_name, str):
            raise TypeError("method_name must be a string.")

        normalized_name = method_name.strip()

        if not normalized_name:
            raise ValueError("method_name must be a non-empty string.")

        return normalized_name