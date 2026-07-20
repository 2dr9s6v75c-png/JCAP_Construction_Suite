"""
JCAP Construction Suite
Workflow Builder

Builds workflow-transition scenarios for service and process tests.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from tests.base.fake_uuid_provider import FakeUUIDProvider
from tests.builders.base_builder import BaseBuilder


class WorkflowBuilder(BaseBuilder[dict[str, Any]]):
    """
    Fluent builder for workflow-transition test scenarios.

    Workflow state rules currently live in Python rather than in a dedicated
    persisted workflow entity. This builder therefore creates a stable scenario
    dictionary that tests can pass to workflow services, process coordinators,
    fakes, and assertions.
    """

    @classmethod
    def default_values(cls) -> dict[str, Any]:
        """Return defaults for one material-request assignment transition."""
        return {
            "entity_type": "material_request",
            "entity_id": FakeUUIDProvider.sequential_uuid(1001),
            "workflow_name": "material_request_assignment",
            "current_state": "New",
            "target_state": "Assigned",
            "actor_id": FakeUUIDProvider.sequential_uuid(4001),
            "reason": "Material request assigned for processing.",
            "transitioned_at": datetime(
                2026,
                1,
                2,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            "metadata": {},
            "allowed": True,
            "expected_error": None,
        }

    def _build(self, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and return an isolated workflow scenario."""
        self._validate(values)
        return deepcopy(values)

    def for_entity(
        self,
        entity_type: str,
        entity_id: UUID | str,
    ) -> "WorkflowBuilder":
        """Set the workflow subject."""
        return self.with_values(
            entity_type=self._required_text(entity_type, "entity_type"),
            entity_id=self._as_uuid(entity_id, "entity_id"),
        )

    def for_material_request(
        self,
        material_request_id: UUID | str,
    ) -> "WorkflowBuilder":
        """Configure a material-request workflow scenario."""
        return self.for_entity(
            "material_request",
            material_request_id,
        )

    def for_assignment(
        self,
        assignment_id: UUID | str,
    ) -> "WorkflowBuilder":
        """Configure an assignment workflow scenario."""
        return self.with_values(
            entity_type="material_request_assignment",
            entity_id=self._as_uuid(assignment_id, "assignment_id"),
            workflow_name="material_request_assignment",
        )

    def with_workflow(self, value: str) -> "WorkflowBuilder":
        """Set the workflow name."""
        return self.with_value(
            "workflow_name",
            self._required_text(value, "workflow_name"),
        )

    def from_state(self, value: str | Enum) -> "WorkflowBuilder":
        """Set the current state."""
        return self.with_value(
            "current_state",
            self._state_value(value, "current_state"),
        )

    def to_state(self, value: str | Enum) -> "WorkflowBuilder":
        """Set the requested target state."""
        return self.with_value(
            "target_state",
            self._state_value(value, "target_state"),
        )

    def transition(
        self,
        current_state: str | Enum,
        target_state: str | Enum,
    ) -> "WorkflowBuilder":
        """Set both sides of a transition."""
        return self.with_values(
            current_state=self._state_value(
                current_state,
                "current_state",
            ),
            target_state=self._state_value(
                target_state,
                "target_state",
            ),
        )

    def new_to_assigned(self) -> "WorkflowBuilder":
        """Configure the initial material-request assignment transition."""
        return self.transition("New", "Assigned")

    def assigned_to_accepted(self) -> "WorkflowBuilder":
        """Configure assignment acceptance."""
        return self.transition("Assigned", "Accepted")

    def accepted_to_in_progress(self) -> "WorkflowBuilder":
        """Configure processing start."""
        return self.transition("Accepted", "In Progress")

    def in_progress_to_completed(self) -> "WorkflowBuilder":
        """Configure assignment completion."""
        return self.transition("In Progress", "Completed")

    def assigned_to_reassigned(self) -> "WorkflowBuilder":
        """Configure reassignment of an active assignment."""
        return self.transition("Assigned", "Reassigned")

    def assigned_to_cancelled(self) -> "WorkflowBuilder":
        """Configure assignment cancellation."""
        return self.transition("Assigned", "Cancelled")

    def performed_by(
        self,
        actor_id: UUID | str,
    ) -> "WorkflowBuilder":
        """Set the user performing the transition."""
        return self.with_value(
            "actor_id",
            self._as_uuid(actor_id, "actor_id"),
        )

    def with_reason(
        self,
        value: str | None,
    ) -> "WorkflowBuilder":
        """Set an optional transition reason."""
        if value is None:
            return self.with_value("reason", None)

        if not isinstance(value, str):
            raise TypeError("reason must be a string or None.")

        normalized = value.strip()
        return self.with_value("reason", normalized or None)

    def at(self, value: datetime) -> "WorkflowBuilder":
        """Set the transition timestamp."""
        return self.with_value(
            "transitioned_at",
            self._as_datetime(value, "transitioned_at"),
        )

    def with_metadata(
        self,
        **metadata: Any,
    ) -> "WorkflowBuilder":
        """Replace workflow metadata."""
        return self.with_value("metadata", deepcopy(metadata))

    def add_metadata(
        self,
        key: str,
        value: Any,
    ) -> "WorkflowBuilder":
        """Add one metadata entry."""
        normalized_key = self._required_text(key, "metadata key")
        metadata = self.get_value("metadata")
        metadata[normalized_key] = deepcopy(value)
        return self.with_value("metadata", metadata)

    def allowed(self) -> "WorkflowBuilder":
        """Mark the transition as expected to succeed."""
        return self.with_values(
            allowed=True,
            expected_error=None,
        )

    def denied(
        self,
        expected_error: str = "Workflow transition is not allowed.",
    ) -> "WorkflowBuilder":
        """Mark the transition as expected to fail."""
        return self.with_values(
            allowed=False,
            expected_error=self._required_text(
                expected_error,
                "expected_error",
            ),
        )

    @staticmethod
    def _validate(values: dict[str, Any]) -> None:
        for field_name in (
            "entity_type",
            "workflow_name",
            "current_state",
            "target_state",
        ):
            value = values.get(field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty.")

        for field_name in ("entity_id", "actor_id"):
            if not isinstance(values.get(field_name), UUID):
                raise TypeError(f"{field_name} must be a UUID.")

        if not isinstance(values.get("transitioned_at"), datetime):
            raise TypeError("transitioned_at must be a datetime.")

        if not isinstance(values.get("metadata"), dict):
            raise TypeError("metadata must be a dictionary.")

        if not isinstance(values.get("allowed"), bool):
            raise TypeError("allowed must be a boolean.")

        expected_error = values.get("expected_error")

        if values["allowed"] and expected_error is not None:
            raise ValueError(
                "An allowed transition cannot define expected_error."
            )

        if not values["allowed"]:
            if not isinstance(expected_error, str) or not expected_error.strip():
                raise ValueError(
                    "A denied transition must define expected_error."
                )

    @staticmethod
    def _state_value(value: str | Enum, field_name: str) -> str:
        """Normalize string and Enum workflow states."""
        if isinstance(value, Enum):
            value = value.value

        return WorkflowBuilder._required_text(
            value,
            field_name,
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