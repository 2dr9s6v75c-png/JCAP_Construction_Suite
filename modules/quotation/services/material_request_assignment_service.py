"""
JCAP Construction Suite
Material Request Assignment Service

Owns assignment validation, permission enforcement, workload rules, and
single-record assignment lifecycle operations.

Cross-table coordination, replacement-assignment creation, notifications, and
transaction orchestration belong to the process layer.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from core.security.permissions import PermissionService
from core.services.base_service import BaseService
from core.workflow.material_request_workflow import AssignmentState
from modules.quotation.constants.assignment_constants import (
    DEFAULT_ASSIGNMENT_REMARKS,
    MAX_ACTIVE_ASSIGNMENTS,
    MAX_ASSIGNMENT_REMARK_LENGTH,
)
from modules.quotation.repositories.material_request_assignment_repository import (
    MaterialRequestAssignmentRepository,
)


class MaterialRequestAssignmentService(BaseService):
    """Business service for material-request assignment records."""

    def __init__(
        self,
        repository: MaterialRequestAssignmentRepository | None = None,
    ) -> None:
        self._repository = (
            repository or MaterialRequestAssignmentRepository()
        )

    def get_by_id(
        self,
        assignment_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        assignment_id = self.normalize_uuid_object(
            assignment_id,
            "Assignment ID",
        )
        return self._repository.get_by_id(
            assignment_id,
            cursor=cursor,
        )

    def get_current_assignment(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.get_current_assignment(
            material_request_id,
            cursor=cursor,
        )

    def get_assignment_history(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.get_assignment_history(
            material_request_id,
            cursor=cursor,
        )

    def get_active_assignment(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.get_active_assignment(
            material_request_id,
            cursor=cursor,
        )

    def has_active_assignment(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> bool:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.has_active_assignment(
            material_request_id,
            cursor=cursor,
        )

    def get_officer_workload(
        self,
        officer_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        officer_id = self.normalize_uuid_object(
            officer_id,
            "Officer ID",
        )
        return self._repository.get_officer_workload(
            officer_id,
            cursor=cursor,
        )

    def assign(
        self,
        material_request_id: UUID | str,
        assigned_to: UUID | str,
        current_user: dict[str, Any],
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> UUID:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        assigned_to = self.normalize_uuid_object(
            assigned_to,
            "Assigned Officer ID",
        )

        current_user = self.require_user(current_user)
        assigned_by = self.get_user_uuid(current_user)

        self._require_assign_permission(current_user)

        if self.has_active_assignment(
            material_request_id,
            cursor=cursor,
        ):
            raise ValueError(
                "The material request already has an active assignment."
            )

        normalized_remarks = self._validate_assignment_remarks(
            remarks,
            use_default=True,
        )

        self._validate_officer_workload(
            assigned_to,
            cursor=cursor,
        )

        return self._repository.create_assignment(
            material_request_id=material_request_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assignment_status=AssignmentState.ASSIGNED,
            remarks=normalized_remarks,
            cursor=cursor,
        )

    def reassign(
        self,
        assignment_id: UUID | str,
        current_user: dict[str, Any],
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        """
        Close an active assignment using the Reassigned state.

        Creating the replacement assignment and updating the Material Request
        belong to the process layer and must occur in one shared transaction.
        """
        assignment_id = self.normalize_uuid_object(
            assignment_id,
            "Assignment ID",
        )
        current_user = self.require_user(current_user)

        self._require_reassign_permission(current_user)

        assignment = self.require_record(
            self._repository.get_by_id(
                assignment_id,
                cursor=cursor,
            ),
            "Assignment",
        )
        self._require_active_assignment(assignment)

        normalized_remarks = self._validate_assignment_remarks(
            remarks,
            use_default=False,
        )

        updated = self._repository.reassign_assignment(
            assignment_id=assignment_id,
            assignment_status=AssignmentState.REASSIGNED,
            remarks=normalized_remarks,
            cursor=cursor,
        )

        if updated is None:
            raise ValueError(
                "Assignment could not be reassigned because it is no longer active."
            )

        return updated

    @staticmethod
    def _require_assign_permission(
        current_user: dict[str, Any],
    ) -> None:
        MaterialRequestAssignmentService.require_permission(
            lambda: PermissionService.can_assign_material_request(
                current_user
            ),
            "You do not have permission to assign Material Requests.",
        )

    @staticmethod
    def _require_reassign_permission(
        current_user: dict[str, Any],
    ) -> None:
        MaterialRequestAssignmentService.require_permission(
            lambda: PermissionService.can_reassign_material_request(
                current_user
            ),
            "You do not have permission to reassign Material Requests.",
        )

    def _validate_assignment_remarks(
        self,
        remarks: str | None,
        *,
        use_default: bool,
    ) -> str | None:
        normalized = self.normalize_optional_text(remarks)

        if normalized is None:
            return (
                DEFAULT_ASSIGNMENT_REMARKS
                if use_default
                else None
            )

        if len(normalized) > MAX_ASSIGNMENT_REMARK_LENGTH:
            raise ValueError(
                "Assignment remarks may not exceed "
                f"{MAX_ASSIGNMENT_REMARK_LENGTH} characters."
            )

        return normalized

    def _validate_officer_workload(
        self,
        officer_id: UUID,
        *,
        cursor=None,
    ) -> None:
        workload = self.get_officer_workload(
            officer_id,
            cursor=cursor,
        )

        if workload >= MAX_ACTIVE_ASSIGNMENTS:
            raise ValueError(
                "The selected purchasing officer has reached the "
                "maximum number of active assignments."
            )

    @staticmethod
    def _require_active_assignment(
        assignment: dict[str, Any],
    ) -> None:
        if assignment.get("ended_at") is not None:
            raise ValueError("Assignment is no longer active.")

        current_status = BaseService.normalize_text(
            assignment.get("assignment_status")
        )

        terminal_states = {
            AssignmentState.COMPLETED,
            AssignmentState.REASSIGNED,
            AssignmentState.CANCELLED,
        }
        normalized_terminal_states = {
            state.value if hasattr(state, "value") else str(state)
            for state in terminal_states
        }

        if current_status in normalized_terminal_states:
            raise ValueError("Assignment is no longer active.")