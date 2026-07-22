"""
JCAP Construction Suite
Material Request Assignment Process

Coordinates assignment-history records and the Material Request's current
assignment context inside one shared PostgreSQL transaction.

The process layer owns cross-table coordination. Validation, permissions,
workload rules, and single-assignment lifecycle operations remain in
MaterialRequestAssignmentService.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from core.database.transaction_manager import TransactionManager
from core.workflow.material_request_workflow import MaterialRequestState
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)
from modules.quotation.services.material_request_assignment_service import (
    MaterialRequestAssignmentService,
)


class MaterialRequestAssignmentProcess:
    """Coordinate complete Material Request assignment operations."""

    def __init__(
        self,
        assignment_service: MaterialRequestAssignmentService | None = None,
        material_request_repository: MaterialRequestRepository | None = None,
        transaction_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._assignment_service = (
            assignment_service or MaterialRequestAssignmentService()
        )
        self._material_request_repository = (
            material_request_repository or MaterialRequestRepository()
        )
        self._transaction_factory = (
            transaction_factory or TransactionManager
        )

    def assign(
        self,
        material_request_id: UUID | str,
        assigned_to: UUID | str,
        current_user: dict[str, Any],
        remarks: str | None = None,
    ) -> dict[str, Any]:
        """
        Create an assignment and link it to the Material Request atomically.

        Returns:
            Dictionary containing the new assignment UUID and the updated
            Material Request record.

        Raises:
            ValueError:
                When the Material Request does not exist or cannot be updated.

            PermissionError:
                When the current user cannot assign Material Requests.

            Exception:
                Any service, repository, or database error. The transaction
                manager rolls the complete operation back.
        """
        with self._transaction_factory() as cursor:
            material_request = self._material_request_repository.get_by_id(
                material_request_id,
                cursor=cursor,
            )

            if material_request is None:
                raise ValueError("Material Request not found.")

            assignment_id = self._assignment_service.assign(
                material_request_id=material_request_id,
                assigned_to=assigned_to,
                current_user=current_user,
                remarks=remarks,
                cursor=cursor,
            )

            updated_material_request = (
                self._material_request_repository.update_assignment_context(
                    material_request_id=material_request_id,
                    assignment_id=assignment_id,
                    assigned_to=assigned_to,
                    workflow_status=MaterialRequestState.ASSIGNED,
                    cursor=cursor,
                )
            )

            if updated_material_request is None:
                raise ValueError(
                    "Material Request assignment context could not be updated."
                )

            return {
                "assignment_id": assignment_id,
                "material_request": updated_material_request,
            }

    def reassign(
        self,
        assignment_id: UUID | str,
        assigned_to: UUID | str,
        current_user: dict[str, Any],
        remarks: str | None = None,
        replacement_remarks: str | None = None,
    ) -> dict[str, Any]:
        """
        End the current assignment, create its replacement, and relink the
        Material Request atomically.

        The old assignment is first moved to Reassigned by the service.
        A replacement assignment is then created through the same service so
        permission, duplicate-assignment, workload, UUID, and remarks rules
        remain centralized.

        Returns:
            Dictionary containing the closed assignment, replacement
            assignment UUID, and updated Material Request record.
        """
        with self._transaction_factory() as cursor:
            closed_assignment = self._assignment_service.reassign(
                assignment_id=assignment_id,
                current_user=current_user,
                remarks=remarks,
                cursor=cursor,
            )

            material_request_id = closed_assignment.get(
                "material_request_id"
            )

            if material_request_id is None:
                raise ValueError(
                    "Reassigned assignment has no Material Request ID."
                )

            replacement_assignment_id = self._assignment_service.assign(
                material_request_id=material_request_id,
                assigned_to=assigned_to,
                current_user=current_user,
                remarks=replacement_remarks,
                cursor=cursor,
            )

            updated_material_request = (
                self._material_request_repository.update_assignment_context(
                    material_request_id=material_request_id,
                    assignment_id=replacement_assignment_id,
                    assigned_to=assigned_to,
                    workflow_status=MaterialRequestState.ASSIGNED,
                    cursor=cursor,
                )
            )

            if updated_material_request is None:
                raise ValueError(
                    "Material Request assignment context could not be updated."
                )

            return {
                "closed_assignment": closed_assignment,
                "assignment_id": replacement_assignment_id,
                "material_request": updated_material_request,
            }