"""
JCAP Construction Suite
MaterialRequestAssignmentService - Reassignment Tests
"""

from __future__ import annotations

from core.workflow.material_request_workflow import AssignmentState
from modules.quotation.constants.assignment_constants import (
    MAX_ASSIGNMENT_REMARK_LENGTH,
)
from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)


class TestReassign(BaseAssignmentServiceTest):
    """Tests for MaterialRequestAssignmentService.reassign()."""

    def test_reassign_returns_updated_assignment(self):
        self.seed_active_assignment()

        result = self.reassign()

        self.assertEqual(self.ASSIGNMENT_ID, result["id"])
        self.assertEqual(
            AssignmentState.REASSIGNED,
            result["assignment_status"],
        )
        self.assertIsNotNone(result["ended_at"])

    def test_reassign_persists_reassigned_state(self):
        self.seed_active_assignment()

        self.reassign()

        self.assert_reassign_called_once_with()

    def test_reassign_fetches_assignment_before_update(self):
        self.seed_active_assignment()

        self.reassign()

        self.assertRepositoryCalled(
            self.repository,
            "get_by_id",
            expected_count=1,
        )
        self.assertEqual(
            {
                "assignment_id": self.ASSIGNMENT_ID,
                "cursor": None,
            },
            self.repository.last_call("get_by_id"),
        )

    def test_reassign_accepts_uuid_string(self):
        self.seed_active_assignment()

        result = self.reassign(
            assignment_id=str(self.ASSIGNMENT_ID),
        )

        self.assertEqual(self.ASSIGNMENT_ID, result["id"])
        self.assert_reassign_called_once_with()

    def test_reassign_forwards_cursor(self):
        cursor = object()
        self.seed_active_assignment()

        self.reassign(cursor=cursor)

        self.assertEqual(
            {
                "assignment_id": self.ASSIGNMENT_ID,
                "cursor": cursor,
            },
            self.repository.last_call("get_by_id"),
        )
        self.assert_reassign_called_once_with(cursor=cursor)

    def test_reassign_uses_custom_remarks(self):
        remarks = "Transferred to another purchasing officer."
        self.seed_active_assignment()

        result = self.reassign(remarks=remarks)

        self.assertEqual(remarks, result["remarks"])
        self.assert_reassign_called_once_with(remarks=remarks)

    def test_reassign_trims_remarks(self):
        self.seed_active_assignment()

        result = self.reassign(remarks="  Workload balancing.  ")

        self.assertEqual("Workload balancing.", result["remarks"])
        self.assert_reassign_called_once_with(
            remarks="Workload balancing.",
        )

    def test_reassign_accepts_none_remarks(self):
        original = self.seed_active_assignment()

        result = self.reassign(remarks=None)

        self.assertEqual(original["remarks"], result["remarks"])
        self.assert_reassign_called_once_with(remarks=None)

    def test_reassign_converts_blank_remarks_to_none(self):
        original = self.seed_active_assignment()

        result = self.reassign(remarks="   ")

        self.assertEqual(original["remarks"], result["remarks"])
        self.assert_reassign_called_once_with(remarks=None)

    def test_reassign_accepts_maximum_length_remarks(self):
        remarks = "R" * MAX_ASSIGNMENT_REMARK_LENGTH
        self.seed_active_assignment()

        result = self.reassign(remarks=remarks)

        self.assertEqual(remarks, result["remarks"])
        self.assert_reassign_called_once_with(remarks=remarks)

    def test_reassign_rejects_remarks_over_maximum_length(self):
        remarks = "R" * (MAX_ASSIGNMENT_REMARK_LENGTH + 1)
        self.seed_active_assignment()

        self.assertValidationError(
            lambda: self.reassign(remarks=remarks),
            (
                "Assignment remarks may not exceed "
                f"{MAX_ASSIGNMENT_REMARK_LENGTH} characters."
            ),
        )

        self.assert_reassignment_not_performed()

    def test_reassign_requires_assignment_id(self):
        self.assertValidationError(
            lambda: self.reassign(assignment_id=None),
        )

        self.assertRepositoryNotCalled(
            self.repository,
            "get_by_id",
        )
        self.assert_reassignment_not_performed()

    def test_reassign_rejects_invalid_assignment_id(self):
        self.assertValidationError(
            lambda: self.reassign(assignment_id="not-a-uuid"),
        )

        self.assertRepositoryNotCalled(
            self.repository,
            "get_by_id",
        )
        self.assert_reassignment_not_performed()

    def test_reassign_requires_current_user(self):
        self.assertValidationError(
            lambda: self.reassign(current_user=None),
        )

        self.assertRepositoryNotCalled(
            self.repository,
            "get_by_id",
        )
        self.assert_reassignment_not_performed()

    def test_reassign_denies_unauthorized_user(self):
        self.deny_reassignment_permission()

        self.assertPermissionDenied(
            lambda: self.reassign(),
            "You do not have permission to reassign Material Requests.",
        )

        self.assertRepositoryNotCalled(
            self.repository,
            "get_by_id",
        )
        self.assert_reassignment_not_performed()

    def test_reassign_raises_when_assignment_not_found(self):
        self.assertValidationError(
            lambda: self.reassign(
                assignment_id=self.new_uuid(),
            ),
            "Assignment was not found.",
        )

        self.assert_reassignment_not_performed()

    def test_reassign_rejects_completed_assignment(self):
        assignment = (
            self.assignment_builder
            .with_id(self.ASSIGNMENT_ID)
            .for_material_request(self.MATERIAL_REQUEST_ID)
            .assigned_to(self.ASSIGNED_TO_ID)
            .assigned_by(self.ASSIGNED_BY_ID)
            .completed()
            .build()
        )
        self.repository.store(self.ASSIGNMENT_ID, assignment)

        self.assertValidationError(
            lambda: self.reassign(),
            "Assignment is no longer active.",
        )

        self.assert_reassignment_not_performed()

    def test_reassign_rejects_cancelled_assignment(self):
        assignment = (
            self.assignment_builder
            .with_id(self.ASSIGNMENT_ID)
            .for_material_request(self.MATERIAL_REQUEST_ID)
            .assigned_to(self.ASSIGNED_TO_ID)
            .assigned_by(self.ASSIGNED_BY_ID)
            .cancelled()
            .build()
        )
        self.repository.store(self.ASSIGNMENT_ID, assignment)

        self.assertValidationError(
            lambda: self.reassign(),
            "Assignment is no longer active.",
        )

        self.assert_reassignment_not_performed()

    def test_reassign_rejects_already_reassigned_assignment(self):
        assignment = (
            self.assignment_builder
            .with_id(self.ASSIGNMENT_ID)
            .for_material_request(self.MATERIAL_REQUEST_ID)
            .assigned_to(self.ASSIGNED_TO_ID)
            .assigned_by(self.ASSIGNED_BY_ID)
            .reassigned()
            .build()
        )
        self.repository.store(self.ASSIGNMENT_ID, assignment)

        self.assertValidationError(
            lambda: self.reassign(),
            "Assignment is no longer active.",
        )

        self.assert_reassignment_not_performed()

    def test_reassign_rejects_assignment_with_ended_at(self):
        assignment = (
            self.assignment_builder
            .with_id(self.ASSIGNMENT_ID)
            .for_material_request(self.MATERIAL_REQUEST_ID)
            .assigned_to(self.ASSIGNED_TO_ID)
            .assigned_by(self.ASSIGNED_BY_ID)
            .assigned()
            .ended()
            .build()
        )
        self.repository.store(self.ASSIGNMENT_ID, assignment)

        self.assertValidationError(
            lambda: self.reassign(),
            "Assignment is no longer active.",
        )

        self.assert_reassignment_not_performed()

    def test_reassign_propagates_get_by_id_exception(self):
        expected_error = RuntimeError("Database read failed.")
        self.repository.configure_exception(
            "get_by_id",
            expected_error,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Database read failed.",
        ):
            self.reassign()

        self.assert_reassignment_not_performed()

    def test_reassign_propagates_repository_update_exception(self):
        expected_error = RuntimeError("Database update failed.")
        self.seed_active_assignment()
        self.repository.configure_exception(
            "reassign_assignment",
            expected_error,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Database update failed.",
        ):
            self.reassign()

        self.assert_reassign_called_once_with()

    def test_reassign_rejects_optimistic_concurrency_failure(self):
        self.seed_active_assignment()
        self.repository.configure_result(
            "reassign_assignment",
            None,
        )

        self.assertValidationError(
            lambda: self.reassign(),
            (
                "Assignment could not be reassigned because it is "
                "no longer active."
            ),
        )

        self.assert_reassign_called_once_with()

    def test_reassign_removes_assignment_from_active_lookup(self):
        self.seed_active_assignment()

        self.reassign()

        self.assertIsNone(
            self.repository.get_active_assignment(
                self.MATERIAL_REQUEST_ID,
            )
        )

    def test_reassign_reduces_assigned_officer_workload(self):
        self.seed_active_assignment()
        self.set_officer_workload(3)

        self.reassign()

        self.assertEqual(
            2,
            self.repository.get_officer_workload(
                self.ASSIGNED_TO_ID,
            ),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()