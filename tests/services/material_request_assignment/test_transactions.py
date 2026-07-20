"""
JCAP Construction Suite
MaterialRequestAssignmentService - Transaction Tests
"""

from __future__ import annotations

from tests.base.fake_transaction import FakeTransaction
from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)


class TestAssignmentTransactions(BaseAssignmentServiceTest):
    """
    Transaction-oriented tests.

    These tests are written for the future process layer where an explicit
    transaction manager coordinates assignment, workflow and notifications.
    """

    def setUp(self):
        super().setUp()
        self.transaction = FakeTransaction()

    def test_successful_assignment_can_execute_inside_transaction(self):
        self.configure_assignment_id()

        with self.transaction:
            result = self.assign()

        self.assertEqual(self.ASSIGNMENT_ID, result)
        self.assertTrue(self.transaction.committed)

    def test_repository_failure_rolls_back_transaction(self):
        self.repository.configure_exception(
            "create_assignment",
            RuntimeError("database failure"),
        )

        with self.assertRaises(RuntimeError):
            with self.transaction:
                self.assign()

        self.assertTrue(self.transaction.rolled_back)

    def test_duplicate_assignment_rolls_back_transaction(self):
        self.seed_active_assignment()

        with self.assertRaises(ValueError):
            with self.transaction:
                self.assign()

        self.assertTrue(self.transaction.rolled_back)

    def test_permission_failure_rolls_back_transaction(self):
        self.deny_assignment_permission()

        with self.assertRaises(PermissionError):
            with self.transaction:
                self.assign()

        self.assertTrue(self.transaction.rolled_back)

    def test_failed_transaction_does_not_persist_assignment(self):
        self.repository.configure_exception(
            "create_assignment",
            RuntimeError("database failure"),
        )

        with self.assertRaises(RuntimeError):
            with self.transaction:
                self.assign()

        self.assertTrue(self.transaction.rolled_back)
        self.assertRepositoryCalled(
            self.repository,
            "create_assignment",
            expected_count=1,
        )
        self.assertEqual({}, self.repository.records)


if __name__ == "__main__":
    import unittest

    unittest.main()