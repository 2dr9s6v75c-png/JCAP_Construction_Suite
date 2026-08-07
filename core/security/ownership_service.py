"""
JCAP Construction Suite
Ownership Service

Centralizes record-specific ownership rules on top of RBAC.
"""

from __future__ import annotations

from typing import Any

from core.security.permissions import PermissionService


class OwnershipService:
    """Centralized Phase 1 record-ownership rules."""

    @staticmethod
    def _normalize_id(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def get_user_id(cls, user: dict[str, Any] | None) -> str:
        if not isinstance(user, dict):
            return ""
        return cls._normalize_id(user.get("id"))

    @classmethod
    def get_assigned_user_id(
        cls,
        material_request: dict[str, Any] | None,
    ) -> str:
        if not isinstance(material_request, dict):
            return ""
        return cls._normalize_id(
            material_request.get("assigned_to_id")
            or material_request.get("assigned_to")
        )

    @classmethod
    def is_purchasing_manager(
        cls,
        user: dict[str, Any] | None,
    ) -> bool:
        return PermissionService.has_role(
            user,
            PermissionService.PURCHASING_MANAGER,
        )

    @classmethod
    def is_purchasing_officer(
        cls,
        user: dict[str, Any] | None,
    ) -> bool:
        return PermissionService.has_role(
            user,
            PermissionService.PURCHASING_OFFICER,
        )

    @classmethod
    def is_administrator(
        cls,
        user: dict[str, Any] | None,
    ) -> bool:
        return PermissionService.is_administrator(user)

    @classmethod
    def is_assigned_user(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        user_id = cls.get_user_id(user)
        assigned_user_id = cls.get_assigned_user_id(material_request)
        return bool(
            user_id
            and assigned_user_id
            and user_id == assigned_user_id
        )

    @classmethod
    def is_material_request_requester(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(material_request, dict):
            return False

        requester_user_id = cls._normalize_id(
            material_request.get("requested_by_user_id")
        )

        return bool(
            requester_user_id
            and requester_user_id == cls.get_user_id(user)
        )

    @classmethod
    def is_operational_owner(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        if not cls.is_assigned_user(user, material_request):
            return False

        return (
            cls.is_purchasing_officer(user)
            or cls.is_administrator(user)
        )

    @classmethod
    def can_view_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return PermissionService.can_view_material_request(user)

    @classmethod
    def can_edit_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_edit_material_request(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_process_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_process_material_request(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_assign_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return PermissionService.can_assign_material_request(user)

    @classmethod
    def can_reassign_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return PermissionService.can_reassign_material_request(user)

    @classmethod
    def can_archive_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return (
            PermissionService.can_archive_material_request(user)
            and (
                cls.is_purchasing_manager(user)
                or cls.is_administrator(user)
            )
        )

    @classmethod
    def can_restore_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return (
            PermissionService.can_restore_material_request(user)
            and (
                cls.is_purchasing_manager(user)
                or cls.is_administrator(user)
            )
        )

    @classmethod
    def can_force_unlock_material_request(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return (
            cls.is_administrator(user)
            and PermissionService.can_force_unlock_material_request(user)
        )

    @classmethod
    def can_manage_supplier_quotations(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_manage_supplier_quotations(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_view_material_request_documents(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None = None,
    ) -> bool:
        return (
            PermissionService.can_view_material_request_documents(user)
            or PermissionService.can_view_material_request(user)
        )

    @classmethod
    def can_upload_material_request_documents(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        """
        Allow attachment uploads to:
        - the assigned Purchasing Officer who owns MR processing; or
        - the Engineering requester who created the Material Request.

        RBAC still applies, so the account must also carry the document
        upload permission.
        """
        has_upload_permission = (
            PermissionService.can_upload_material_request_documents(
                user
            )
        )

        if not has_upload_permission:
            return False

        return (
            cls.is_operational_owner(
                user,
                material_request,
            )
            or cls.is_material_request_requester(
                user,
                material_request,
            )
        )

    @classmethod
    def can_delete_material_request_documents(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        """
        Compatibility helper for callers that only have MR-level context.

        Assigned Purchasing Officers may delete attachments on their assigned
        Material Request. Engineering deletion requires attachment-level
        ownership, so callers should prefer can_delete_attachment().
        """
        return cls.is_operational_owner(
            user,
            material_request,
        )

    @classmethod
    def can_delete_attachment(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
        attachment: dict[str, Any] | None,
    ) -> bool:
        """
        Phase 1 attachment delete ownership rule.

        - Administrator: allowed.
        - Assigned Purchasing Officer: may delete any attachment on the MR.
        - Engineering requester: may delete only attachments they uploaded.
        - Everyone else: denied.
        """
        if cls.is_administrator(user):
            return True

        if cls.is_operational_owner(
            user,
            material_request,
        ):
            return True

        if not (
            cls.is_material_request_requester(
                user,
                material_request,
            )
            and isinstance(attachment, dict)
        ):
            return False

        uploaded_by = cls._normalize_id(
            attachment.get("uploaded_by")
            or attachment.get("uploaded_by_user_id")
        )

        return bool(
            uploaded_by
            and uploaded_by == cls.get_user_id(user)
        )

    @classmethod
    def can_record_supplier_clarification(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_record_supplier_clarification(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_forward_clarification_to_supplier(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_forward_clarification_to_supplier(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_resolve_material_request_clarification(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        return (
            PermissionService.can_resolve_material_request_clarification(user)
            and cls.is_operational_owner(user, material_request)
        )

    @classmethod
    def can_reply_to_engineering_clarification(
        cls,
        user: dict[str, Any] | None,
        material_request: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(material_request, dict):
            return False

        return (
            PermissionService.can_reply_material_request_clarification(
                user
            )
            and cls.is_material_request_requester(
                user,
                material_request,
            )
        )