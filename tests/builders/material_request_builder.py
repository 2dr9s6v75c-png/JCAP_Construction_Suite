"""
JCAP Construction Suite
Material Request Builder

Builds production-shaped material request dictionary records for tests.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from tests.base.fake_uuid_provider import FakeUUIDProvider
from tests.builders.base_builder import BaseBuilder


class MaterialRequestBuilder(BaseBuilder[dict[str, Any]]):
    """
    Fluent builder for material request records.

    The current production service and UI layers use dictionary-based records,
    so this builder intentionally returns ``dict[str, Any]`` rather than a
    test-only entity.
    """

    @classmethod
    def default_values(cls) -> dict[str, Any]:
        """Return realistic default values for one material request."""
        created_at = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
        request_id = FakeUUIDProvider.sequential_uuid(1001)
        project_id = FakeUUIDProvider.sequential_uuid(2001)
        client_id = FakeUUIDProvider.sequential_uuid(3001)
        requester_id = FakeUUIDProvider.sequential_uuid(4001)

        return {
            "id": request_id,
            "mr_number": "MR-2026-0001",
            "project_id": project_id,
            "project_name": "Caticlan Airport Project",
            "client_id": client_id,
            "client_name": "Sample Client",
            "location": "Caticlan, Aklan",
            "requested_by_id": requester_id,
            "requested_by": "Test Requester",
            "assigned_to_id": None,
            "assigned_to": None,
            "material_request_description": "General construction materials",
            "priority": "Medium",
            "status": "New",
            "due_date": created_at.date() + timedelta(days=7),
            "remarks": "",
            "attachments": [],
            "items": [],
            "created_at": created_at,
            "updated_at": created_at,
            "archived_at": None,
        }

    def _build(self, values: dict[str, Any]) -> dict[str, Any]:
        """Build and return an isolated material request record."""
        self._validate(values)
        return deepcopy(values)

    def with_id(self, value: UUID | str) -> "MaterialRequestBuilder":
        return self.with_value("id", self._as_uuid(value, "id"))

    def with_number(self, value: str) -> "MaterialRequestBuilder":
        return self.with_value("mr_number", self._required_text(value, "mr_number"))

    def with_project(
        self,
        project_id: UUID | str,
        project_name: str,
    ) -> "MaterialRequestBuilder":
        return self.with_values(
            project_id=self._as_uuid(project_id, "project_id"),
            project_name=self._required_text(project_name, "project_name"),
        )

    def with_client(
        self,
        client_id: UUID | str | None,
        client_name: str | None,
    ) -> "MaterialRequestBuilder":
        normalized_id = (
            None if client_id is None else self._as_uuid(client_id, "client_id")
        )
        normalized_name = (
            None if client_name is None else self._required_text(
                client_name, "client_name"
            )
        )
        return self.with_values(
            client_id=normalized_id,
            client_name=normalized_name,
        )

    def requested_by(
        self,
        user_id: UUID | str,
        display_name: str,
    ) -> "MaterialRequestBuilder":
        return self.with_values(
            requested_by_id=self._as_uuid(user_id, "requested_by_id"),
            requested_by=self._required_text(display_name, "requested_by"),
        )

    def assigned_to(
        self,
        user_id: UUID | str,
        display_name: str,
    ) -> "MaterialRequestBuilder":
        return self.with_values(
            assigned_to_id=self._as_uuid(user_id, "assigned_to_id"),
            assigned_to=self._required_text(display_name, "assigned_to"),
        )

    def unassigned(self) -> "MaterialRequestBuilder":
        return self.with_values(
            assigned_to_id=None,
            assigned_to=None,
        )

    def with_description(self, value: str) -> "MaterialRequestBuilder":
        return self.with_value(
            "material_request_description",
            self._required_text(value, "material_request_description"),
        )

    def with_location(self, value: str) -> "MaterialRequestBuilder":
        return self.with_value("location", self._required_text(value, "location"))

    def with_priority(self, value: str) -> "MaterialRequestBuilder":
        return self.with_value("priority", self._required_text(value, "priority"))

    def high_priority(self) -> "MaterialRequestBuilder":
        return self.with_priority("High")

    def medium_priority(self) -> "MaterialRequestBuilder":
        return self.with_priority("Medium")

    def low_priority(self) -> "MaterialRequestBuilder":
        return self.with_priority("Low")

    def with_status(self, value: str) -> "MaterialRequestBuilder":
        return self.with_value("status", self._required_text(value, "status"))

    def new(self) -> "MaterialRequestBuilder":
        return self.with_status("New")

    def assigned(self) -> "MaterialRequestBuilder":
        return self.with_status("Assigned")

    def in_progress(self) -> "MaterialRequestBuilder":
        return self.with_status("In Progress")

    def waiting_supplier_quote(self) -> "MaterialRequestBuilder":
        return self.with_status("Waiting Supplier Quote")

    def completed(self) -> "MaterialRequestBuilder":
        return self.with_status("Completed")

    def archived(self, archived_at: datetime | None = None) -> "MaterialRequestBuilder":
        timestamp = archived_at or datetime(
            2026, 1, 15, 8, 0, tzinfo=timezone.utc
        )
        return self.with_values(
            status="Archived",
            archived_at=self._as_datetime(timestamp, "archived_at"),
        )

    def with_due_date(self, value: date | datetime | None) -> "MaterialRequestBuilder":
        if isinstance(value, datetime):
            value = value.date()
        if value is not None and not isinstance(value, date):
            raise TypeError("due_date must be a date, datetime, or None.")
        return self.with_value("due_date", value)

    def overdue(self, days: int = 1) -> "MaterialRequestBuilder":
        if not isinstance(days, int):
            raise TypeError("days must be an integer.")
        if days < 1:
            raise ValueError("days must be at least 1.")
        return self.with_due_date(date(2025, 12, 31) - timedelta(days=days - 1))

    def with_remarks(self, value: str) -> "MaterialRequestBuilder":
        if not isinstance(value, str):
            raise TypeError("remarks must be a string.")
        return self.with_value("remarks", value)

    def with_items(
        self,
        items: list[dict[str, Any]],
    ) -> "MaterialRequestBuilder":
        if not isinstance(items, list):
            raise TypeError("items must be a list.")
        if not all(isinstance(item, dict) for item in items):
            raise TypeError("every item must be a dictionary.")
        return self.with_value("items", deepcopy(items))

    def add_item(
        self,
        description: str,
        *,
        quantity: int | float = 1,
        unit: str = "pc",
        brand: str = "",
        remarks: str = "",
    ) -> "MaterialRequestBuilder":
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
            raise TypeError("quantity must be numeric.")
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero.")

        items = self.get_value("items")
        items.append(
            {
                "quantity": quantity,
                "unit": self._required_text(unit, "unit"),
                "description": self._required_text(
                    description, "description"
                ),
                "brand": brand,
                "remarks": remarks,
            }
        )
        return self.with_value("items", items)

    def with_attachments(
        self,
        attachments: list[Any],
    ) -> "MaterialRequestBuilder":
        if not isinstance(attachments, list):
            raise TypeError("attachments must be a list.")
        return self.with_value("attachments", deepcopy(attachments))

    def created_at(self, value: datetime) -> "MaterialRequestBuilder":
        timestamp = self._as_datetime(value, "created_at")
        return self.with_values(
            created_at=timestamp,
            updated_at=timestamp,
        )

    def updated_at(self, value: datetime) -> "MaterialRequestBuilder":
        return self.with_value(
            "updated_at",
            self._as_datetime(value, "updated_at"),
        )

    @staticmethod
    def _validate(values: dict[str, Any]) -> None:
        required_fields = (
            "id",
            "mr_number",
            "project_id",
            "project_name",
            "requested_by_id",
            "requested_by",
            "material_request_description",
            "priority",
            "status",
            "created_at",
            "updated_at",
        )

        missing = [
            field_name
            for field_name in required_fields
            if values.get(field_name) in (None, "")
        ]

        if missing:
            raise ValueError(
                "Material request is missing required field(s): "
                + ", ".join(missing)
            )

        if not isinstance(values["id"], UUID):
            raise TypeError("id must be a UUID.")

        if not isinstance(values["project_id"], UUID):
            raise TypeError("project_id must be a UUID.")

        if not isinstance(values["requested_by_id"], UUID):
            raise TypeError("requested_by_id must be a UUID.")

        if values["assigned_to_id"] is not None and not isinstance(
            values["assigned_to_id"], UUID
        ):
            raise TypeError("assigned_to_id must be a UUID or None.")

        if values["client_id"] is not None and not isinstance(
            values["client_id"], UUID
        ):
            raise TypeError("client_id must be a UUID or None.")

        if not isinstance(values["items"], list):
            raise TypeError("items must be a list.")

        if not isinstance(values["attachments"], list):
            raise TypeError("attachments must be a list.")

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