from core.database.connection import get_connection
from core.database.repositories.clarification_repository import (
    ClarificationRepository,
)
from core.organization.organization_service import OrganizationService


def main():
    conn = None
    cur = None

    try:
        print("=" * 60)
        print("JCAP CLARIFICATION REPOSITORY TRANSACTION TEST")
        print("=" * 60)

        admin = OrganizationService.get_user_by_username("admin")

        if not admin:
            raise RuntimeError("Administrator account was not found.")

        admin_id = admin["id"]

        conn = get_connection()
        cur = conn.cursor()

        # ========================================================
        # 1. FIND MATERIAL REQUEST
        # ========================================================

        print("\n[1] Loading Material Request")

        cur.execute(
            """
            SELECT
                id,
                COALESCE(mr_number, request_no)
            FROM quotation.material_requests
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        material_request = cur.fetchone()

        if not material_request:
            raise RuntimeError(
                "No Material Request exists for repository testing."
            )

        material_request_id = material_request[0]
        material_request_number = material_request[1]

        print(
            f"Material Request: {material_request_number}"
        )

        # ========================================================
        # 2. CREATE CLARIFICATION
        # ========================================================

        print("\n[2] Creating temporary clarification")

        clarification_id = (
            ClarificationRepository.create_clarification(
                material_request_id=material_request_id,
                subject="Temporary Repository Test Clarification",
                supplier_name="TEST SUPPLIER",
                supplier_reference="TEST-REF-001",
                assigned_to=admin_id,
                created_by=admin_id,
                cursor=cur,
            )
        )

        print(
            f"Clarification ID: {clarification_id}"
        )

        assert ClarificationRepository.exists(
            clarification_id,
            cursor=cur,
        )

        # ========================================================
        # 3. CREATE SUPPLIER QUESTION
        # ========================================================

        print("\n[3] Creating supplier question")

        supplier_message_id = (
            ClarificationRepository.create_message(
                clarification_id=clarification_id,
                message_type="Supplier Question",
                message_text=(
                    "Please confirm the required material specification."
                ),
                sent_by=admin_id,
                cursor=cur,
            )
        )

        print(
            f"Supplier Question ID: {supplier_message_id}"
        )

        # ========================================================
        # 4. CREATE ENGINEERING RESPONSE
        # ========================================================

        print("\n[4] Creating engineering response")

        engineering_message_id = (
            ClarificationRepository.create_message(
                clarification_id=clarification_id,
                message_type="Engineering Response",
                message_text=(
                    "Use the approved project material specification."
                ),
                sent_by=admin_id,
                cursor=cur,
            )
        )

        print(
            f"Engineering Response ID: {engineering_message_id}"
        )

        # ========================================================
        # 5. CREATE ATTACHMENT METADATA
        # ========================================================

        print("\n[5] Creating attachment metadata")

        attachment_id = (
            ClarificationRepository.create_message_attachment(
                clarification_message_id=engineering_message_id,
                original_filename="test_specification.pdf",
                stored_filename="TEST_SPECIFICATION_001.pdf",
                file_extension=".pdf",
                file_size=1024,
                uploaded_by=admin_id,
                cursor=cur,
            )
        )

        print(
            f"Attachment ID: {attachment_id}"
        )

        # ========================================================
        # 6. READ CLARIFICATION
        # ========================================================

        print("\n[6] Reading clarification")

        clarification = (
            ClarificationRepository.get_clarification_by_id(
                clarification_id,
                cursor=cur,
            )
        )

        assert clarification is not None
        assert clarification["subject"] == (
            "Temporary Repository Test Clarification"
        )
        assert clarification["supplier_name"] == "TEST SUPPLIER"
        assert clarification["assigned_to"] == str(admin_id)

        print(
            f"Subject: {clarification['subject']}"
        )

        print(
            f"Status: {clarification['status']}"
        )

        # ========================================================
        # 7. READ MESSAGES
        # ========================================================

        print("\n[7] Reading clarification messages")

        messages = ClarificationRepository.get_messages(
            clarification_id,
            cursor=cur,
        )

        assert len(messages) == 2

        assert messages[0]["message_type"] == (
            "Supplier Question"
        )

        assert messages[1]["message_type"] == (
            "Engineering Response"
        )

        assert messages[1]["attachment_count"] == 1

        print(
            f"Message Count: {len(messages)}"
        )

        for message in messages:
            print(
                f"- {message['message_type']}: "
                f"{message['message_text']}"
            )

        # ========================================================
        # 8. READ ATTACHMENTS
        # ========================================================

        print("\n[8] Reading message attachments")

        attachments = (
            ClarificationRepository.get_message_attachments(
                engineering_message_id,
                cursor=cur,
            )
        )

        assert len(attachments) == 1

        assert attachments[0]["original_filename"] == (
            "test_specification.pdf"
        )

        assert attachments[0]["file_size"] == 1024

        print(
            f"Attachment Count: {len(attachments)}"
        )

        print(
            f"Attachment: "
            f"{attachments[0]['original_filename']}"
        )

        # ========================================================
        # 9. UPDATE STATUS
        # ========================================================

        print("\n[9] Updating clarification status")

        updated = ClarificationRepository.update_status(
            clarification_id,
            "Response Ready",
            cursor=cur,
        )

        assert updated is True

        clarification = (
            ClarificationRepository.get_clarification_by_id(
                clarification_id,
                cursor=cur,
            )
        )

        assert clarification["status"] == "Response Ready"

        print(
            f"Updated Status: {clarification['status']}"
        )

        # ========================================================
        # 10. RESOLVE CLARIFICATION
        # ========================================================

        print("\n[10] Resolving clarification")

        resolved = ClarificationRepository.resolve(
            clarification_id,
            admin_id,
            cursor=cur,
        )

        assert resolved is True

        clarification = (
            ClarificationRepository.get_clarification_by_id(
                clarification_id,
                cursor=cur,
            )
        )

        assert clarification["status"] == "Resolved"
        assert clarification["resolved_at"] is not None
        assert clarification["resolved_by"] == str(admin_id)

        print(
            f"Final Status: {clarification['status']}"
        )

        # ========================================================
        # SUCCESS
        # ========================================================

        print("\n" + "=" * 60)
        print("ALL CLARIFICATION REPOSITORY TESTS PASSED")
        print("=" * 60)

    except Exception:
        if conn is not None:
            conn.rollback()

        raise

    finally:
        if conn is not None:
            conn.rollback()

        if cur is not None:
            cur.close()

        if conn is not None:
            conn.close()

        print("\nTransaction rolled back.")
        print("No temporary clarification data was saved.")


if __name__ == "__main__":
    main()