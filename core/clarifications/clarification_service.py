from core.database.connection import get_connection
from core.database.repositories.clarification_repository import (
    ClarificationRepository,
)
from core.notifications.notification_service import NotificationService
from core.organization.organization_service import OrganizationService
from core.security.permissions import PermissionService


class ClarificationService:
    """
    Business workflow service for Supplier Clarifications.

    The service owns:
    - Permission enforcement
    - Workflow status transitions
    - PostgreSQL transactions
    - Persistent notifications
    - Activity logging

    Repositories own SQL data access.
    """

    STATUS_AWAITING_ENGINEERING = "Awaiting Engineering Response"
    STATUS_RESPONSE_READY = "Response Ready"
    STATUS_FORWARDED = "Forwarded to Supplier"
    STATUS_RESOLVED = "Resolved"
    STATUS_CANCELLED = "Cancelled"

    MESSAGE_SUPPLIER_QUESTION = "Supplier Question"
    MESSAGE_ENGINEERING_RESPONSE = "Engineering Response"
    MESSAGE_PURCHASING_NOTE = "Purchasing Note"
    MESSAGE_SUPPLIER_FOLLOW_UP = "Supplier Follow-up"
    MESSAGE_SYSTEM = "System"

    # ============================================================
    # READ
    # ============================================================

    @classmethod
    def get_clarification(
        cls,
        clarification_id,
    ):
        if not clarification_id:
            return None

        return ClarificationRepository.get_clarification_by_id(
            clarification_id
        )

    @classmethod
    def get_material_request_clarifications(
        cls,
        material_request_id,
        *,
        status: str | None = None,
    ) -> list[dict]:
        if not material_request_id:
            return []

        return ClarificationRepository.get_by_material_request(
            material_request_id,
            status=status,
        )

    @classmethod
    def get_messages(
        cls,
        clarification_id,
    ) -> list[dict]:
        if not clarification_id:
            return []

        return ClarificationRepository.get_messages(
            clarification_id
        )

    @classmethod
    def get_message_attachments(
        cls,
        clarification_message_id,
    ) -> list[dict]:
        if not clarification_message_id:
            return []

        return ClarificationRepository.get_message_attachments(
            clarification_message_id
        )

    # ============================================================
    # RECORD SUPPLIER CLARIFICATION
    # ============================================================

    @classmethod
    def record_supplier_clarification(
        cls,
        material_request_id,
        subject: str,
        supplier_question: str,
        project_engineer_user_id,
        current_user: dict,
        *,
        supplier_name: str | None = None,
        supplier_reference: str | None = None,
    ) -> str:
        cls._require_permission(
            current_user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        )

        user_id = cls._require_user_id(current_user)

        subject = cls._require_text(
            subject,
            "Clarification subject is required.",
        )

        supplier_question = cls._require_text(
            supplier_question,
            "Supplier question is required.",
        )

        if not material_request_id:
            raise ValueError(
                "Material Request ID is required."
            )

        if not project_engineer_user_id:
            raise ValueError(
                "Project Engineer is required."
            )

        project_engineer = OrganizationService.get_user(
            project_engineer_user_id
        )

        if (
            not project_engineer
            or not project_engineer.get("is_active")
        ):
            raise ValueError(
                "Selected Project Engineer is invalid or inactive."
            )

        conn = get_connection()
        cur = conn.cursor()

        try:
            material_request = cls._get_material_request_for_update(
                material_request_id,
                cursor=cur,
            )

            if not material_request:
                raise ValueError(
                    "Material Request was not found."
                )

            if material_request["status"] == "Archived":
                raise ValueError(
                    "Supplier clarifications cannot be created "
                    "for an archived Material Request."
                )

            clarification_id = (
                ClarificationRepository.create_clarification(
                    material_request_id=material_request_id,
                    subject=subject,
                    supplier_name=cls._clean_optional_text(
                        supplier_name
                    ),
                    supplier_reference=cls._clean_optional_text(
                        supplier_reference
                    ),
                    status=cls.STATUS_AWAITING_ENGINEERING,
                    assigned_to=project_engineer_user_id,
                    created_by=user_id,
                    cursor=cur,
                )
            )

            ClarificationRepository.create_message(
                clarification_id=clarification_id,
                message_type=cls.MESSAGE_SUPPLIER_QUESTION,
                message_text=supplier_question,
                sent_by=user_id,
                cursor=cur,
            )

            NotificationService.create_notification(
                recipient_user_id=project_engineer_user_id,
                notification_type=(
                    NotificationService.CLARIFICATION_REQUESTED
                ),
                title="Supplier Clarification Required",
                message=(
                    f"{material_request['mr_number']} requires "
                    f"your technical clarification: {subject}"
                ),
                entity_type="clarification",
                entity_id=clarification_id,
                created_by=user_id,
                cursor=cur,
            )

            cls._log_activity(
                cursor=cur,
                user_id=user_id,
                action="CLARIFICATION_CREATE",
                record_id=material_request_id,
                details=(
                    f"Recorded supplier clarification for "
                    f"{material_request['mr_number']}: {subject}"
                ),
            )

            conn.commit()

            return clarification_id

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # ENGINEERING RESPONSE
    # ============================================================

    @classmethod
    def submit_engineering_response(
        cls,
        clarification_id,
        response_text: str,
        current_user: dict,
    ) -> str:
        cls._require_permission(
        current_user,
            (
                "material_requests."
                "clarifications.reply"
            ),
        )

        user_id = cls._require_user_id(current_user)

        response_text = cls._require_text(
            response_text,
            "Engineering response is required.",
        )

        conn = get_connection()
        cur = conn.cursor()

        try:
            clarification = (
                ClarificationRepository.get_clarification_by_id(
                    clarification_id,
                    cursor=cur,
                )
            )

            if not clarification:
                raise ValueError(
                    "Clarification was not found."
                )

            if clarification["status"] != cls.STATUS_AWAITING_ENGINEERING:
                raise ValueError(
                    "This clarification is not awaiting "
                    "an Engineering response."
                )

            if clarification["assigned_to"] != str(user_id):
                raise PermissionError(
                    "This clarification is assigned to another user."
                )

            message_id = ClarificationRepository.create_message(
                clarification_id=clarification_id,
                message_type=cls.MESSAGE_ENGINEERING_RESPONSE,
                message_text=response_text,
                sent_by=user_id,
                cursor=cur,
            )

            ClarificationRepository.update_status(
                clarification_id,
                cls.STATUS_RESPONSE_READY,
                cursor=cur,
            )

            NotificationService.create_notification(
                recipient_user_id=clarification["created_by"],
                notification_type=(
                    NotificationService.CLARIFICATION_RESPONSE_RECEIVED
                ),
                title="Engineering Clarification Response Received",
                message=(
                    f"A technical response is ready for "
                    f"{clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
                entity_type="clarification",
                entity_id=clarification_id,
                created_by=user_id,
                cursor=cur,
            )

            cls._log_activity(
                cursor=cur,
                user_id=user_id,
                action="CLARIFICATION_RESPONSE",
                record_id=clarification["material_request_id"],
                details=(
                    f"Submitted Engineering response for "
                    f"{clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
            )

            conn.commit()

            return message_id

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # MARK FORWARDED TO SUPPLIER
    # ============================================================

    @classmethod
    def mark_forwarded_to_supplier(
        cls,
        clarification_id,
        current_user: dict,
        *,
        note: str | None = None,
    ) -> bool:
        cls._require_permission(
            current_user,
            "material_requests.clarifications.forward",
        )

        user_id = cls._require_user_id(current_user)

        conn = get_connection()
        cur = conn.cursor()

        try:
            clarification = (
                ClarificationRepository.get_clarification_by_id(
                    clarification_id,
                    cursor=cur,
                )
            )

            if not clarification:
                raise ValueError(
                    "Clarification was not found."
                )

            if clarification["status"] != cls.STATUS_RESPONSE_READY:
                raise ValueError(
                    "Only a clarification with a ready response "
                    "can be marked as forwarded to the supplier."
                )

            clean_note = cls._clean_optional_text(note)

            if clean_note:
                ClarificationRepository.create_message(
                    clarification_id=clarification_id,
                    message_type=cls.MESSAGE_PURCHASING_NOTE,
                    message_text=clean_note,
                    sent_by=user_id,
                    cursor=cur,
                )

            ClarificationRepository.update_status(
                clarification_id,
                cls.STATUS_FORWARDED,
                cursor=cur,
            )

            cls._log_activity(
                cursor=cur,
                user_id=user_id,
                action="CLARIFICATION_FORWARDED",
                record_id=clarification["material_request_id"],
                details=(
                    f"Marked clarification as forwarded to supplier "
                    f"for {clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
            )

            conn.commit()

            return True

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # SUPPLIER FOLLOW-UP
    # ============================================================

    @classmethod
    def record_supplier_follow_up(
        cls,
        clarification_id,
        follow_up_text: str,
        current_user: dict,
    ) -> str:
        cls._require_permission(
            current_user,
            (
                "material_requests."
            "clarifications.record_supplier"
            ),
        )

        user_id = cls._require_user_id(current_user)

        follow_up_text = cls._require_text(
            follow_up_text,
            "Supplier follow-up question is required.",
        )

        conn = get_connection()
        cur = conn.cursor()

        try:
            clarification = (
                ClarificationRepository.get_clarification_by_id(
                    clarification_id,
                    cursor=cur,
                )
            )

            if not clarification:
                raise ValueError(
                    "Clarification was not found."
                )

            if clarification["status"] != cls.STATUS_FORWARDED:
                raise ValueError(
                    "A supplier follow-up can only be recorded "
                    "after the previous response was forwarded."
                )

            if not clarification["assigned_to"]:
                raise ValueError(
                    "The clarification has no assigned Project Engineer."
                )

            message_id = ClarificationRepository.create_message(
                clarification_id=clarification_id,
                message_type=cls.MESSAGE_SUPPLIER_FOLLOW_UP,
                message_text=follow_up_text,
                sent_by=user_id,
                cursor=cur,
            )

            ClarificationRepository.update_status(
                clarification_id,
                cls.STATUS_AWAITING_ENGINEERING,
                cursor=cur,
            )

            NotificationService.create_notification(
                recipient_user_id=clarification["assigned_to"],
                notification_type=(
                    NotificationService.CLARIFICATION_REQUESTED
                ),
                title="Supplier Follow-up Clarification Required",
                message=(
                    f"A supplier follow-up requires your response for "
                    f"{clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
                entity_type="clarification",
                entity_id=clarification_id,
                created_by=user_id,
                cursor=cur,
            )

            cls._log_activity(
                cursor=cur,
                user_id=user_id,
                action="CLARIFICATION_FOLLOW_UP",
                record_id=clarification["material_request_id"],
                details=(
                    f"Recorded supplier follow-up for "
                    f"{clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
            )

            conn.commit()

            return message_id

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # RESOLVE
    # ============================================================

    @classmethod
    def resolve_clarification(
        cls,
        clarification_id,
        current_user: dict,
    ) -> bool:
        cls._require_permission(
            current_user,
            "material_requests.clarifications.resolve",
        )

        user_id = cls._require_user_id(current_user)

        conn = get_connection()
        cur = conn.cursor()

        try:
            clarification = (
                ClarificationRepository.get_clarification_by_id(
                    clarification_id,
                    cursor=cur,
                )
            )

            if not clarification:
                raise ValueError(
                    "Clarification was not found."
                )

            if clarification["status"] != cls.STATUS_FORWARDED:
                raise ValueError(
                    "Only a clarification forwarded to the supplier "
                    "can be resolved."
                )

            ClarificationRepository.resolve(
                clarification_id,
                user_id,
                cursor=cur,
            )

            cls._log_activity(
                cursor=cur,
                user_id=user_id,
                action="CLARIFICATION_RESOLVE",
                record_id=clarification["material_request_id"],
                details=(
                    f"Resolved supplier clarification for "
                    f"{clarification['mr_number']}: "
                    f"{clarification['subject']}"
                ),
            )

            conn.commit()

            return True

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @classmethod
    def _get_material_request_for_update(
        cls,
        material_request_id,
        *,
        cursor,
    ):
        cursor.execute(
            """
            SELECT
                id,
                mr_number,
                status,
                created_by
            FROM quotation.material_requests
            WHERE id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": str(row[0]),
            "mr_number": row[1],
            "status": row[2],
            "created_by": (
                str(row[3])
                if row[3]
                else None
            ),
        }

    @staticmethod
    def _log_activity(
        *,
        cursor,
        user_id,
        action: str,
        record_id,
        details: str,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO core.activity_logs (
                user_id,
                action,
                module,
                record_id,
                details
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                action,
                "Quotation Monitoring",
                record_id,
                details,
            ),
        )

    @staticmethod
    def _require_user_id(
        user: dict | None,
    ):
        if not user or not user.get("id"):
            raise ValueError(
                "Authenticated user is required."
            )

        return user["id"]

    @staticmethod
    def _require_text(
        value,
        error_message: str,
    ) -> str:
        cleaned = str(value or "").strip()

        if not cleaned:
            raise ValueError(error_message)

        return cleaned

    @staticmethod
    def _clean_optional_text(value):
        if value is None:
            return None

        cleaned = str(value).strip()

        return cleaned or None

    @staticmethod
    def _require_permission(
        user: dict | None,
        permission_name: str,
    ) -> None:
        if not PermissionService.has_permission(
            user,
            permission_name,
        ):
            raise PermissionError(
                f"Permission required: {permission_name}"
            )