"""
JCAP Construction Suite
Supplier Quotation Service

Owns supplier-quotation validation, permission enforcement, status rules, and
single-record repository operations.

Transaction orchestration, file copying/removal, activity logging, and
cross-component coordination belong to the process layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from core.security.permissions import PermissionService
from core.services.base_service import BaseService
from modules.quotation.repositories.supplier_quotation_repository import (
    SupplierQuotationRepository,
)


DEFAULT_SUPPLIER_QUOTATION_STATUS = "Received"

SUPPLIER_QUOTATION_STATUSES = (
    "Received",
    "Under Review",
    "Clarification Required",
    "Accepted",
    "Rejected",
)

MAX_SUPPLIER_NAME_LENGTH = 200
MAX_QUOTATION_REFERENCE_LENGTH = 100
MAX_QUOTATION_REMARKS_LENGTH = 2000
MAX_FILENAME_LENGTH = 255
MAX_FOLDER_PATH_LENGTH = 1000


class SupplierQuotationService(BaseService):
    """Business service for supplier quotation records."""

    def __init__(
        self,
        repository: SupplierQuotationRepository | None = None,
    ) -> None:
        self._repository = repository or SupplierQuotationRepository()

    def get_by_id(
        self,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        return self._repository.get_supplier_quotation(
            quotation_id,
            cursor=cursor,
        )

    def require_by_id(
        self,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        return self.require_record(
            self.get_by_id(
                supplier_quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )

    def list_by_material_request(
        self,
        material_request_id: UUID | str,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        normalized_filter = self._validate_status_filter(status_filter)
        return self._repository.list_supplier_quotations_by_material_request(
            material_request_id,
            normalized_filter,
            cursor=cursor,
        )

    def list_all(
        self,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        normalized_filter = self._validate_status_filter(status_filter)
        return self._repository.list_supplier_quotations(
            normalized_filter,
            cursor=cursor,
        )

    def count_by_material_request(
        self,
        material_request_id: UUID | str,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> int:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        normalized_filter = self._validate_status_filter(status_filter)
        return self._repository.count_supplier_quotations(
            material_request_id,
            normalized_filter,
            cursor=cursor,
        )

    def get_latest(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.get_latest_supplier_quotation(
            material_request_id,
            cursor=cursor,
        )

    def get_statistics(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, int]:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        return self._repository.get_supplier_statistics(
            material_request_id,
            cursor=cursor,
        )

    def create(
        self,
        material_request_id: UUID | str,
        supplier_name: str,
        current_user: dict[str, Any],
        quotation_reference: str | None = None,
        quotation_date: date | datetime | str | None = None,
        remarks: str | None = None,
        status: str = DEFAULT_SUPPLIER_QUOTATION_STATUS,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        material_request_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        current_user = self.require_user(current_user)
        created_by = self.get_user_uuid(current_user)
        self._require_create_permission(current_user)

        created = self._repository.create_supplier_quotation(
            material_request_id=material_request_id,
            supplier_name=self._validate_supplier_name(supplier_name),
            quotation_reference=self._validate_quotation_reference(
                quotation_reference
            ),
            quotation_date=self._validate_quotation_date(quotation_date),
            remarks=self._validate_remarks(remarks),
            status=self._validate_status(status),
            created_by=created_by,
            cursor=cursor,
        )
        return self.require_record(created, "Supplier Quotation")

    def update(
        self,
        supplier_quotation_id: UUID | str,
        supplier_name: str,
        current_user: dict[str, Any],
        quotation_reference: str | None = None,
        quotation_date: date | datetime | str | None = None,
        remarks: str | None = None,
        status: str = DEFAULT_SUPPLIER_QUOTATION_STATUS,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        updated_by = self.get_user_uuid(current_user)
        self._require_edit_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        self._require_not_archived(existing)

        updated = self._repository.update_supplier_quotation(
            quotation_id,
            supplier_name=self._validate_supplier_name(supplier_name),
            quotation_reference=self._validate_quotation_reference(
                quotation_reference
            ),
            quotation_date=self._validate_quotation_date(quotation_date),
            remarks=self._validate_remarks(remarks),
            status=self._validate_status(status),
            updated_by=updated_by,
            cursor=cursor,
        )
        return self.require_record(updated, "Supplier Quotation")

    def update_status(
        self,
        supplier_quotation_id: UUID | str,
        status: str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        updated_by = self.get_user_uuid(current_user)
        self._require_edit_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        self._require_not_archived(existing)
        normalized_status = self._validate_status(status)
        self._validate_status_transition(
            existing.get("status"),
            normalized_status,
        )

        updated = self._repository.update_supplier_quotation_status(
            quotation_id,
            status=normalized_status,
            updated_by=updated_by,
            cursor=cursor,
        )
        return self.require_record(updated, "Supplier Quotation")

    def archive(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        updated_by = self.get_user_uuid(current_user)
        self._require_archive_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        if bool(existing.get("is_archived")):
            raise ValueError(
                "This Supplier Quotation is already archived."
            )

        archived = self._repository.archive_supplier_quotation(
            quotation_id,
            updated_by=updated_by,
            cursor=cursor,
        )
        return self.require_record(archived, "Supplier Quotation")

    def restore(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        updated_by = self.get_user_uuid(current_user)
        self._require_restore_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        if not bool(existing.get("is_archived")):
            raise ValueError(
                "Only archived Supplier Quotations can be restored."
            )

        restored = self._repository.restore_supplier_quotation(
            quotation_id,
            updated_by=updated_by,
            cursor=cursor,
        )
        return self.require_record(restored, "Supplier Quotation")

    def delete(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        self._require_delete_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        if not bool(existing.get("is_archived")):
            raise ValueError(
                "A Supplier Quotation must be archived before "
                "it can be permanently deleted."
            )

        affected_rows = self._repository.delete_supplier_quotation(
            quotation_id,
            cursor=cursor,
        )
        if affected_rows != 1:
            raise ValueError(
                "Supplier Quotation could not be deleted."
            )
        return existing

    def get_file_by_id(
        self,
        supplier_quotation_file_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        file_id = self.normalize_uuid_object(
            supplier_quotation_file_id,
            "Supplier Quotation File ID",
        )
        return self._repository.get_supplier_quotation_file(
            file_id,
            cursor=cursor,
        )

    def list_files(
        self,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        return self._repository.list_supplier_quotation_files(
            quotation_id,
            cursor=cursor,
        )

    def count_files(
        self,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        return self._repository.count_supplier_quotation_files(
            quotation_id,
            cursor=cursor,
        )

    def register_file(
        self,
        supplier_quotation_id: UUID | str,
        original_filename: str,
        stored_filename: str,
        folder_path: str,
        current_user: dict[str, Any],
        file_extension: str | None = None,
        file_size: int | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        quotation_id = self.normalize_uuid_object(
            supplier_quotation_id,
            "Supplier Quotation ID",
        )
        current_user = self.require_user(current_user)
        uploaded_by = self.get_user_uuid(current_user)
        self._require_edit_permission(current_user)

        quotation = self.require_record(
            self._repository.get_supplier_quotation(
                quotation_id,
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        self._require_not_archived(quotation)

        original_filename = self._validate_filename(
            original_filename,
            "Original filename",
        )
        stored_filename = self._validate_filename(
            stored_filename,
            "Stored filename",
        )
        folder_path = self._validate_folder_path(folder_path)
        file_extension = self._validate_file_extension(file_extension)
        file_size = self._validate_file_size(file_size)

        if self._repository.stored_filename_exists(
            quotation_id,
            stored_filename,
            cursor=cursor,
        ):
            raise ValueError(
                "The stored quotation filename already exists "
                "for this Supplier Quotation."
            )

        created = self._repository.create_supplier_quotation_file(
            supplier_quotation_id=quotation_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            folder_path=folder_path,
            file_extension=file_extension,
            file_size=file_size,
            uploaded_by=uploaded_by,
            cursor=cursor,
        )
        return self.require_record(
            created,
            "Supplier Quotation File",
        )

    def delete_file_metadata(
        self,
        supplier_quotation_file_id: UUID | str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        file_id = self.normalize_uuid_object(
            supplier_quotation_file_id,
            "Supplier Quotation File ID",
        )
        current_user = self.require_user(current_user)
        self._require_edit_permission(current_user)

        existing = self.require_record(
            self._repository.get_supplier_quotation_file(
                file_id,
                cursor=cursor,
            ),
            "Supplier Quotation File",
        )
        quotation = self.require_record(
            self._repository.get_supplier_quotation(
                existing["supplier_quotation_id"],
                cursor=cursor,
            ),
            "Supplier Quotation",
        )
        self._require_not_archived(quotation)

        affected_rows = self._repository.delete_supplier_quotation_file(
            file_id,
            cursor=cursor,
        )
        if affected_rows != 1:
            raise ValueError(
                "Supplier Quotation File metadata could not be deleted."
            )
        return existing

    def _validate_supplier_name(self, value: Any) -> str:
        supplier_name = self.require_non_empty_string(
            value,
            "Supplier name",
        )
        if len(supplier_name) > MAX_SUPPLIER_NAME_LENGTH:
            raise ValueError(
                "Supplier name may not exceed "
                f"{MAX_SUPPLIER_NAME_LENGTH} characters."
            )
        return supplier_name

    def _validate_quotation_reference(
        self,
        value: Any,
    ) -> str | None:
        reference = self.normalize_optional_text(value)
        if (
            reference is not None
            and len(reference) > MAX_QUOTATION_REFERENCE_LENGTH
        ):
            raise ValueError(
                "Quotation reference may not exceed "
                f"{MAX_QUOTATION_REFERENCE_LENGTH} characters."
            )
        return reference

    @staticmethod
    def _validate_quotation_date(
        value: date | datetime | str | None,
    ) -> date | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        normalized = str(value).strip()
        if not normalized:
            return None
        try:
            return date.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(
                "Quotation date must use YYYY-MM-DD format."
            ) from exc

    def _validate_remarks(self, value: Any) -> str | None:
        remarks = self.normalize_optional_text(value)
        if (
            remarks is not None
            and len(remarks) > MAX_QUOTATION_REMARKS_LENGTH
        ):
            raise ValueError(
                "Quotation remarks may not exceed "
                f"{MAX_QUOTATION_REMARKS_LENGTH} characters."
            )
        return remarks

    def _validate_status(self, value: Any) -> str:
        status = self.require_non_empty_string(
            value,
            "Supplier Quotation status",
        )
        if status not in SUPPLIER_QUOTATION_STATUSES:
            allowed = ", ".join(SUPPLIER_QUOTATION_STATUSES)
            raise ValueError(
                "Invalid Supplier Quotation status. "
                f"Allowed values: {allowed}."
            )
        return status

    def _validate_status_filter(self, value: Any) -> str:
        normalized = self.require_non_empty_string(
            value,
            "Status filter",
        )
        allowed_filters = {
            "Active",
            "Archived",
            "All",
            *SUPPLIER_QUOTATION_STATUSES,
        }
        if normalized not in allowed_filters:
            allowed = ", ".join(sorted(allowed_filters))
            raise ValueError(
                f"Invalid status filter. Allowed values: {allowed}."
            )
        return normalized

    @staticmethod
    def _validate_status_transition(
        current_status: Any,
        new_status: str,
    ) -> None:
        current = BaseService.normalize_text(current_status)
        if not current or current == new_status:
            return

        allowed_transitions = {
            "Received": {
                "Under Review",
                "Clarification Required",
                "Accepted",
                "Rejected",
            },
            "Under Review": {
                "Clarification Required",
                "Accepted",
                "Rejected",
                "Received",
            },
            "Clarification Required": {
                "Under Review",
                "Accepted",
                "Rejected",
            },
            "Accepted": {
                "Under Review",
                "Rejected",
            },
            "Rejected": {
                "Under Review",
                "Accepted",
            },
        }
        if new_status not in allowed_transitions.get(current, set()):
            raise ValueError(
                "Supplier Quotation status cannot change from "
                f"'{current}' to '{new_status}'."
            )

    def _validate_filename(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        filename = self.require_non_empty_string(value, field_name)
        if len(filename) > MAX_FILENAME_LENGTH:
            raise ValueError(
                f"{field_name} may not exceed "
                f"{MAX_FILENAME_LENGTH} characters."
            )
        return filename

    def _validate_folder_path(self, value: Any) -> str:
        folder_path = self.require_non_empty_string(
            value,
            "Folder path",
        )
        if len(folder_path) > MAX_FOLDER_PATH_LENGTH:
            raise ValueError(
                "Folder path may not exceed "
                f"{MAX_FOLDER_PATH_LENGTH} characters."
            )
        return folder_path

    def _validate_file_extension(
        self,
        value: Any,
    ) -> str | None:
        extension = self.normalize_optional_text(value)
        if extension is None:
            return None
        if len(extension) > 20:
            raise ValueError(
                "File extension may not exceed 20 characters."
            )
        return extension if extension.startswith(".") else f".{extension}"

    @staticmethod
    def _validate_file_size(value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            file_size = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "File size must be a whole number."
            ) from exc
        if file_size < 0:
            raise ValueError("File size cannot be negative.")
        return file_size

    @staticmethod
    def _require_not_archived(
        quotation: dict[str, Any],
    ) -> None:
        if bool(quotation.get("is_archived")):
            raise ValueError(
                "Archived Supplier Quotations cannot be modified."
            )

    @staticmethod
    def _require_create_permission(
        current_user: dict[str, Any],
    ) -> None:
        SupplierQuotationService.require_permission(
            lambda: PermissionService.can_edit_material_request(
                current_user
            ),
            "You do not have permission to create Supplier Quotations.",
        )

    @staticmethod
    def _require_edit_permission(
        current_user: dict[str, Any],
    ) -> None:
        SupplierQuotationService.require_permission(
            lambda: PermissionService.can_edit_material_request(
                current_user
            ),
            "You do not have permission to modify Supplier Quotations.",
        )

    @staticmethod
    def _require_archive_permission(
        current_user: dict[str, Any],
    ) -> None:
        SupplierQuotationService.require_permission(
            lambda: PermissionService.can_archive_material_request(
                current_user
            ),
            "You do not have permission to archive Supplier Quotations.",
        )

    @staticmethod
    def _require_restore_permission(
        current_user: dict[str, Any],
    ) -> None:
        SupplierQuotationService.require_permission(
            lambda: PermissionService.can_restore_material_request(
                current_user
            ),
            "You do not have permission to restore Supplier Quotations.",
        )

    @staticmethod
    def _require_delete_permission(
        current_user: dict[str, Any],
    ) -> None:
        SupplierQuotationService.require_permission(
            lambda: PermissionService.can_archive_material_request(
                current_user
            ),
            "You do not have permission to permanently delete "
            "Supplier Quotations.",
        )