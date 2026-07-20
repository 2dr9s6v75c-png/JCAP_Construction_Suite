"""
JCAP Construction Suite
MaterialRequestAssignmentService - Assignment Tests
"""

from __future__ import annotations

from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)
from tests.services.material_request_assignment import constants as C


class TestAssign(BaseAssignmentServiceTest):
    """Happy-path tests for MaterialRequestAssignmentService.assign()."""

    def test_assign_returns_repository_assignment_id(self):
        expected_id = self.configure_assignment_id()

        result = self.assign()

        self.assertEqual(expected_id, result)

    def test_assign_persists_assignment(self):
        self.configure_assignment_id()

        self.assign()

        self.assert_create_assignment_called_once_with()
        self.assert_assignment_validation_calls()

    def test_assign_uses_custom_remarks(self):
        remarks = "Urgent RFQ."

        self.configure_assignment_id()

        self.assign(remarks=remarks)

        self.assert_create_assignment_called_once_with(
            remarks=remarks,
        )

    def test_assign_accepts_different_assignee(self):
        self.configure_assignment_id()

        self.assign(
            assigned_to=C.SECOND_ASSIGNED_TO_ID,
        )

        self.assert_create_assignment_called_once_with(
            assigned_to=C.SECOND_ASSIGNED_TO_ID,
        )

    def test_assign_forwards_cursor(self):
        cursor = object()

        self.configure_assignment_id()

        self.assign(cursor=cursor)

        self.assert_create_assignment_called_once_with(
            cursor=cursor,
        )
        self.assert_assignment_validation_calls(
            cursor=cursor,
        )

    def test_assign_checks_workload_before_creation(self):
        self.configure_assignment_id()
        self.set_officer_workload(C.WORKLOAD_BELOW_LIMIT)

        self.assign()

        self.assertRepositoryCalled(
            self.repository,
            "get_officer_workload",
            expected_count=1,
        )

    def test_assign_checks_for_existing_assignment(self):
        self.configure_assignment_id()

        self.assign()

        self.assertRepositoryCalled(
            self.repository,
            "has_active_assignment",
            expected_count=1,
        )