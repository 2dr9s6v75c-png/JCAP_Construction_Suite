"""
JCAP Construction Suite
MaterialRequestAssignmentService - Edge Case Tests
"""

from __future__ import annotations

from modules.quotation.constants.assignment_constants import (
    MAX_ACTIVE_ASSIGNMENTS,
    MAX_ASSIGNMENT_REMARK_LENGTH,
)
from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)
from tests.services.material_request_assignment import constants as C


class TestAssignmentEdgeCases(BaseAssignmentServiceTest):
    """Boundary, regression, and repository-failure tests for assign()."""

    def test_workload_one_below_limit_is_allowed(self):
        self.set_officer_workload(MAX_ACTIVE_ASSIGNMENTS - 1)
        expected_id = self.configure_assignment_id()

        result = self.assign()

        self.assertEqual(expected_id, result)
        self.assert_create_assignment_called_once_with()

    def test_workload_exactly_at_limit_is_rejected(self):
        self.set_officer_workload(MAX_ACTIVE_ASSIGNMENTS)

        with self.assertRaisesRegex(
            ValueError,
            "reached the maximum number of active assignments",
        ):
            self.assign()

        self.assert_assignment_not_created()

    def test_remarks_exactly_at_maximum_length_are_allowed(self):
        remarks = "x" * MAX_ASSIGNMENT_REMARK_LENGTH
        self.configure_assignment_id()

        self.assign(remarks=remarks)

        self.assert_create_assignment_called_once_with(
            remarks=remarks,
        )

    def test_whitespace_around_uuid_strings_is_normalized(self):
        expected_id = self.configure_assignment_id()

        result = self.assign(
            material_request_id=f" {self.MATERIAL_REQUEST_ID} ",
        )

        self.assertEqual(expected_id, result)
        self.assert_create_assignment_called_once_with(
            material_request_id=self.MATERIAL_REQUEST_ID,
        )

    def test_repository_duplicate_check_failure_is_propagated(self):
        expected_error = RuntimeError("duplicate check unavailable")
        self.repository.configure_exception(
            "has_active_assignment",
            expected_error,
        )

        with self.assertRaises(RuntimeError) as context:
            self.assign()

        self.assertIs(expected_error, context.exception)
        self.assertRepositoryNotCalled(
            self.repository,
            "get_officer_workload",
        )
        self.assert_assignment_not_created()

    def test_repository_workload_failure_is_propagated(self):
        expected_error = RuntimeError("workload query unavailable")
        self.repository.configure_exception(
            "get_officer_workload",
            expected_error,
        )

        with self.assertRaises(RuntimeError) as context:
            self.assign()

        self.assertIs(expected_error, context.exception)
        self.assert_assignment_not_created()

    def test_repository_create_failure_is_propagated(self):
        expected_error = RuntimeError("assignment insert failed")
        self.repository.configure_exception(
            "create_assignment",
            expected_error,
        )

        with self.assertRaises(RuntimeError) as context:
            self.assign()

        self.assertIs(expected_error, context.exception)

    def test_assignee_may_be_same_as_assigning_user_when_authorized(self):
        self.configure_assignment_id()

        self.assign(assigned_to=self.ASSIGNED_BY_ID)

        self.assert_create_assignment_called_once_with(
            assigned_to=self.ASSIGNED_BY_ID,
        )

    def test_second_material_request_is_independent(self):
        self.seed_active_assignment(
            material_request_id=self.MATERIAL_REQUEST_ID,
        )
        self.configure_assignment_id(C.SECOND_ASSIGNMENT_ID)

        result = self.assign(
            material_request_id=C.SECOND_MATERIAL_REQUEST_ID,
        )

        self.assertEqual(C.SECOND_ASSIGNMENT_ID, result)
        self.assert_create_assignment_called_once_with(
            material_request_id=C.SECOND_MATERIAL_REQUEST_ID,
        )

    def test_empty_string_remarks_use_default(self):
        self.configure_assignment_id()

        self.assign(remarks="")

        call = self.repository.last_call("create_assignment")
        self.assertIsNotNone(call["remarks"])
        self.assertNotEqual("", call["remarks"])