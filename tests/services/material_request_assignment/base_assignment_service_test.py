"""
JCAP Construction Suite
Base Material Request Assignment Service Test

Shared setup and assertions for MaterialRequestAssignmentService unit tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch
from uuid import UUID

from core.workflow.material_request_workflow import AssignmentState
from modules.quotation.services.material_request_assignment_service import (
    MaterialRequestAssignmentService,
)
from tests.base.base_test_case import BaseTestCase
from tests.builders.assignment_builder import AssignmentBuilder
from tests.builders.material_request_builder import MaterialRequestBuilder
from tests.builders.notification_builder import NotificationBuilder
from tests.builders.workflow_builder import WorkflowBuilder
from tests.services.material_request_assignment.fake_dependencies import (
    FakeMaterialRequestAssignmentRepository,
)


_UNSET = object()


class BaseAssignmentServiceTest(BaseTestCase):
    """
    Shared test foundation for MaterialRequestAssignmentService.

    The service directly depends on its repository and PermissionService.
    Transaction management, workflow coordination, notification dispatch,
    and replacement-assignment creation belong to process-layer tests.
    """

    MATERIAL_REQUEST_ID = UUID(
        "00000000-0000-0000-0000-000000001001"
    )
    ASSIGNED_TO_ID = UUID(
        "00000000-0000-0000-0000-000000004002"
    )
    ASSIGNED_BY_ID = UUID(
        "00000000-0000-0000-0000-000000004001"
    )
    ASSIGNMENT_ID = UUID(
        "00000000-0000-0000-0000-000000002001"
    )

    DEFAULT_REMARKS = "Assigned for quotation processing."
    DEFAULT_REASSIGNMENT_REMARKS = (
        "Reassigned due to workload balancing."
    )

    def setUp(self) -> None:
        super().setUp()

        self.repository = self.register_test_double(
            FakeMaterialRequestAssignmentRepository()
        )
        self.service = MaterialRequestAssignmentService(
            repository=self.repository
        )

        self.current_user: dict[str, Any] = {
            "id": str(self.ASSIGNED_BY_ID),
            "username": "assigning.user",
            "full_name": "Assigning User",
            "role": "Administrator",
        }

        self.material_request_builder = MaterialRequestBuilder()
        self.assignment_builder = AssignmentBuilder()
        self.workflow_builder = WorkflowBuilder()
        self.notification_builder = NotificationBuilder()

        assign_permission_patcher = patch(
            (
                "modules.quotation.services."
                "material_request_assignment_service."
                "PermissionService.can_assign_material_request"
            ),
            return_value=True,
        )
        self.can_assign_material_request = (
            assign_permission_patcher.start()
        )
        self.addCleanup(assign_permission_patcher.stop)

        reassign_permission_patcher = patch(
            (
                "modules.quotation.services."
                "material_request_assignment_service."
                "PermissionService.can_reassign_material_request"
            ),
            return_value=True,
        )
        self.can_reassign_material_request = (
            reassign_permission_patcher.start()
        )
        self.addCleanup(reassign_permission_patcher.stop)

    def assign(
        self,
        *,
        material_request_id: UUID | str | None | object = _UNSET,
        assigned_to: UUID | str | None | object = _UNSET,
        current_user: dict[str, Any] | None | object = _UNSET,
        remarks: str | None = DEFAULT_REMARKS,
        cursor: Any = None,
    ) -> UUID:
        """
        Execute assign() with valid defaults.

        The sentinel allows validation tests to pass None intentionally.
        """
        return self.service.assign(
            material_request_id=(
                self.MATERIAL_REQUEST_ID
                if material_request_id is _UNSET
                else material_request_id
            ),
            assigned_to=(
                self.ASSIGNED_TO_ID
                if assigned_to is _UNSET
                else assigned_to
            ),
            current_user=(
                self.current_user
                if current_user is _UNSET
                else current_user
            ),
            remarks=remarks,
            cursor=cursor,
        )

    def reassign(
        self,
        *,
        assignment_id: UUID | str | None | object = _UNSET,
        current_user: dict[str, Any] | None | object = _UNSET,
        remarks: str | None = DEFAULT_REASSIGNMENT_REMARKS,
        cursor: Any = None,
    ) -> dict[str, Any]:
        """
        Execute reassign() with valid defaults.

        An active assignment is seeded automatically when the default
        assignment ID is used and no matching record already exists.
        """
        resolved_assignment_id = (
            self.ASSIGNMENT_ID
            if assignment_id is _UNSET
            else assignment_id
        )

        if (
            resolved_assignment_id == self.ASSIGNMENT_ID
            and self.repository.get_stored(self.ASSIGNMENT_ID) is None
        ):
            self.seed_active_assignment()

        return self.service.reassign(
            assignment_id=resolved_assignment_id,
            current_user=(
                self.current_user
                if current_user is _UNSET
                else current_user
            ),
            remarks=remarks,
            cursor=cursor,
        )

    def deny_assignment_permission(self) -> None:
        """Configure assignment permission to be denied."""
        self.can_assign_material_request.return_value = False

    def deny_reassignment_permission(self) -> None:
        """Configure reassignment permission to be denied."""
        self.can_reassign_material_request.return_value = False

    def seed_active_assignment(
        self,
        *,
        material_request_id: UUID | None = None,
        assigned_to: UUID | None = None,
        assigned_by: UUID | None = None,
    ) -> dict[str, Any]:
        """Seed one active assignment in the fake repository."""
        target_material_request_id = (
            material_request_id or self.MATERIAL_REQUEST_ID
        )

        assignment = (
            self.assignment_builder
            .with_id(self.ASSIGNMENT_ID)
            .for_material_request(target_material_request_id)
            .assigned_to(assigned_to or self.ASSIGNED_TO_ID)
            .assigned_by(assigned_by or self.ASSIGNED_BY_ID)
            .assigned()
            .active()
            .build()
        )

        self.repository.set_active_assignment(
            target_material_request_id,
            assignment,
        )
        return assignment

    def set_officer_workload(
        self,
        workload: int,
        *,
        officer_id: UUID | None = None,
    ) -> None:
        """Set a deterministic workload for the selected officer."""
        self.repository.set_officer_workload(
            officer_id or self.ASSIGNED_TO_ID,
            workload,
        )

    def configure_assignment_id(
        self,
        assignment_id: UUID | None = None,
    ) -> UUID:
        """Configure create_assignment to return a selected UUID."""
        configured_id = assignment_id or self.ASSIGNMENT_ID
        self.repository.configure_result(
            "create_assignment",
            configured_id,
        )
        return configured_id

    def assert_create_assignment_called_once_with(
        self,
        *,
        material_request_id: UUID | None = None,
        assigned_to: UUID | None = None,
        assigned_by: UUID | None = None,
        remarks: str | None = DEFAULT_REMARKS,
        cursor: Any = None,
    ) -> None:
        """Assert the exact persistence request produced by assign()."""
        self.assertRepositoryCalled(
            self.repository,
            "create_assignment",
            expected_count=1,
        )

        self.assertEqual(
            self.repository.last_call("create_assignment"),
            {
                "material_request_id": (
                    material_request_id or self.MATERIAL_REQUEST_ID
                ),
                "assigned_to": assigned_to or self.ASSIGNED_TO_ID,
                "assigned_by": assigned_by or self.ASSIGNED_BY_ID,
                "assignment_status": AssignmentState.ASSIGNED,
                "remarks": remarks,
                "cursor": cursor,
            },
        )

    def assert_reassign_called_once_with(
        self,
        *,
        assignment_id: UUID | None = None,
        remarks: str | None = DEFAULT_REASSIGNMENT_REMARKS,
        cursor: Any = None,
    ) -> None:
        """Assert the exact persistence request produced by reassign()."""
        self.assertRepositoryCalled(
            self.repository,
            "reassign_assignment",
            expected_count=1,
        )

        self.assertEqual(
            self.repository.last_call("reassign_assignment"),
            {
                "assignment_id": assignment_id or self.ASSIGNMENT_ID,
                "assignment_status": AssignmentState.REASSIGNED,
                "remarks": remarks,
                "cursor": cursor,
            },
        )

    def assert_assignment_validation_calls(
        self,
        *,
        material_request_id: UUID | None = None,
        assigned_to: UUID | None = None,
        cursor: Any = None,
    ) -> None:
        """Assert duplicate and workload validation repository calls."""
        self.assertEqual(
            self.repository.last_call("has_active_assignment"),
            {
                "material_request_id": (
                    material_request_id or self.MATERIAL_REQUEST_ID
                ),
                "cursor": cursor,
            },
        )
        self.assertEqual(
            self.repository.last_call("get_officer_workload"),
            {
                "officer_id": assigned_to or self.ASSIGNED_TO_ID,
                "cursor": cursor,
            },
        )

    def assert_assignment_not_created(self) -> None:
        """Assert that assignment creation was not reached."""
        self.assertRepositoryNotCalled(
            self.repository,
            "create_assignment",
        )

    def assert_reassignment_not_performed(self) -> None:
        """Assert that reassignment persistence was not reached."""
        self.assertRepositoryNotCalled(
            self.repository,
            "reassign_assignment",
        )