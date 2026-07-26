"""
JCAP Construction Suite
Material Request Attachment Service

Owns Material Request attachment validation, permission enforcement, and
single-record repository operations.

Transaction orchestration, physical file copying/removal, activity logging,
and file/folder opening belong to the process layer.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from core.security.permissions import PermissionService
from core.services.base_service import BaseService
from modules.quotation.repositories.material_request_attachment_repository import (
    MaterialRequestAttachmentRepository,
)
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)


MAX_FILENAME_LENGTH = 255
MAX_RELATIVE_MODULE_LENGTH = 500
MAX_FILE_EXTENSION_LENGTH = 20


class MaterialRequestAttachmentService(BaseService):
    """Business service for Material Request attachment metadata."""

    def __init__(
        self,
        repository: MaterialRequestAttachmentRepository | None = None,
        material_request_repository: MaterialRequestRepository | None = None,
    ) -> None:
        self._repository = (
            repository or MaterialRequestAttachmentRepository()
        )
        self._material_request_repository = (
            material_request_repository or MaterialRequestRepository()
        )

    # ========================================================
    # READ
    # ========================================================

    def get_by_id(
        self,
        attachment_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        normalized_id = self.normalize_uuid_object(
            attachment_id,
            "Material Request Attachment ID",
        )
        return self._repository.get_attachment(
            normalized_id,
            cursor=cursor,
        )

    def require_by_id(
        self,
        attachment_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        return self.require_record(
            self.get_by_id(
                attachment_id,
                cursor=cursor,
            ),
            "Material Request Attachment",
        )

    def list_by_material_request(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        normalized_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        self._require_material_request(
            normalized_id,
            cursor=cursor,
        )
        return self._repository.list_attachments(
            normalized_id,
            cursor=cursor,
        )

    def search(
        self,
        material_request_id: UUID | str,
        search_text: str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        normalized_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        self._require_material_request(
            normalized_id,
            cursor=cursor,
        )
        return self._repository.search_attachments(
            normalized_id,
            self.normalize_text(search_text),
            cursor=cursor,
        )

    def count_by_material_request(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        normalized_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        self._require_material_request(
            normalized_id,
            cursor=cursor,
        )
        return self._repository.count_attachments(
            normalized_id,
            cursor=cursor,
        )

    # ========================================================
    # WRITE
    # ========================================================

    def register_attachment(
        self,
        material_request_id: UUID | str,
        original_filename: str,
        stored_filename: str,
        relative_module: str,
        current_user: dict[str, Any],
        file_extension: str | None = None,
        file_size: int | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        normalized_mr_id = self.normalize_uuid_object(
            material_request_id,
            "Material Request ID",
        )
        current_user = self.require_user(current_user)
        uploaded_by = self.get_user_uuid(current_user)
        self._require_edit_permission(current_user)

        self._require_material_request(
            normalized_mr_id,
            cursor=cursor,
        )

        created = self._repository.create_attachment(
            material_request_id=normalized_mr_id,
            original_filename=self._validate_filename(
                original_filename,
                "Original filename",
            ),
            stored_filename=self._validate_filename(
                stored_filename,
                "Stored filename",
            ),
            file_extension=self._validate_file_extension(
                file_extension
            ),
            file_size=self._validate_file_size(file_size),
            relative_module=self._validate_relative_module(
                relative_module
            ),
            uploaded_by=uploaded_by,
            cursor=cursor,
        )

        return self.require_record(
            created,
            "Material Request Attachment",
        )

    def delete_metadata(
        self,
        attachment_id: UUID | str,
        current_user: dict[str, Any],
        *,
        cursor=None,
    ) -> dict[str, Any]:
        normalized_id = self.normalize_uuid_object(
            attachment_id,
            "Material Request Attachment ID",
        )
        current_user = self.require_user(current_user)
        self._require_edit_permission(current_user)

        existing = self.require_by_id(
            normalized_id,
            cursor=cursor,
        )

        self._require_material_request(
            existing["material_request_id"],
            cursor=cursor,
        )

        affected_rows = self._repository.delete_attachment(
            normalized_id,
            cursor=cursor,
        )

        if affected_rows != 1:
            raise ValueError(
                "Material Request Attachment metadata could not be deleted."
            )

        return existing

    # ========================================================
    # VALIDATION
    # ========================================================

    def _require_material_request(
        self,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any]:
        material_request = self._material_request_repository.get_by_id(
            material_request_id,
            cursor=cursor,
        )

        return self.require_record(
            material_request,
            "Material Request",
        )

    def _validate_filename(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        filename = self.require_non_empty_string(
            value,
            field_name,
        )

        if len(filename) > MAX_FILENAME_LENGTH:
            raise ValueError(
                f"{field_name} may not exceed "
                f"{MAX_FILENAME_LENGTH} characters."
            )

        return filename

    def _validate_relative_module(
        self,
        value: Any,
    ) -> str:
        relative_module = self.require_non_empty_string(
            value,
            "Relative module",
        )

        if len(relative_module) > MAX_RELATIVE_MODULE_LENGTH:
            raise ValueError(
                "Relative module may not exceed "
                f"{MAX_RELATIVE_MODULE_LENGTH} characters."
            )

        return relative_module

    def _validate_file_extension(
        self,
        value: Any,
    ) -> str | None:
        extension = self.normalize_optional_text(value)

        if extension is None:
            return None

        extension = extension.lstrip(".").lower()

        if len(extension) > MAX_FILE_EXTENSION_LENGTH:
            raise ValueError(
                "File extension may not exceed "
                f"{MAX_FILE_EXTENSION_LENGTH} characters."
            )

        return extension

    @staticmethod
    def _validate_file_size(
        value: Any,
    ) -> int | None:
        if value is None or value == "":
            return None

        try:
            file_size = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "File size must be a whole number."
            ) from exc

        if file_size < 0:
            raise ValueError(
                "File size cannot be negative."
            )

        return file_size

    # ========================================================
    # PERMISSIONS
    # ========================================================

    @staticmethod
    def _require_edit_permission(
        current_user: dict[str, Any],
    ) -> None:
        MaterialRequestAttachmentService.require_permission(
            lambda: PermissionService.can_edit_material_request(
                current_user
            ),
            "You do not have permission to manage "
            "Material Request attachments.",
        )