from __future__ import annotations

import re
from typing import Any

from core.database.transaction_manager import TransactionManager
from core.logging.activity_logger import ActivityLogger
from core.security.permissions import PermissionService
from modules.master_data.clients.client_repository import ClientRepository


class ClientService:
    """
    Business service for Client Master records.

    Responsibilities:
    - Enforce Client Master permissions.
    - Validate and normalize user input.
    - Generate sequential client codes.
    - Coordinate database transactions.
    - Write activity logs in the same transaction.
    """

    CLIENT_CODE_PREFIX = "CLI"
    CLIENT_CODE_DIGITS = 6

    # Transaction-scoped PostgreSQL advisory lock used only while
    # generating the next Client Master code.
    CLIENT_CODE_LOCK_KEY = 741001

    EMAIL_PATTERN = re.compile(
        r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )

    # ============================================================
    # READ OPERATIONS
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        client_id: Any,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_clients,
            "You do not have permission to view Client Master records.",
        )

        if not client_id:
            raise ValueError("A client ID is required.")

        return ClientRepository.get_by_id(client_id)

    @classmethod
    def get_by_code(
        cls,
        client_code: str,
        *,
        current_user: dict | None,
    ) -> dict | None:
        cls._require_permission(
            current_user,
            PermissionService.can_view_clients,
            "You do not have permission to view Client Master records.",
        )

        clean_code = cls._clean_required_text(
            client_code,
            "Client code",
        )

        return ClientRepository.get_by_code(clean_code)

    @classmethod
    def get_all(
        cls,
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_clients,
            "You do not have permission to view Client Master records.",
        )

        clean_status = cls._normalize_status_filter(status_filter)

        return ClientRepository.get_all(
            status_filter=clean_status,
        )

    @classmethod
    def get_active(
        cls,
        *,
        current_user: dict | None,
    ) -> list[dict]:
        return cls.get_all(
            status_filter="Active",
            current_user=current_user,
        )

    @classmethod
    def search(
        cls,
        search_text: str = "",
        status_filter: str = "Active",
        *,
        current_user: dict | None,
    ) -> list[dict]:
        cls._require_permission(
            current_user,
            PermissionService.can_view_clients,
            "You do not have permission to view Client Master records.",
        )

        return ClientRepository.search(
            search_text=str(search_text or "").strip(),
            status_filter=cls._normalize_status_filter(status_filter),
        )

    # ============================================================
    # CREATE
    # ============================================================

    @classmethod
    def create_client(
        cls,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_create_clients,
            "You do not have permission to create Client Master records.",
        )

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            if ClientRepository.name_exists(
                clean_data["client_name"],
                active_only=True,
                cursor=cursor,
            ):
                raise ValueError(
                    "An active client with the same name already exists."
                )

            # Prevent two concurrent users from generating the same code.
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (cls.CLIENT_CODE_LOCK_KEY,),
            )

            client_code = cls._generate_next_code(
                cursor=cursor,
            )

            client = ClientRepository.create(
                client_code=client_code,
                client_name=clean_data["client_name"],
                contact_person=clean_data["contact_person"],
                phone=clean_data["phone"],
                email=clean_data["email"],
                address=clean_data["address"],
                remarks=clean_data["remarks"],
                created_by=user_id,
                cursor=cursor,
            )

            if not client:
                raise RuntimeError(
                    "The Client Master record was not created."
                )

            ActivityLogger.log_create(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=client["id"],
                details=(
                    f"Created Client Master record "
                    f"{client['client_code']} - "
                    f"{client['client_name']}."
                ),
            )

            return client

    # ============================================================
    # UPDATE
    # ============================================================

    @classmethod
    def update_client(
        cls,
        client_id: Any,
        data: dict,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_edit_clients,
            "You do not have permission to edit Client Master records.",
        )

        if not client_id:
            raise ValueError("A client ID is required.")

        user_id = cls._get_user_id(current_user)
        clean_data = cls._validate_and_clean(data)

        with TransactionManager() as cursor:
            existing = ClientRepository.get_by_id(
                client_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Client Master record was not found."
                )

            if ClientRepository.name_exists(
                clean_data["client_name"],
                exclude_client_id=client_id,
                active_only=True,
                cursor=cursor,
            ):
                raise ValueError(
                    "An active client with the same name already exists."
                )

            updated = ClientRepository.update(
                client_id,
                client_name=clean_data["client_name"],
                contact_person=clean_data["contact_person"],
                phone=clean_data["phone"],
                email=clean_data["email"],
                address=clean_data["address"],
                remarks=clean_data["remarks"],
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Client Master record was not updated."
                )

            ActivityLogger.log_update(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Updated Client Master record "
                    f"{updated['client_code']} - "
                    f"{updated['client_name']}."
                ),
            )

            return updated

    # ============================================================
    # ARCHIVE / RESTORE
    # ============================================================

    @classmethod
    def deactivate_client(
        cls,
        client_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_archive_clients,
            "You do not have permission to deactivate Client Master records.",
        )

        if not client_id:
            raise ValueError("A client ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = ClientRepository.get_by_id(
                client_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Client Master record was not found."
                )

            if not existing["is_active"]:
                raise ValueError(
                    "The selected client is already inactive."
                )

            updated = ClientRepository.deactivate(
                client_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Client Master record was not deactivated."
                )

            ActivityLogger.log_archive(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Deactivated Client Master record "
                    f"{updated['client_code']} - "
                    f"{updated['client_name']}."
                ),
            )

            return updated

    @classmethod
    def restore_client(
        cls,
        client_id: Any,
        *,
        current_user: dict | None,
    ) -> dict:
        cls._require_permission(
            current_user,
            PermissionService.can_restore_clients,
            "You do not have permission to restore Client Master records.",
        )

        if not client_id:
            raise ValueError("A client ID is required.")

        user_id = cls._get_user_id(current_user)

        with TransactionManager() as cursor:
            existing = ClientRepository.get_by_id(
                client_id,
                cursor=cursor,
            )

            if not existing:
                raise ValueError(
                    "The selected Client Master record was not found."
                )

            if existing["is_active"]:
                raise ValueError(
                    "The selected client is already active."
                )

            # The database allows the same name for inactive clients,
            # but restoration must not create two active duplicates.
            if ClientRepository.name_exists(
                existing["client_name"],
                exclude_client_id=client_id,
                active_only=True,
                cursor=cursor,
            ):
                raise ValueError(
                    "This client cannot be restored because another "
                    "active client already uses the same name."
                )

            updated = ClientRepository.activate(
                client_id,
                updated_by=user_id,
                cursor=cursor,
            )

            if not updated:
                raise RuntimeError(
                    "The Client Master record was not restored."
                )

            ActivityLogger.log_restore(
                cursor,
                user_id=user_id,
                module=ActivityLogger.MODULE_MASTER_DATA,
                record_id=updated["id"],
                details=(
                    f"Restored Client Master record "
                    f"{updated['client_code']} - "
                    f"{updated['client_name']}."
                ),
            )

            return updated

    # Compatibility aliases for UI naming.
    archive_client = deactivate_client
    activate_client = restore_client

    # ============================================================
    # CODE GENERATION
    # ============================================================

    @classmethod
    def _generate_next_code(
        cls,
        *,
        cursor,
    ) -> str:
        highest_number = ClientRepository.get_highest_code_number(
            cursor=cursor,
        )

        next_number = highest_number + 1

        while True:
            client_code = (
                f"{cls.CLIENT_CODE_PREFIX}-"
                f"{next_number:0{cls.CLIENT_CODE_DIGITS}d}"
            )

            if not ClientRepository.code_exists(
                client_code,
                cursor=cursor,
            ):
                return client_code

            next_number += 1

    # ============================================================
    # VALIDATION
    # ============================================================

    @classmethod
    def _validate_and_clean(
        cls,
        data: dict | None,
    ) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Client data must be supplied as a dictionary.")

        client_name = cls._clean_required_text(
            data.get("client_name"),
            "Client name",
            maximum_length=255,
        )

        contact_person = cls._clean_optional_text(
            data.get("contact_person"),
            maximum_length=255,
        )

        phone = cls._clean_optional_text(
            data.get("phone"),
            maximum_length=50,
        )

        email = cls._clean_optional_text(
            data.get("email"),
            maximum_length=255,
        )

        address = cls._clean_optional_text(
            data.get("address"),
        )

        remarks = cls._clean_optional_text(
            data.get("remarks"),
        )

        if email and not cls.EMAIL_PATTERN.fullmatch(email):
            raise ValueError(
                "Please enter a valid email address."
            )

        return {
            "client_name": client_name,
            "contact_person": contact_person,
            "phone": phone,
            "email": email,
            "address": address,
            "remarks": remarks,
        }

    @staticmethod
    def _clean_required_text(
        value: Any,
        field_name: str,
        *,
        maximum_length: int | None = None,
    ) -> str:
        clean_value = str(value or "").strip()

        if not clean_value:
            raise ValueError(f"{field_name} is required.")

        if maximum_length and len(clean_value) > maximum_length:
            raise ValueError(
                f"{field_name} must not exceed "
                f"{maximum_length} characters."
            )

        return clean_value

    @staticmethod
    def _clean_optional_text(
        value: Any,
        *,
        maximum_length: int | None = None,
    ) -> str | None:
        clean_value = str(value or "").strip()

        if not clean_value:
            return None

        if maximum_length and len(clean_value) > maximum_length:
            raise ValueError(
                f"Value must not exceed {maximum_length} characters."
            )

        return clean_value

    @staticmethod
    def _normalize_status_filter(
        status_filter: str,
    ) -> str:
        normalized = str(
            status_filter or "Active"
        ).strip().lower()

        if normalized == "all":
            return "All"

        if normalized == "inactive":
            return "Inactive"

        return "Active"

    # ============================================================
    # SECURITY HELPERS
    # ============================================================

    @staticmethod
    def _get_user_id(
        current_user: dict | None,
    ) -> Any:
        if not current_user:
            raise PermissionError(
                "An authenticated user is required."
            )

        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
        )

        if not user_id:
            raise PermissionError(
                "The authenticated user does not contain a user ID."
            )

        return user_id

    @staticmethod
    def _require_permission(
        current_user: dict | None,
        permission_check,
        error_message: str,
    ) -> None:
        if not current_user:
            raise PermissionError(
                "An authenticated user is required."
            )

        if not permission_check(current_user):
            raise PermissionError(error_message)