"""
JCAP Construction Suite
Notification Builder

Builds production-shaped notification dictionary records for tests.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from tests.base.fake_uuid_provider import FakeUUIDProvider
from tests.builders.base_builder import BaseBuilder


class NotificationBuilder(BaseBuilder[dict[str, Any]]):
    """
    Fluent builder for persistent notification records.

    The production repository maps notification identifiers to strings, so this
    builder mirrors that public repository shape instead of returning UUID
    instances for mapped ID fields.
    """

    @classmethod
    def default_values(cls) -> dict[str, Any]:
        """Return realistic defaults for one unread notification."""
        return {
            "id": str(FakeUUIDProvider.sequential_uuid(6001)),
            "recipient_user_id": str(
                FakeUUIDProvider.sequential_uuid(4002)
            ),
            "notification_type": "MATERIAL_REQUEST_ASSIGNED",
            "title": "Material Request Assigned",
            "message": (
                "Material Request MR-2026-0001 has been assigned to you."
            ),
            "entity_type": "material_request",
            "entity_id": str(
                FakeUUIDProvider.sequential_uuid(1001)
            ),
            "is_read": False,
            "created_by": str(
                FakeUUIDProvider.sequential_uuid(4001)
            ),
            "created_at": datetime(
                2026,
                1,
                2,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            "read_at": None,
            "recipient_username": "assigned.user",
            "recipient_full_name": "Assigned User",
            "created_by_username": "assigning.user",
            "created_by_full_name": "Assigning User",
        }

    def _build(self, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and return an isolated notification record."""
        self._validate(values)
        return deepcopy(values)

    def with_id(self, value: UUID | str) -> "NotificationBuilder":
        return self.with_value(
            "id",
            self._as_uuid_string(value, "id"),
        )

    def for_recipient(
        self,
        user_id: UUID | str,
        *,
        username: str = "assigned.user",
        full_name: str = "Assigned User",
    ) -> "NotificationBuilder":
        """Set the recipient and optional display fields."""
        return self.with_values(
            recipient_user_id=self._as_uuid_string(
                user_id,
                "recipient_user_id",
            ),
            recipient_username=self._required_text(
                username,
                "recipient_username",
            ),
            recipient_full_name=self._required_text(
                full_name,
                "recipient_full_name",
            ),
        )

    def created_by(
        self,
        user_id: UUID | str | None,
        *,
        username: str | None = "assigning.user",
        full_name: str | None = "Assigning User",
    ) -> "NotificationBuilder":
        """Set the notification creator and optional display fields."""
        if user_id is None:
            return self.with_values(
                created_by=None,
                created_by_username=None,
                created_by_full_name=None,
            )

        return self.with_values(
            created_by=self._as_uuid_string(
                user_id,
                "created_by",
            ),
            created_by_username=(
                None
                if username is None
                else self._required_text(
                    username,
                    "created_by_username",
                )
            ),
            created_by_full_name=(
                None
                if full_name is None
                else self._required_text(
                    full_name,
                    "created_by_full_name",
                )
            ),
        )

    def with_type(self, value: str) -> "NotificationBuilder":
        return self.with_value(
            "notification_type",
            self._required_text(value, "notification_type"),
        )

    def with_title(self, value: str) -> "NotificationBuilder":
        return self.with_value(
            "title",
            self._required_text(value, "title"),
        )

    def with_message(self, value: str) -> "NotificationBuilder":
        return self.with_value(
            "message",
            self._required_text(value, "message"),
        )

    def for_entity(
        self,
        entity_type: str,
        entity_id: UUID | str,
    ) -> "NotificationBuilder":
        """Link the notification to an application record."""
        return self.with_values(
            entity_type=self._required_text(
                entity_type,
                "entity_type",
            ),
            entity_id=self._as_uuid_string(
                entity_id,
                "entity_id",
            ),
        )

    def without_entity(self) -> "NotificationBuilder":
        """Build a notification that is not linked to a record."""
        return self.with_values(
            entity_type=None,
            entity_id=None,
        )

    def material_request_assigned(
        self,
        material_request_id: UUID | str,
        mr_number: str = "MR-2026-0001",
    ) -> "NotificationBuilder":
        """Configure a material-request assignment notification."""
        clean_number = self._required_text(mr_number, "mr_number")

        return self.with_values(
            notification_type="MATERIAL_REQUEST_ASSIGNED",
            title="Material Request Assigned",
            message=(
                f"Material Request {clean_number} has been assigned to you."
            ),
            entity_type="material_request",
            entity_id=self._as_uuid_string(
                material_request_id,
                "material_request_id",
            ),
        )

    def clarification_requested(
        self,
        clarification_id: UUID | str,
    ) -> "NotificationBuilder":
        """Configure a clarification-request notification."""
        return self.with_values(
            notification_type="CLARIFICATION_REQUESTED",
            title="Clarification Requested",
            message=(
                "A supplier clarification requires your attention."
            ),
            entity_type="clarification",
            entity_id=self._as_uuid_string(
                clarification_id,
                "clarification_id",
            ),
        )

    def unread(self) -> "NotificationBuilder":
        """Mark the notification as unread."""
        return self.with_values(
            is_read=False,
            read_at=None,
        )

    def read(
        self,
        read_at: datetime | None = None,
    ) -> "NotificationBuilder":
        """Mark the notification as read."""
        timestamp = self._as_datetime(
            read_at
            or datetime(
                2026,
                1,
                2,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            "read_at",
        )

        return self.with_values(
            is_read=True,
            read_at=timestamp,
        )

    def created_at(
        self,
        value: datetime,
    ) -> "NotificationBuilder":
        return self.with_value(
            "created_at",
            self._as_datetime(value, "created_at"),
        )

    @staticmethod
    def _validate(values: dict[str, Any]) -> None:
        required_text_fields = (
            "id",
            "recipient_user_id",
            "notification_type",
            "title",
            "message",
        )

        for field_name in required_text_fields:
            value = values.get(field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty.")

        for field_name in (
            "id",
            "recipient_user_id",
        ):
            NotificationBuilder._as_uuid_string(
                values[field_name],
                field_name,
            )

        for field_name in (
            "entity_id",
            "created_by",
        ):
            value = values.get(field_name)

            if value is not None:
                NotificationBuilder._as_uuid_string(
                    value,
                    field_name,
                )

        entity_type = values.get("entity_type")
        entity_id = values.get("entity_id")

        if (entity_type is None) != (entity_id is None):
            raise ValueError(
                "entity_type and entity_id must either both be set "
                "or both be None."
            )

        if entity_type is not None:
            NotificationBuilder._required_text(
                entity_type,
                "entity_type",
            )

        if not isinstance(values.get("is_read"), bool):
            raise TypeError("is_read must be a boolean.")

        if not isinstance(values.get("created_at"), datetime):
            raise TypeError("created_at must be a datetime.")

        read_at = values.get("read_at")

        if read_at is not None and not isinstance(read_at, datetime):
            raise TypeError("read_at must be a datetime or None.")

        if values["is_read"] and read_at is None:
            raise ValueError(
                "A read notification must define read_at."
            )

        if not values["is_read"] and read_at is not None:
            raise ValueError(
                "An unread notification cannot define read_at."
            )

        if read_at is not None and read_at < values["created_at"]:
            raise ValueError(
                "read_at cannot be earlier than created_at."
            )

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty.")

        return normalized

    @staticmethod
    def _as_uuid_string(
        value: UUID | str,
        field_name: str,
    ) -> str:
        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, str):
            try:
                return str(UUID(value))
            except ValueError as exc:
                raise ValueError(
                    f"{field_name} must contain a valid UUID."
                ) from exc

        raise TypeError(
            f"{field_name} must be a UUID or UUID string."
        )

    @staticmethod
    def _as_datetime(value: datetime, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(f"{field_name} must be a datetime.")

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)