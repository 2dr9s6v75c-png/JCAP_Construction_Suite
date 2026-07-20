"""
JCAP Construction Suite
Material Request Assignment Test Doubles

Module-specific fakes used by MaterialRequestAssignmentService unit tests.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from tests.base.fake_base_repository import FakeBaseRepository


class FakeMaterialRequestAssignmentRepository(
    FakeBaseRepository[UUID, dict[str, Any]]
):
    """
    In-memory test double matching MaterialRequestAssignmentRepository.

    It records every public repository call, supports deterministic configured
    results/exceptions through FakeBaseRepository, and stores assignments
    created or updated during tests.
    """

    def __init__(self) -> None:
        super().__init__()
        self._next_assignment_id = UUID(
            "00000000-0000-0000-0000-000000002001"
        )
        self._active_assignment_ids: dict[UUID, UUID] = {}
        self._officer_workloads: dict[UUID, int] = {}

    def get_by_id(self, assignment_id: UUID, *, cursor=None) -> dict[str, Any] | None:
        self._record_call("get_by_id", assignment_id=assignment_id, cursor=cursor)
        self._raise_configured_exception("get_by_id")
        configured = self._get_configured_result("get_by_id")
        if configured is not None:
            return deepcopy(configured)
        return self.get_stored(assignment_id)

    def get_current_assignment(self, material_request_id: UUID, *, cursor=None) -> dict[str, Any] | None:
        self._record_call("get_current_assignment", material_request_id=material_request_id, cursor=cursor)
        self._raise_configured_exception("get_current_assignment")
        configured = self._get_configured_result("get_current_assignment")
        if configured is not None:
            return deepcopy(configured)
        assignment_id = self._active_assignment_ids.get(material_request_id)
        if assignment_id is None:
            return None
        return self.get_stored(assignment_id)

    def get_assignment_history(self, material_request_id: UUID, *, cursor=None) -> list[dict[str, Any]]:
        self._record_call("get_assignment_history", material_request_id=material_request_id, cursor=cursor)
        self._raise_configured_exception("get_assignment_history")
        configured = self._get_configured_result("get_assignment_history")
        if configured is not None:
            return deepcopy(configured)
        return [
            record for record in self.records.values()
            if record.get("material_request_id") == material_request_id
        ]

    def get_active_assignment(self, material_request_id: UUID, *, cursor=None) -> dict[str, Any] | None:
        self._record_call("get_active_assignment", material_request_id=material_request_id, cursor=cursor)
        self._raise_configured_exception("get_active_assignment")
        configured = self._get_configured_result("get_active_assignment")
        if configured is not None:
            return deepcopy(configured)
        assignment_id = self._active_assignment_ids.get(material_request_id)
        if assignment_id is None:
            return None
        return self.get_stored(assignment_id)

    def has_active_assignment(self, material_request_id: UUID, *, cursor=None) -> bool:
        self._record_call("has_active_assignment", material_request_id=material_request_id, cursor=cursor)
        self._raise_configured_exception("has_active_assignment")
        configured = self._get_configured_result("has_active_assignment")
        if configured is not None:
            return bool(configured)
        return material_request_id in self._active_assignment_ids

    def get_officer_workload(self, officer_id: UUID, *, cursor=None) -> int:
        self._record_call("get_officer_workload", officer_id=officer_id, cursor=cursor)
        self._raise_configured_exception("get_officer_workload")
        configured = self._get_configured_result("get_officer_workload")
        if configured is not None:
            return int(configured)
        return self._officer_workloads.get(officer_id, 0)

    def create_assignment(
        self,
        material_request_id: UUID,
        assigned_to: UUID,
        assigned_by: UUID,
        assignment_status: Any,
        remarks: str | None,
        *,
        cursor=None,
    ) -> UUID:
        self._record_call(
            "create_assignment",
            material_request_id=material_request_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assignment_status=assignment_status,
            remarks=remarks,
            cursor=cursor,
        )
        self._raise_configured_exception("create_assignment")
        configured = self._get_configured_result("create_assignment")
        assignment_id = configured if configured is not None else self._next_assignment_id
        if not isinstance(assignment_id, UUID):
            raise TypeError("Configured create_assignment result must be a UUID.")
        record = {
            "id": assignment_id,
            "material_request_id": material_request_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "assignment_status": assignment_status,
            "remarks": remarks,
        }
        self.store(assignment_id, record)
        self._active_assignment_ids[material_request_id] = assignment_id
        self._officer_workloads[assigned_to] = self._officer_workloads.get(assigned_to, 0) + 1
        return assignment_id

    def reassign_assignment(
        self,
        assignment_id: UUID,
        assignment_status: Any,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        self._record_call(
            "reassign_assignment",
            assignment_id=assignment_id,
            assignment_status=assignment_status,
            remarks=remarks,
            cursor=cursor,
        )
        self._raise_configured_exception("reassign_assignment")

        if self.has_configured_result("reassign_assignment"):
            return deepcopy(self.configured_result("reassign_assignment"))

        record = self.get_stored(assignment_id)
        if record is None or record.get("ended_at") is not None:
            return None

        updated = deepcopy(record)
        updated["assignment_status"] = assignment_status
        updated["ended_at"] = datetime.now(timezone.utc)
        if remarks is not None:
            updated["remarks"] = remarks

        self.store(assignment_id, updated)

        material_request_id = updated.get("material_request_id")
        if isinstance(material_request_id, UUID):
            self._active_assignment_ids.pop(material_request_id, None)

        assigned_to = updated.get("assigned_to")
        if isinstance(assigned_to, UUID):
            current_workload = self._officer_workloads.get(assigned_to, 0)
            self._officer_workloads[assigned_to] = max(current_workload - 1, 0)

        return deepcopy(updated)

    def set_active_assignment(self, material_request_id: UUID, assignment: dict[str, Any] | None) -> None:
        """Seed or clear the active assignment for a material request."""
        if assignment is None:
            self._active_assignment_ids.pop(material_request_id, None)
            return
        assignment_id = assignment.get("id")
        if not isinstance(assignment_id, UUID):
            raise TypeError("assignment['id'] must be a UUID.")
        self.store(assignment_id, assignment)
        self._active_assignment_ids[material_request_id] = assignment_id

    def set_officer_workload(self, officer_id: UUID, workload: int) -> None:
        """Set a deterministic active assignment count for an officer."""
        if not isinstance(workload, int):
            raise TypeError("workload must be an integer.")
        if workload < 0:
            raise ValueError("workload cannot be negative.")
        self._officer_workloads[officer_id] = workload

    def reset(self) -> None:
        super().reset()
        self._next_assignment_id = UUID("00000000-0000-0000-0000-000000002001")
        self._active_assignment_ids = {}
        self._officer_workloads = {}

    def _record_call(self, method_name: str, **arguments: Any) -> None:
        self.record_call(method_name, **arguments)

    def _raise_configured_exception(self, method_name: str) -> None:
        self.raise_if_configured(method_name)

    def _get_configured_result(self, method_name: str) -> Any:
        if not self.has_configured_result(method_name):
            return None
        return self.configured_result(method_name)