"""
JCAP Construction Suite
Base Service

Purpose
-------
Provides reusable validation and normalization helpers for application
services.

Responsibilities
----------------
- Validate required values.
- Validate permissions.
- Normalize text values.
- Validate and normalize UUID values.
- Provide consistent service-layer error messages.

Does NOT
--------
- Implement domain-specific business rules.
- Execute SQL.
- Access repositories.
- Open database connections.
- Manage transactions.
- Coordinate workflows.
- Send notifications.
- Write activity logs.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID


class BaseService:
    """Base class for JCAP Construction Suite application services."""

    @staticmethod
    def require_not_none(value: Any, field_name: str) -> Any:
        """Require a value that is not None."""
        if value is None:
            raise ValueError(f"{field_name} is required.")
        return value

    @classmethod
    def require_non_empty_string(cls, value: Any, field_name: str) -> str:
        """Require a non-empty normalized string."""
        normalized_value = cls.normalize_text(value)
        if not normalized_value:
            raise ValueError(f"{field_name} is required.")
        return normalized_value

    @staticmethod
    def require_mapping(value: Any, field_name: str) -> dict[str, Any]:
        """Require a dictionary-like service input."""
        if value is None:
            raise ValueError(f"{field_name} is required.")
        if not isinstance(value, dict):
            raise TypeError(f"{field_name} must be a dictionary.")
        return value

    @staticmethod
    def normalize_text(value: Any) -> str:
        """Convert a value to stripped text; None becomes an empty string."""
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        """Normalize optional text to stripped text or None."""
        normalized_value = cls.normalize_text(value)
        return normalized_value or None

    @staticmethod
    def normalize_uuid(value: Any, field_name: str = "ID") -> str:
        """Validate and normalize a UUID value to a canonical string."""
        if value is None:
            raise ValueError(f"{field_name} is required.")

        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError(f"{field_name} is required.")

        try:
            return str(UUID(normalized_value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"{field_name} must be a valid UUID.") from exc

    @classmethod
    def normalize_uuid_object(
        cls,
        value: UUID | str,
        field_name: str = "ID",
    ) -> UUID:
        """Validate and normalize a UUID value and return a UUID object."""
        normalized_value = cls.normalize_uuid(value, field_name)
        return UUID(normalized_value)

    @classmethod
    def normalize_optional_uuid(
        cls,
        value: Any,
        field_name: str = "ID",
    ) -> str | None:
        """Validate and normalize an optional UUID to a canonical string."""
        if value is None:
            return None

        normalized_value = str(value).strip()
        if not normalized_value:
            return None

        return cls.normalize_uuid(normalized_value, field_name)

    @classmethod
    def normalize_optional_uuid_object(
        cls,
        value: UUID | str | None,
        field_name: str = "ID",
    ) -> UUID | None:
        """Validate and normalize an optional UUID value to a UUID object."""
        normalized_value = cls.normalize_optional_uuid(value, field_name)
        if normalized_value is None:
            return None
        return UUID(normalized_value)

    @staticmethod
    def require_permission(
        permission_check: bool | Callable[[], bool],
        message: str,
    ) -> None:
        """Require a successful permission check."""
        is_allowed = permission_check() if callable(permission_check) else bool(permission_check)
        if not is_allowed:
            raise PermissionError(message)

    @staticmethod
    def require_record(
        record: dict[str, Any] | None,
        record_name: str,
    ) -> dict[str, Any]:
        """Require a repository record."""
        if not record:
            raise ValueError(f"{record_name} was not found.")
        return record

    @staticmethod
    def require_status(
        record: dict[str, Any],
        allowed_statuses: str | tuple[str, ...] | list[str] | set[str],
        record_name: str,
        status_field: str = "assignment_status",
    ) -> str:
        """Require a record to have one of the allowed statuses."""
        current_status = BaseService.normalize_text(record.get(status_field))
        if not current_status:
            raise ValueError(f"{record_name} has no valid status.")

        if isinstance(allowed_statuses, str):
            normalized_allowed_statuses = {allowed_statuses}
        else:
            normalized_allowed_statuses = set(allowed_statuses)

        if current_status not in normalized_allowed_statuses:
            expected_statuses = ", ".join(sorted(normalized_allowed_statuses))
            raise ValueError(
                f"{record_name} cannot be processed while its status is "
                f"'{current_status}'. Expected: {expected_statuses}."
            )

        return current_status

    @classmethod
    def require_user(
        cls,
        user: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Require a valid authenticated-user dictionary."""
        validated_user = cls.require_mapping(user, "Current user")
        cls.normalize_uuid(validated_user.get("id"), "Current user ID")
        return validated_user

    @classmethod
    def get_user_id(cls, user: dict[str, Any] | None) -> str:
        """Return the authenticated user's normalized UUID string."""
        validated_user = cls.require_user(user)
        return cls.normalize_uuid(validated_user.get("id"), "Current user ID")

    @classmethod
    def get_user_uuid(cls, user: dict[str, Any] | None) -> UUID:
        """Return the authenticated user's ID as a UUID object."""
        validated_user = cls.require_user(user)
        return cls.normalize_uuid_object(validated_user.get("id"), "Current user ID")