"""
JCAP Construction Suite
Assignment Builder

Builds production-shaped material request assignment dictionary records.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from tests.base.fake_uuid_provider import FakeUUIDProvider
from tests.builders.base_builder import BaseBuilder


class AssignmentBuilder(BaseBuilder[dict[str, Any]]):
    """
    Fluent builder for material request assignment records.

    The production repository maps assignment rows into dictionaries with
    lifecycle timestamps, so this builder mirrors that public shape exactly.
    """

    @classmethod
    def default_values(cls) -> dict[str, Any]:
        """Return realistic defaults for one active assignment."""
        assigned_at = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)

        return {
            "id": FakeUUIDProvider.sequential_uuid(5001),
            "material_request_id": FakeUUIDProvider.sequential_uuid(1001),
            "assigned_to": FakeUUIDProvider.sequential_uuid(4002),
            "assigned_by": FakeUUIDProvider.sequential_uuid(4001),
            "assignment_status": "Assigned",
            "assigned_at": assigned_at,
            "accepted_at": None,
            "started_at": None,
            "completed_at": None,
            "ended_at": None,
            "remarks": "Assigned for quotation processing.",
            "created_at": assigned_at,
            "updated_at": assigned_at,
        }

    def _build(self, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and return an isolated assignment record."""
        self._validate(values)
        return deepcopy(values)

    def with_id(self, value: UUID | str) -> "AssignmentBuilder":
        return self.with_value("id", self._as_uuid(value, "id"))

    def for_material_request(
        self,
        material_request_id: UUID | str,
    ) -> "AssignmentBuilder":
        return self.with_value(
            "material_request_id",
            self._as_uuid(material_request_id, "material_request_id"),
        )

    def assigned_to(
        self,
        user_id: UUID | str,
    ) -> "AssignmentBuilder":
        return self.with_value(
            "assigned_to",
            self._as_uuid(user_id, "assigned_to"),
        )

    def assigned_by(
        self,
        user_id: UUID | str,
    ) -> "AssignmentBuilder":
        return self.with_value(
            "assigned_by",
            self._as_uuid(user_id, "assigned_by"),
        )

    def with_status(self, value: str) -> "AssignmentBuilder":
        return self.with_value(
            "assignment_status",
            self._required_text(value, "assignment_status"),
        )

    def assigned(self) -> "AssignmentBuilder":
        return self.with_status("Assigned")

    def accepted(
        self,
        accepted_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            accepted_at
            or datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
            "accepted_at",
        )
        return self.with_values(
            assignment_status="Accepted",
            accepted_at=timestamp,
            updated_at=timestamp,
        )

    def in_progress(
        self,
        started_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            started_at
            or datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc),
            "started_at",
        )
        accepted_at = self.get_value("accepted_at") or timestamp

        return self.with_values(
            assignment_status="In Progress",
            accepted_at=accepted_at,
            started_at=timestamp,
            updated_at=timestamp,
        )

    def completed(
        self,
        completed_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            completed_at
            or datetime(2026, 1, 5, 16, 0, tzinfo=timezone.utc),
            "completed_at",
        )
        accepted_at = self.get_value("accepted_at") or timestamp
        started_at = self.get_value("started_at") or timestamp

        return self.with_values(
            assignment_status="Completed",
            accepted_at=accepted_at,
            started_at=started_at,
            completed_at=timestamp,
            ended_at=timestamp,
            updated_at=timestamp,
        )

    def reassigned(
        self,
        ended_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            ended_at
            or datetime(2026, 1, 3, 14, 0, tzinfo=timezone.utc),
            "ended_at",
        )
        return self.with_values(
            assignment_status="Reassigned",
            ended_at=timestamp,
            updated_at=timestamp,
        )

    def cancelled(
        self,
        ended_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            ended_at
            or datetime(2026, 1, 3, 15, 0, tzinfo=timezone.utc),
            "ended_at",
        )
        return self.with_values(
            assignment_status="Cancelled",
            ended_at=timestamp,
            updated_at=timestamp,
        )

    def active(self) -> "AssignmentBuilder":
        """Make the assignment non-ended."""
        return self.with_values(
            ended_at=None,
            completed_at=None,
        )

    def ended(
        self,
        ended_at: datetime | None = None,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(
            ended_at
            or datetime(2026, 1, 3, 17, 0, tzinfo=timezone.utc),
            "ended_at",
        )
        return self.with_values(
            ended_at=timestamp,
            updated_at=timestamp,
        )

    def with_remarks(
        self,
        value: str | None,
    ) -> "AssignmentBuilder":
        if value is None:
            return self.with_value("remarks", None)

        if not isinstance(value, str):
            raise TypeError("remarks must be a string or None.")

        return self.with_value("remarks", value.strip())

    def assigned_at(
        self,
        value: datetime,
    ) -> "AssignmentBuilder":
        timestamp = self._as_datetime(value, "assigned_at")
        return self.with_values(
            assigned_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def updated_at(
        self,
        value: datetime,
    ) -> "AssignmentBuilder":
        return self.with_value(
            "updated_at",
            self._as_datetime(value, "updated_at"),
        )

    @staticmethod
    def _validate(values: dict[str, Any]) -> None:
        required_uuid_fields = (
            "id",
            "material_request_id",
            "assigned_to",
            "assigned_by",
        )

        for field_name in required_uuid_fields:
            if not isinstance(values.get(field_name), UUID):
                raise TypeError(f"{field_name} must be a UUID.")

        required_text_fields = ("assignment_status",)

        for field_name in required_text_fields:
            value = values.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty.")

        required_datetime_fields = (
            "assigned_at",
            "created_at",
            "updated_at",
        )

        for field_name in required_datetime_fields:
            if not isinstance(values.get(field_name), datetime):
                raise TypeError(f"{field_name} must be a datetime.")

        optional_datetime_fields = (
            "accepted_at",
            "started_at",
            "completed_at",
            "ended_at",
        )

        for field_name in optional_datetime_fields:
            value = values.get(field_name)
            if value is not None and not isinstance(value, datetime):
                raise TypeError(
                    f"{field_name} must be a datetime or None."
                )

        if values["ended_at"] is not None:
            if values["ended_at"] < values["assigned_at"]:
                raise ValueError(
                    "ended_at cannot be earlier than assigned_at."
                )

        if values["completed_at"] is not None and values["ended_at"] is None:
            raise ValueError(
                "A completed assignment must also have ended_at."
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
    def _as_uuid(value: UUID | str, field_name: str) -> UUID:
        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as exc:
                raise ValueError(
                    f"{field_name} must contain a valid UUID."
                ) from exc

        raise TypeError(f"{field_name} must be a UUID or UUID string.")

    @staticmethod
    def _as_datetime(value: datetime, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(f"{field_name} must be a datetime.")

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)