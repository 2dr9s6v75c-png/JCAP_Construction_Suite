"""
JCAP Construction Suite
MaterialRequestAssignmentService - Workflow Tests
"""

from __future__ import annotations

from core.workflow.material_request_workflow import AssignmentState
from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)


class TestAssignmentWorkflow(BaseAssignmentServiceTest):
    """Workflow-focused tests for assign()."""

    def test_assign_persists_assigned_workflow_state(self):
        self.configure_assignment_id()

        self.assign()

        self.assert_create_assignment_called_once_with()

    def test_assign_uses_assigned_state_enum(self):
        self.configure_assignment_id()

        self.assign()

        call = self.repository.last_call("create_assignment")
        self.assertEqual(
            AssignmentState.ASSIGNED,
            call["assignment_status"],
        )

    def test_failed_duplicate_assignment_does_not_create_new_state(self):
        existing = self.seed_active_assignment()

        with self.assertRaises(ValueError):
            self.assign()

        active = self.repository.get_active_assignment(
            self.MATERIAL_REQUEST_ID
        )
        self.assertEqual(existing["id"], active["id"])
        self.assert_assignment_not_created()

    def test_failed_permission_check_does_not_change_workflow(self):
        self.seed_active_assignment()
        before = self.repository.get_active_assignment(
            self.MATERIAL_REQUEST_ID
        )

        self.deny_assignment_permission()

        with self.assertRaises(PermissionError):
            self.assign()

        after = self.repository.get_active_assignment(
            self.MATERIAL_REQUEST_ID
        )
        self.assertEqual(before, after)

    def test_assignment_history_initially_contains_created_assignment(self):
        self.seed_active_assignment()

        history = self.repository.get_assignment_history(
            self.MATERIAL_REQUEST_ID
        )

        self.assertEqual(1, len(history))

    def test_new_assignment_becomes_active_assignment(self):
        assignment_id = self.configure_assignment_id()

        self.assign()

        active = self.repository.get_active_assignment(
            self.MATERIAL_REQUEST_ID
        )

        self.assertIsNotNone(active)
        self.assertEqual(assignment_id, active["id"])