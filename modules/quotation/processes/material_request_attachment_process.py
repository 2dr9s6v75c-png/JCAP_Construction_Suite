"""
JCAP Construction Suite
Material Request Attachment Process

Coordinates Material Request attachment services, shared-folder storage,
activity logging, operating-system file actions, and PostgreSQL transactions.

Business validation and permission checks remain in
MaterialRequestAttachmentService. Database access remains in repositories.
Physical file operations and cross-component orchestration belong here.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from core.database.transaction_manager import TransactionManager
from core.documents.storage_service import (
    copy_attachments_to_request_folder,
    delete_stored_file,
    ensure_material_request_folder,
)
from core.logging.activity_logger import ActivityLogger
from core.realtime.realtime_event_service import RealtimeEventService
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)
from modules.quotation.services.material_request_attachment_service import (
    MaterialRequestAttachmentService,
)


class MaterialRequestAttachmentProcess:
    """Coordinate complete Phase 1 Material Request attachment workflows."""

    def __init__(
        self,
        attachment_service: MaterialRequestAttachmentService | None = None,
        material_request_repository: MaterialRequestRepository | None = None,
        transaction_factory: Callable[[], Any] | None = None,
        file_copy_function: Callable[..., list[dict[str, Any]]] | None = None,
    ) -> None:
        self._attachment_service = (
            attachment_service or MaterialRequestAttachmentService()
        )
        self._material_request_repository = (
            material_request_repository or MaterialRequestRepository()
        )
        self._transaction_factory = (
            transaction_factory or TransactionManager
        )
        self._file_copy_function = (
            file_copy_function or copy_attachments_to_request_folder
        )

    # ========================================================
    # READ
    # ========================================================

    def get_by_id(
        self,
        attachment_id: UUID | str,
    ) -> dict[str, Any] | None:
        """Return one Material Request attachment record."""
        return self._attachment_service.get_by_id(attachment_id)

    def list_by_material_request(
        self,
        material_request_id: UUID | str,
    ) -> list[dict[str, Any]]:
        """Return all attachments for one Material Request."""
        return self._attachment_service.list_by_material_request(
            material_request_id
        )

    def search(
        self,
        material_request_id: UUID | str,
        search_text: str,
    ) -> list[dict[str, Any]]:
        """Search Material Request attachments by filename or extension."""
        return self._attachment_service.search(
            material_request_id,
            search_text,
        )

    def count_by_material_request(
        self,
        material_request_id: UUID | str,
    ) -> int:
        """Return the attachment count for one Material Request."""
        return self._attachment_service.count_by_material_request(
            material_request_id
        )

    # ========================================================
    # UPLOAD
    # ========================================================

    def upload_files(
        self,
        material_request_id: UUID | str,
        files: Iterable[str],
        current_user: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Copy files and register their metadata atomically.

        Database changes participate in one transaction. Any files copied
        before a database failure are removed during compensation.
        """
        copied_files: list[dict[str, Any]] = []
        normalized_files = self._normalize_file_paths(files)

        if not normalized_files:
            raise ValueError(
                "Select at least one Material Request attachment."
            )

        try:
            with self._transaction_factory() as cursor:
                material_request = self._require_material_request(
                    material_request_id,
                    cursor=cursor,
                )
                storage_context = self._get_storage_context(
                    material_request,
                    cursor=cursor,
                )

                copied_files = self._file_copy_function(
                    attachments=normalized_files,
                    project_code=storage_context["project_code"],
                    project_name=storage_context["project_name"],
                    request_no=storage_context["request_no"],
                )

                if not copied_files:
                    raise ValueError(
                        "No valid Material Request attachments were copied."
                    )

                records = self._register_copied_files(
                    material_request_id=material_request["id"],
                    copied_files=copied_files,
                    current_user=current_user,
                    cursor=cursor,
                )

                uploaded_filenames = [
                    str(record.get("original_filename") or "").strip()
                    for record in records
                    if str(record.get("original_filename") or "").strip()
                ]

                if len(uploaded_filenames) == 1:
                    activity_details = (
                        f"Uploaded attachment "
                        f"{uploaded_filenames[0]} to Material Request "
                        f"{storage_context['request_no']}."
                    )
                elif uploaded_filenames:
                    activity_details = (
                        f"Uploaded {len(uploaded_filenames)} attachments to "
                        f"Material Request {storage_context['request_no']}: "
                        f"{', '.join(uploaded_filenames)}."
                    )
                else:
                    activity_details = (
                        f"Uploaded {len(records)} attachment(s) to "
                        f"Material Request {storage_context['request_no']}."
                    )

                ActivityLogger.log_update(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=material_request["id"],
                    details=activity_details,
                )

                RealtimeEventService.publish(
                    "material_request_attachment_uploaded",
                    entity_type="material_request",
                    entity_id=material_request["id"],
                    action="attachment_uploaded",
                    actor_user_id=self._get_user_id(current_user),
                    data={
                        "mr_number": storage_context["request_no"],
                        "attachment_count": len(records),
                    },
                    cursor=cursor,
                )

                return records

        except Exception:
            self._cleanup_copied_files(copied_files)
            raise

    # ========================================================
    # OPEN
    # ========================================================

    def open_attachment(
        self,
        attachment_id: UUID | str,
    ) -> str:
        """Open one stored attachment using the operating system."""
        with self._transaction_factory() as cursor:
            attachment = self._attachment_service.require_by_id(
                attachment_id,
                cursor=cursor,
            )
            material_request = self._require_material_request(
                attachment["material_request_id"],
                cursor=cursor,
            )
            file_path = self._resolve_attachment_path(
                attachment,
                material_request,
                cursor=cursor,
            )

        if not file_path.exists():
            raise FileNotFoundError(
                f"Stored attachment was not found: {file_path}"
            )
        if not file_path.is_file():
            raise ValueError(
                f"Stored attachment path is not a file: {file_path}"
            )

        self._open_path(file_path)
        return str(file_path)

    def open_attachment_folder(
        self,
        attachment_id: UUID | str,
    ) -> str:
        """Open the attachment folder and select the file when supported."""
        with self._transaction_factory() as cursor:
            attachment = self._attachment_service.require_by_id(
                attachment_id,
                cursor=cursor,
            )
            material_request = self._require_material_request(
                attachment["material_request_id"],
                cursor=cursor,
            )
            file_path = self._resolve_attachment_path(
                attachment,
                material_request,
                cursor=cursor,
            )

        folder_path = file_path.parent

        if not folder_path.exists():
            raise FileNotFoundError(
                f"Material Request attachment folder was not found: "
                f"{folder_path}"
            )
        if not folder_path.is_dir():
            raise ValueError(
                f"Attachment folder path is not a directory: {folder_path}"
            )

        self._open_folder(folder_path, file_path)
        return str(folder_path)

    def open_material_request_folder(
        self,
        material_request_id: UUID | str,
    ) -> str:
        """Open the managed folder for one Material Request."""
        with self._transaction_factory() as cursor:
            material_request = self._require_material_request(
                material_request_id,
                cursor=cursor,
            )
            context = self._get_storage_context(
                material_request,
                cursor=cursor,
            )

        folder_path = Path(
            ensure_material_request_folder(
                project_code=context["project_code"],
                project_name=context["project_name"],
                request_no=context["request_no"],
            )
        )

        self._open_path(folder_path)
        return str(folder_path)

    # ========================================================
    # DELETE
    # ========================================================

    def delete_attachment(
        self,
        attachment_id: UUID | str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Delete one attachment using a reversible quarantine step.

        The physical file is renamed before database metadata is removed.
        If the transaction fails, the original filename is restored. After a
        successful commit, the quarantined file is permanently deleted.
        """
        original_path: Path | None = None
        quarantined_path: Path | None = None
        deleted_metadata: dict[str, Any] | None = None

        try:
            with self._transaction_factory() as cursor:
                attachment = self._attachment_service.require_by_id(
                    attachment_id,
                    cursor=cursor,
                )
                material_request = self._require_material_request(
                    attachment["material_request_id"],
                    cursor=cursor,
                )
                storage_context = self._get_storage_context(
                    material_request,
                    cursor=cursor,
                )

                file_path = self._resolve_attachment_path(
                    attachment,
                    material_request,
                    cursor=cursor,
                )
                original_path, quarantined_path = self._quarantine_file(
                    file_path
                )

                deleted_metadata = (
                    self._attachment_service.delete_metadata(
                        attachment_id,
                        current_user=current_user,
                        cursor=cursor,
                    )
                )

                ActivityLogger.log_update(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=material_request["id"],
                    details=(
                        "Deleted Material Request attachment "
                        f"{attachment['original_filename']} from "
                        f"{storage_context['request_no']}."
                    ),
                )

                RealtimeEventService.publish(
                    "material_request_attachment_deleted",
                    entity_type="material_request",
                    entity_id=material_request["id"],
                    action="attachment_deleted",
                    actor_user_id=self._get_user_id(current_user),
                    data={
                        "mr_number": storage_context["request_no"],
                        "original_filename": attachment["original_filename"],
                    },
                    cursor=cursor,
                )

            self._delete_quarantined_file(quarantined_path)
            return deleted_metadata

        except Exception:
            self._restore_quarantined_file(
                original_path,
                quarantined_path,
            )
            raise

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _require_material_request(
        self,
        material_request_id: UUID | str,
        *,
        cursor,
    ) -> dict[str, Any]:
        material_request = self._material_request_repository.get_by_id(
            material_request_id,
            cursor=cursor,
        )

        if material_request is None:
            raise ValueError("Material Request not found.")

        return material_request

    @staticmethod
    def _get_storage_context(
        material_request: dict[str, Any],
        *,
        cursor,
    ) -> dict[str, str]:
        cursor.execute(
            """
            SELECT
                project.project_code,
                project.project_name
            FROM master.projects AS project
            WHERE project.id = %s
            """,
            (material_request["project_id"],),
        )
        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                "The Material Request project could not be found."
            )

        project_code = str(row[0] or "").strip()
        project_name = str(row[1] or "").strip()
        request_no = str(
            material_request.get("mr_number")
            or material_request.get("request_no")
            or material_request.get("folder_name")
            or ""
        ).strip()

        if not project_code:
            raise ValueError(
                "The Material Request project code is missing."
            )
        if not project_name:
            raise ValueError(
                "The Material Request project name is missing."
            )
        if not request_no:
            raise ValueError(
                "The Material Request number is missing."
            )

        return {
            "project_code": project_code,
            "project_name": project_name,
            "request_no": request_no,
        }

    def _resolve_attachment_path(
        self,
        attachment: dict[str, Any],
        material_request: dict[str, Any],
        *,
        cursor,
    ) -> Path:
        stored_filename = str(
            attachment.get("stored_filename") or ""
        ).strip()

        if not stored_filename:
            raise ValueError(
                "Material Request attachment storage metadata is incomplete."
            )

        context = self._get_storage_context(
            material_request,
            cursor=cursor,
        )
        folder_path = ensure_material_request_folder(
            project_code=context["project_code"],
            project_name=context["project_name"],
            request_no=context["request_no"],
        )

        return Path(folder_path) / stored_filename

    def _register_copied_files(
        self,
        material_request_id: UUID | str,
        copied_files: list[dict[str, Any]],
        current_user: dict[str, Any],
        *,
        cursor,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        for file_data in copied_files:
            record = self._attachment_service.register_attachment(
                material_request_id=material_request_id,
                original_filename=file_data["original_filename"],
                stored_filename=file_data["stored_filename"],
                relative_module=file_data["relative_module"],
                current_user=current_user,
                file_extension=file_data.get("file_extension"),
                file_size=file_data.get("file_size"),
                cursor=cursor,
            )
            records.append(record)

        return records

    @staticmethod
    def _normalize_file_paths(
        files: Iterable[str] | None,
    ) -> list[str]:
        if files is None:
            return []

        normalized: list[str] = []

        for value in files:
            path = str(value or "").strip()
            if path:
                normalized.append(path)

        return normalized

    @staticmethod
    def _get_user_id(
        current_user: dict[str, Any],
    ) -> Any:
        if not isinstance(current_user, dict):
            raise ValueError(
                "A valid authenticated user is required."
            )

        user_id = current_user.get("id")

        if not user_id:
            raise ValueError(
                "The authenticated user ID is missing."
            )

        return user_id

    @staticmethod
    def _cleanup_copied_files(
        copied_files: list[dict[str, Any]],
    ) -> None:
        for file_data in reversed(copied_files):
            folder_path = file_data.get("folder_path")
            stored_filename = file_data.get("stored_filename")

            if not folder_path or not stored_filename:
                continue

            try:
                delete_stored_file(
                    str(folder_path),
                    str(stored_filename),
                    missing_ok=True,
                )
            except OSError:
                # Preserve the original database/storage exception.
                pass

    @staticmethod
    def _quarantine_file(
        file_path: Path,
    ) -> tuple[Path | None, Path | None]:
        if not file_path.exists():
            # Metadata may outlive a manually removed physical file.
            return None, None

        if not file_path.is_file():
            raise ValueError(
                f"Stored attachment path is not a file: {file_path}"
            )

        quarantined_path = file_path.with_name(
            f".{file_path.name}.deleting-{uuid4().hex}"
        )
        os.replace(file_path, quarantined_path)

        return file_path, quarantined_path

    @staticmethod
    def _restore_quarantined_file(
        original_path: Path | None,
        quarantined_path: Path | None,
    ) -> None:
        if (
            original_path is None
            or quarantined_path is None
            or not quarantined_path.exists()
        ):
            return

        os.replace(quarantined_path, original_path)

    @staticmethod
    def _delete_quarantined_file(
        quarantined_path: Path | None,
    ) -> None:
        if (
            quarantined_path is not None
            and quarantined_path.exists()
        ):
            quarantined_path.unlink()

    @staticmethod
    def _open_path(path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return

        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return

        subprocess.Popen(["xdg-open", str(path)])

    @staticmethod
    def _open_folder(
        folder_path: Path,
        file_path: Path | None = None,
    ) -> None:
        if sys.platform.startswith("win"):
            if file_path is not None and file_path.exists():
                subprocess.Popen(
                    ["explorer", "/select,", str(file_path)]
                )
            else:
                os.startfile(str(folder_path))  # type: ignore[attr-defined]
            return

        MaterialRequestAttachmentProcess._open_path(folder_path)