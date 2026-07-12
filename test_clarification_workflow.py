from uuid import uuid4

from core.clarifications.clarification_service import (
    ClarificationService,
)
from core.database.connection import get_connection
from core.organization.organization_service import OrganizationService
from core.notifications.notification_service import NotificationService


def main():
    purchasing = None
    engineer = None
    material_request_id = None
    clarification_id = None

    test_token = uuid4().hex[:8].upper()
    test_subject = f"E2E CLARIFICATION TEST {test_token}"

    try:
        print("=" * 70)
        print("JCAP SUPPLIER CLARIFICATION END-TO-END TEST")
        print("=" * 70)

        # ========================================================
        # 1. LOAD TEST USERS
        # ========================================================

        print("\n[1] Loading workflow users")

        purchasing = OrganizationService.get_user_by_username(
            "ui_create_test"
        )

        engineer = OrganizationService.get_user_by_username(
            "project_engineer_test"
        )

        if not purchasing:
            raise RuntimeError(
                "Purchasing Officer test account was not found."
            )

        if not engineer:
            raise RuntimeError(
                "Project Engineer test account was not found."
            )

        print(
            "Purchasing Officer:",
            purchasing["full_name"],
        )

        print(
            "Project Engineer:",
            engineer["full_name"],
        )

        # ========================================================
        # 2. LOAD MATERIAL REQUEST
        # ========================================================

        print("\n[2] Loading active Material Request")

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT
                    id,
                    mr_number
                FROM quotation.material_requests
                WHERE status <> 'Archived'
                ORDER BY created_at DESC
                LIMIT 1
                """
            )

            row = cur.fetchone()

        finally:
            cur.close()
            conn.close()

        if not row:
            raise RuntimeError(
                "No active Material Request is available "
                "for workflow testing."
            )

        material_request_id = row[0]
        mr_number = row[1]

        print(
            "Material Request:",
            mr_number,
        )

        # ========================================================
        # 3. RECORD SUPPLIER CLARIFICATION
        # ========================================================

        print("\n[3] Recording supplier clarification")

        clarification_id = (
            ClarificationService.record_supplier_clarification(
                material_request_id=material_request_id,
                subject=test_subject,
                supplier_question=(
                    "Please confirm the required technical "
                    "specification for this material."
                ),
                project_engineer_user_id=engineer["id"],
                current_user=purchasing,
                supplier_name="E2E TEST SUPPLIER",
                supplier_reference=(
                    f"TEST-{test_token}"
                ),
            )
        )

        print(
            "Clarification ID:",
            clarification_id,
        )

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification is not None

        assert clarification["status"] == (
            ClarificationService.STATUS_AWAITING_ENGINEERING
        )

        assert clarification["assigned_to"] == str(
            engineer["id"]
        )

        print(
            "Status:",
            clarification["status"],
        )

        # ========================================================
        # 4. VERIFY ENGINEER NOTIFICATION
        # ========================================================

        print("\n[4] Verifying Project Engineer notification")

        engineer_notifications = (
            NotificationService.get_unread_notifications(
                engineer
            )
        )

        engineer_notification = next(
            (
                notification
                for notification in engineer_notifications
                if notification["entity_id"]
                == str(clarification_id)
            ),
            None,
        )

        assert engineer_notification is not None

        assert (
            engineer_notification["notification_type"]
            == NotificationService.CLARIFICATION_REQUESTED
        )

        print(
            "Notification:",
            engineer_notification["title"],
        )

        # ========================================================
        # 5. ENGINEERING RESPONSE
        # ========================================================

        print("\n[5] Submitting Engineering response")

        response_message_id = (
            ClarificationService.submit_engineering_response(
                clarification_id=clarification_id,
                response_text=(
                    "Use the approved project technical "
                    "specification and submitted material standard."
                ),
                current_user=engineer,
            )
        )

        print(
            "Response Message ID:",
            response_message_id,
        )

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_RESPONSE_READY
        )

        print(
            "Status:",
            clarification["status"],
        )

        # ========================================================
        # 6. VERIFY PURCHASING NOTIFICATION
        # ========================================================

        print("\n[6] Verifying Purchasing Officer notification")

        purchasing_notifications = (
            NotificationService.get_unread_notifications(
                purchasing
            )
        )

        purchasing_notification = next(
            (
                notification
                for notification in purchasing_notifications
                if (
                    notification["entity_id"]
                    == str(clarification_id)
                    and notification["notification_type"]
                    == (
                        NotificationService
                        .CLARIFICATION_RESPONSE_RECEIVED
                    )
                )
            ),
            None,
        )

        assert purchasing_notification is not None

        print(
            "Notification:",
            purchasing_notification["title"],
        )

        # ========================================================
        # 7. MARK FORWARDED
        # ========================================================

        print("\n[7] Marking response as forwarded to supplier")

        result = (
            ClarificationService.mark_forwarded_to_supplier(
                clarification_id=clarification_id,
                current_user=purchasing,
                note=(
                    "Engineering response forwarded to "
                    "the supplier for confirmation."
                ),
            )
        )

        assert result is True

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_FORWARDED
        )

        print(
            "Status:",
            clarification["status"],
        )

        # ========================================================
        # 8. RECORD SUPPLIER FOLLOW-UP
        # ========================================================

        print("\n[8] Recording supplier follow-up")

        follow_up_message_id = (
            ClarificationService.record_supplier_follow_up(
                clarification_id=clarification_id,
                follow_up_text=(
                    "Supplier requests confirmation of the "
                    "applicable material thickness."
                ),
                current_user=purchasing,
            )
        )

        print(
            "Follow-up Message ID:",
            follow_up_message_id,
        )

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_AWAITING_ENGINEERING
        )

        print(
            "Status:",
            clarification["status"],
        )

        # ========================================================
        # 9. SECOND ENGINEERING RESPONSE
        # ========================================================

        print("\n[9] Submitting second Engineering response")

        second_response_id = (
            ClarificationService.submit_engineering_response(
                clarification_id=clarification_id,
                response_text=(
                    "Confirmed. Use the thickness indicated "
                    "in the approved project specification."
                ),
                current_user=engineer,
            )
        )

        print(
            "Second Response ID:",
            second_response_id,
        )

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_RESPONSE_READY
        )

        # ========================================================
        # 10. FORWARD SECOND RESPONSE
        # ========================================================

        print("\n[10] Forwarding second response")

        ClarificationService.mark_forwarded_to_supplier(
            clarification_id=clarification_id,
            current_user=purchasing,
            note=(
                "Second Engineering response forwarded "
                "to the supplier."
            ),
        )

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_FORWARDED
        )

        print(
            "Status:",
            clarification["status"],
        )

        # ========================================================
        # 11. RESOLVE
        # ========================================================

        print("\n[11] Resolving clarification")

        result = ClarificationService.resolve_clarification(
            clarification_id=clarification_id,
            current_user=purchasing,
        )

        assert result is True

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        assert clarification["status"] == (
            ClarificationService.STATUS_RESOLVED
        )

        assert clarification["resolved_at"] is not None

        assert clarification["resolved_by"] == str(
            purchasing["id"]
        )

        print(
            "Final Status:",
            clarification["status"],
        )

        # ========================================================
        # 12. VERIFY MESSAGE TIMELINE
        # ========================================================

        print("\n[12] Verifying clarification timeline")

        messages = ClarificationService.get_messages(
            clarification_id
        )

        assert len(messages) == 6

        expected_types = [
            ClarificationService.MESSAGE_SUPPLIER_QUESTION,
            ClarificationService.MESSAGE_ENGINEERING_RESPONSE,
            ClarificationService.MESSAGE_PURCHASING_NOTE,
            ClarificationService.MESSAGE_SUPPLIER_FOLLOW_UP,
            ClarificationService.MESSAGE_ENGINEERING_RESPONSE,
            ClarificationService.MESSAGE_PURCHASING_NOTE,
        ]

        actual_types = [
            message["message_type"]
            for message in messages
        ]

        assert actual_types == expected_types

        print(
            "Message Count:",
            len(messages),
        )

        for message in messages:
            print(
                f"- {message['message_type']} "
                f"by {message['sent_by_full_name']}"
            )

        # ========================================================
        # SUCCESS
        # ========================================================

        print("\n" + "=" * 70)
        print("ALL SUPPLIER CLARIFICATION WORKFLOW TESTS PASSED")
        print("=" * 70)

    finally:
        # ========================================================
        # AUTOMATIC CLEANUP
        # ========================================================

        print("\n[CLEANUP] Removing E2E test records")

        conn = get_connection()
        cur = conn.cursor()

        try:
            if clarification_id:
                cur.execute(
                    """
                    DELETE FROM core.notifications
                    WHERE entity_type = 'clarification'
                      AND entity_id = %s
                    """,
                    (
                        clarification_id,
                    ),
                )

                cur.execute(
                    """
                    DELETE FROM
                        quotation.clarification_message_attachments
                    WHERE clarification_message_id IN (
                        SELECT id
                        FROM quotation.clarification_messages
                        WHERE clarification_id = %s
                    )
                    """,
                    (
                        clarification_id,
                    ),
                )

                cur.execute(
                    """
                    DELETE FROM quotation.clarification_messages
                    WHERE clarification_id = %s
                    """,
                    (
                        clarification_id,
                    ),
                )

                cur.execute(
                    """
                    DELETE FROM quotation.clarifications
                    WHERE id = %s
                    """,
                    (
                        clarification_id,
                    ),
                )

            if material_request_id:
                cur.execute(
                    """
                    DELETE FROM core.activity_logs
                    WHERE record_id = %s
                      AND details LIKE %s
                    """,
                    (
                        material_request_id,
                        f"%{test_subject}%",
                    ),
                )

            conn.commit()

            print(
                "Cleanup completed successfully."
            )

        except Exception:
            conn.rollback()

            print(
                "WARNING: Automatic cleanup failed."
            )

            raise

        finally:
            cur.close()
            conn.close()

        print(
            "No E2E clarification test records remain."
        )


if __name__ == "__main__":
    main()