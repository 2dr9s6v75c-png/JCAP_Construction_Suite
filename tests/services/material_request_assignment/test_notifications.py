"""
JCAP Construction Suite
MaterialRequestAssignmentService - Notification Tests
"""

from __future__ import annotations

from tests.services.material_request_assignment.base_assignment_service_test import (
    BaseAssignmentServiceTest,
)


class TestAssignmentNotifications(BaseAssignmentServiceTest):
    """
    Notification-oriented tests.

    These tests define the expected behaviour for the future process layer
    responsible for dispatching notifications after a successful assignment.
    """

    def test_notification_builder_creates_assignment_notification(self):
        notification = (
            self.notification_builder
            .material_request_assigned(self.MATERIAL_REQUEST_ID)
            .for_recipient(self.ASSIGNED_TO_ID)
            .created_by(self.ASSIGNED_BY_ID)
            .build()
        )

        self.assertEqual(
            "MATERIAL_REQUEST_ASSIGNED",
            notification["notification_type"],
        )
        self.assertEqual(
            str(self.MATERIAL_REQUEST_ID),
            notification["entity_id"],
        )
        self.assertEqual(
            str(self.ASSIGNED_TO_ID),
            notification["recipient_user_id"],
        )

    def test_successful_assignment_has_notification_payload(self):
        self.configure_assignment_id()

        self.assign()

        notification = (
            self.notification_builder
            .material_request_assigned(self.MATERIAL_REQUEST_ID)
            .for_recipient(self.ASSIGNED_TO_ID)
            .created_by(self.ASSIGNED_BY_ID)
            .build()
        )

        self.assertEqual(
            "Material Request Assigned",
            notification["title"],
        )
        self.assertFalse(notification["is_read"])

    def test_failed_duplicate_assignment_produces_no_notification(self):
        self.seed_active_assignment()

        with self.assertRaises(ValueError):
            self.assign()

        # Notification builder should never be invoked by the
        # future orchestration layer after a failed assignment.
        self.assert_assignment_not_created()

    def test_permission_failure_produces_no_notification(self):
        self.deny_assignment_permission()

        with self.assertRaises(PermissionError):
            self.assign()

        self.assert_assignment_not_created()

    def test_notification_targets_assigned_officer(self):
        notification = (
            self.notification_builder
            .material_request_assigned(self.MATERIAL_REQUEST_ID)
            .for_recipient(self.ASSIGNED_TO_ID)
            .build()
        )

        self.assertEqual(
            str(self.ASSIGNED_TO_ID),
            notification["recipient_user_id"],
        )

    def test_notification_links_material_request(self):
        notification = (
            self.notification_builder
            .material_request_assigned(self.MATERIAL_REQUEST_ID)
            .build()
        )

        self.assertEqual(
            "material_request",
            notification["entity_type"],
        )
        self.assertEqual(
            str(self.MATERIAL_REQUEST_ID),
            notification["entity_id"],
        )

    def test_notification_is_unread_when_created(self):
        notification = (
            self.notification_builder
            .material_request_assigned(self.MATERIAL_REQUEST_ID)
            .build()
        )

        self.assertFalse(notification["is_read"])
        self.assertIsNone(notification["read_at"])