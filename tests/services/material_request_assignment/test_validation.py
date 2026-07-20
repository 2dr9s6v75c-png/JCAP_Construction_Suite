"""
JCAP Construction Suite
MaterialRequestAssignmentService - Validation Tests
"""

from __future__ import annotations

from uuid import uuid4

from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)
from tests.services.material_request_assignment import constants as C


class TestAssignmentValidation(BaseAssignmentServiceTest):
    """Validation and guard-clause tests for assign()."""

    def test_duplicate_assignment_is_rejected(self):
        self.seed_active_assignment()

        with self.assertRaises(Exception):
            self.assign()

        self.assert_assignment_not_created()

    def test_permission_denied_is_rejected(self):
        self.deny_assignment_permission()

        with self.assertRaises(Exception):
            self.assign()

        self.assert_assignment_not_created()

    def test_workload_limit_is_rejected(self):
        self.set_officer_workload(C.WORKLOAD_AT_LIMIT)

        with self.assertRaises(Exception):
            self.assign()

        self.assert_assignment_not_created()

    def test_invalid_material_request_uuid(self):
        with self.assertRaises(Exception):
            self.assign(material_request_id="not-a-uuid")

    def test_invalid_assigned_to_uuid(self):
        with self.assertRaises(Exception):
            self.assign(assigned_to="not-a-uuid")

    def test_missing_current_user(self):
        with self.assertRaises(Exception):
            self.assign(current_user=None)

    def test_missing_current_user_id(self):
        user = {
            "username": "tester",
            "role": "Administrator",
        }

        with self.assertRaises(Exception):
            self.assign(current_user=user)

    def test_accepts_valid_uuid_strings(self):
        self.configure_assignment_id()

        result = self.assign(
            material_request_id=str(uuid4()),
            assigned_to=str(uuid4()),
        )

        self.assertIsNotNone(result)