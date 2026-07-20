"""
JCAP Construction Suite
MaterialRequestAssignmentService - Permission Tests
"""

from __future__ import annotations

from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)


class TestAssignmentPermissions(BaseAssignmentServiceTest):
    """Permission-focused tests for assign()."""

    def test_permission_service_is_called_once(self):
        self.configure_assignment_id()

        self.assign()

        self.can_assign_material_request.assert_called_once()

    def test_permission_service_receives_current_user(self):
        self.configure_assignment_id()

        self.assign()

        args, kwargs = self.can_assign_material_request.call_args
        assert not kwargs
        self.assertEqual(self.current_user, args[0])

    def test_permission_denied_prevents_repository_access(self):
        self.deny_assignment_permission()

        with self.assertRaises(PermissionError):
            self.assign()

        self.assertRepositoryNotCalled(
            self.repository,
            "has_active_assignment",
        )
        self.assertRepositoryNotCalled(
            self.repository,
            "create_assignment",
        )

    def test_permission_checked_before_validation(self):
        self.deny_assignment_permission()

        with self.assertRaises(PermissionError):
            self.assign()

        self.assertRepositoryNotCalled(
            self.repository,
            "get_officer_workload",
        )

    def test_allowed_user_reaches_repository(self):
        self.configure_assignment_id()

        self.assign()

        self.assertRepositoryCalled(
            self.repository,
            "has_active_assignment",
            expected_count=1,
        )