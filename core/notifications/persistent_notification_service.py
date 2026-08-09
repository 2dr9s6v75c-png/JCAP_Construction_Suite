"""
JCAP Construction Suite
Persistent Notification Service

Centralized service for database-backed application notifications.

Responsibilities:
- Determine notification recipients
- Standardize notification types
- Standardize notification titles and messages
- Create persistent records through NotificationRepository
- Support existing workflow transactions through an optional cursor

Popup dialogs remain the responsibility of NotificationService.
"""

from core.database.repositories.notification_repository import (
    NotificationRepository,
)
from core.organization.organization_service import (
    OrganizationService,
)


class PersistentNotificationService:
    """
    Central service for persistent application notifications.

    Workflow services and process classes should call this service
    instead of creating notification records directly.
    """

    # ============================================================
    # ROLE NAMES
    # ============================================================

    PURCHASING_MANAGER_ROLE = "Purchasing Manager"

    # ============================================================
    # NOTIFICATION TYPES
    # ============================================================

    MATERIAL_REQUEST_CREATED = "MATERIAL_REQUEST_CREATED"
    MATERIAL_REQUEST_ASSIGNED = "MATERIAL_REQUEST_ASSIGNED"
    MATERIAL_REQUEST_REASSIGNED = "MATERIAL_REQUEST_REASSIGNED"

    REQUESTER_MATERIAL_REQUEST_ASSIGNED = (
        "REQUESTER_MATERIAL_REQUEST_ASSIGNED"
    )
    REQUESTER_MATERIAL_REQUEST_REASSIGNED = (
        "REQUESTER_MATERIAL_REQUEST_REASSIGNED"
    )

    SUPPLIER_CLARIFICATION_RECORDED = (
        "SUPPLIER_CLARIFICATION_RECORDED"
    )
    ENGINEERING_RESPONSE_SUBMITTED = (
        "ENGINEERING_RESPONSE_SUBMITTED"
    )
    SUPPLIER_FOLLOW_UP_RECORDED = (
        "SUPPLIER_FOLLOW_UP_RECORDED"
    )
    SUPPLIER_CLARIFICATION_RESOLVED = (
        "SUPPLIER_CLARIFICATION_RESOLVED"
    )

    SUPPLIER_QUOTATION_CREATED = (
        "SUPPLIER_QUOTATION_CREATED"
    )
    SUPPLIER_QUOTATION_FILES_UPLOADED = (
        "SUPPLIER_QUOTATION_FILES_UPLOADED"
    )

    # ============================================================
    # ENTITY TYPES
    # ============================================================

    ENTITY_MATERIAL_REQUEST = "MATERIAL_REQUEST"
    ENTITY_SUPPLIER_CLARIFICATION = (
        "SUPPLIER_CLARIFICATION"
    )

    # ============================================================
    # MATERIAL REQUEST CREATED
    # ============================================================

    @classmethod
    def notify_material_request_created(
        cls,
        *,
        material_request_id,
        mr_number: str,
        created_by=None,
        cursor=None,
    ) -> int:
        """
        Notify all active Purchasing Managers that a new Material
        Request has been created and is awaiting assignment.

        Returns the number of notification records created.
        """
        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )

        purchasing_managers = (
            OrganizationService.get_active_users_by_role(
                cls.PURCHASING_MANAGER_ROLE
            )
        )

        created_count = 0
        notified_user_ids = set()

        for manager in purchasing_managers:
            recipient_user_id = manager.get("id")

            if not recipient_user_id:
                continue

            recipient_key = str(recipient_user_id)

            if recipient_key in notified_user_ids:
                continue

            cls._create(
                recipient_user_id=recipient_user_id,
                notification_type=(
                    cls.MATERIAL_REQUEST_CREATED
                ),
                title="New Material Request",
                message=(
                    f"Material Request {mr_number} has been "
                    f"created and is awaiting assignment."
                ),
                entity_type=cls.ENTITY_MATERIAL_REQUEST,
                entity_id=material_request_id,
                created_by=created_by,
                cursor=cursor,
            )

            notified_user_ids.add(recipient_key)
            created_count += 1

        return created_count

    # ============================================================
    # MATERIAL REQUEST ASSIGNED
    # ============================================================

    @classmethod
    def notify_material_request_assigned(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        assigned_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Purchasing Officer assigned to a Material Request.
        """
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.MATERIAL_REQUEST_ASSIGNED
            ),
            title="Material Request Assigned",
            message=(
                f"Material Request {mr_number} has been "
                f"assigned to you for processing."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=assigned_by,
            cursor=cursor,
        )

    # ============================================================
    # MATERIAL REQUEST REASSIGNED
    # ============================================================

    @classmethod
    def notify_material_request_reassigned(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        reassigned_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the new Purchasing Officer when a Material Request
        has been reassigned.
        """
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.MATERIAL_REQUEST_REASSIGNED
            ),
            title="Material Request Reassigned",
            message=(
                f"Material Request {mr_number} has been "
                f"reassigned to you for processing."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=reassigned_by,
            cursor=cursor,
        )

    # ============================================================
    # REQUESTER MATERIAL REQUEST ASSIGNED
    # ============================================================

    @classmethod
    def notify_requester_material_request_assigned(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        purchasing_officer_name: str,
        assigned_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Engineering requester that the Material Request
        has been assigned to a Purchasing Officer.
        """
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        purchasing_officer_name = cls._require_text(
            purchasing_officer_name,
            "Purchasing Officer name is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.REQUESTER_MATERIAL_REQUEST_ASSIGNED
            ),
            title="Material Request Assigned",
            message=(
                f"Your Material Request {mr_number} has been "
                f"assigned to {purchasing_officer_name} "
                f"for quotation processing. You will receive "
                f"updates if supplier clarifications require "
                f"your response."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=assigned_by,
            cursor=cursor,
        )

    # ============================================================
    # REQUESTER MATERIAL REQUEST REASSIGNED
    # ============================================================

    @classmethod
    def notify_requester_material_request_reassigned(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        purchasing_officer_name: str,
        reassigned_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Engineering requester that the Material Request
        has been reassigned to another Purchasing Officer.
        """
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        purchasing_officer_name = cls._require_text(
            purchasing_officer_name,
            "Purchasing Officer name is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.REQUESTER_MATERIAL_REQUEST_REASSIGNED
            ),
            title="Material Request Reassigned",
            message=(
                f"Your Material Request {mr_number} has been "
                f"reassigned to {purchasing_officer_name} "
                f"for quotation processing."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=reassigned_by,
            cursor=cursor,
        )

    # ============================================================
    # SUPPLIER CLARIFICATION RECORDED
    # ============================================================

    @classmethod
    def notify_supplier_clarification_recorded(
        cls,
        *,
        recipient_user_id,
        clarification_id,
        mr_number: str,
        subject: str,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Engineering requester that a supplier
        clarification requires a response.
        """
        if not recipient_user_id:
            return None

        clarification_id = cls._require_id(
            clarification_id,
            "Clarification ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        subject = cls._require_text(
            subject,
            "Clarification subject is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.SUPPLIER_CLARIFICATION_RECORDED
            ),
            title="Supplier Clarification Recorded",
            message=(
                f"A supplier clarification for Material Request "
                f"{mr_number} requires your response: {subject}"
            ),
            entity_type=(
                cls.ENTITY_SUPPLIER_CLARIFICATION
            ),
            entity_id=clarification_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # ENGINEERING RESPONSE SUBMITTED
    # ============================================================

    @classmethod
    def notify_engineering_response_submitted(
        cls,
        *,
        recipient_user_id,
        clarification_id,
        mr_number: str,
        subject: str,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the assigned Purchasing Officer that the Engineering
        response is ready to forward to the supplier.
        """
        if not recipient_user_id:
            return None

        clarification_id = cls._require_id(
            clarification_id,
            "Clarification ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        subject = cls._require_text(
            subject,
            "Clarification subject is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.ENGINEERING_RESPONSE_SUBMITTED
            ),
            title="Engineering Response Submitted",
            message=(
                f"An Engineering response for Material Request "
                f"{mr_number} is ready to forward to the supplier: "
                f"{subject}"
            ),
            entity_type=(
                cls.ENTITY_SUPPLIER_CLARIFICATION
            ),
            entity_id=clarification_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # SUPPLIER FOLLOW-UP RECORDED
    # ============================================================

    @classmethod
    def notify_supplier_follow_up_recorded(
        cls,
        *,
        recipient_user_id,
        clarification_id,
        mr_number: str,
        subject: str,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Engineering requester that the supplier submitted
        a follow-up question requiring another response.
        """
        if not recipient_user_id:
            return None

        clarification_id = cls._require_id(
            clarification_id,
            "Clarification ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        subject = cls._require_text(
            subject,
            "Clarification subject is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.SUPPLIER_FOLLOW_UP_RECORDED
            ),
            title="Supplier Follow-up Recorded",
            message=(
                f"A supplier follow-up for Material Request "
                f"{mr_number} requires another Engineering response: "
                f"{subject}"
            ),
            entity_type=(
                cls.ENTITY_SUPPLIER_CLARIFICATION
            ),
            entity_id=clarification_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # SUPPLIER CLARIFICATION RESOLVED
    # ============================================================

    @classmethod
    def notify_supplier_clarification_resolved(
        cls,
        *,
        recipient_user_id,
        clarification_id,
        mr_number: str,
        subject: str,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """
        Notify the Engineering requester that a supplier
        clarification has been resolved.
        """
        if not recipient_user_id:
            return None

        clarification_id = cls._require_id(
            clarification_id,
            "Clarification ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        subject = cls._require_text(
            subject,
            "Clarification subject is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.SUPPLIER_CLARIFICATION_RESOLVED
            ),
            title="Supplier Clarification Resolved",
            message=(
                f"The supplier clarification for Material Request "
                f"{mr_number} has been resolved: {subject}"
            ),
            entity_type=(
                cls.ENTITY_SUPPLIER_CLARIFICATION
            ),
            entity_id=clarification_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # SUPPLIER QUOTATION CREATED
    # ============================================================

    @classmethod
    def notify_supplier_quotation_created(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        supplier_name: str,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """Notify the Engineering requester of a new quotation."""
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        supplier_name = cls._require_text(
            supplier_name,
            "Supplier name is required.",
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=cls.SUPPLIER_QUOTATION_CREATED,
            title="Supplier Quotation Created",
            message=(
                f"A Supplier Quotation from {supplier_name} "
                f"has been recorded for Material Request "
                f"{mr_number}."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # SUPPLIER QUOTATION FILES UPLOADED
    # ============================================================

    @classmethod
    def notify_supplier_quotation_files_uploaded(
        cls,
        *,
        recipient_user_id,
        material_request_id,
        mr_number: str,
        supplier_name: str,
        file_count: int,
        created_by=None,
        cursor=None,
    ) -> str | None:
        """Notify the Engineering requester of new quotation files."""
        if not recipient_user_id:
            return None

        material_request_id = cls._require_id(
            material_request_id,
            "Material Request ID is required.",
        )
        mr_number = cls._require_text(
            mr_number,
            "Material Request number is required.",
        )
        supplier_name = cls._require_text(
            supplier_name,
            "Supplier name is required.",
        )

        try:
            normalized_file_count = int(file_count)
        except (TypeError, ValueError):
            normalized_file_count = 0

        if normalized_file_count < 1:
            raise ValueError(
                "Supplier Quotation file count must be at least 1."
            )

        file_word = (
            "file" if normalized_file_count == 1 else "files"
        )

        return cls._create(
            recipient_user_id=recipient_user_id,
            notification_type=(
                cls.SUPPLIER_QUOTATION_FILES_UPLOADED
            ),
            title="Supplier Quotation Files Uploaded",
            message=(
                f"{normalized_file_count} quotation {file_word} "
                f"from {supplier_name} has been uploaded for "
                f"Material Request {mr_number}."
            ),
            entity_type=cls.ENTITY_MATERIAL_REQUEST,
            entity_id=material_request_id,
            created_by=created_by,
            cursor=cursor,
        )

    # ============================================================
    # INTERNAL CREATE HELPER
    # ============================================================

    @classmethod
    def _create(
        cls,
        *,
        recipient_user_id,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str,
        entity_id,
        created_by=None,
        cursor=None,
    ) -> str:
        recipient_user_id = cls._require_id(
            recipient_user_id,
            "Notification recipient is required.",
        )
        notification_type = cls._require_text(
            notification_type,
            "Notification type is required.",
        )
        title = cls._require_text(
            title,
            "Notification title is required.",
        )
        message = cls._require_text(
            message,
            "Notification message is required.",
        )
        entity_type = cls._require_text(
            entity_type,
            "Notification entity type is required.",
        )
        entity_id = cls._require_id(
            entity_id,
            "Notification entity ID is required.",
        )

        return NotificationRepository.create(
            recipient_user_id,
            notification_type,
            title,
            message,
            entity_type,
            entity_id,
            created_by,
            cursor=cursor,
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _require_id(
        value,
        error_message: str,
    ):
        if value is None:
            raise ValueError(error_message)

        cleaned = str(value).strip()

        if not cleaned:
            raise ValueError(error_message)

        return value

    @staticmethod
    def _require_text(
        value,
        error_message: str,
    ) -> str:
        cleaned = str(value or "").strip()

        if not cleaned:
            raise ValueError(error_message)

        return cleaned