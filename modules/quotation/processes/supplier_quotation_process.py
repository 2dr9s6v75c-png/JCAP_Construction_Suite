"""
JCAP Construction Suite
Supplier Quotation Process

Coordinates Supplier Quotation business services, Material Request context,
shared-folder storage, activity logging, and PostgreSQL transactions.

Business validation and permission checks remain in SupplierQuotationService.
Database access remains in repositories. Physical file operations and
cross-component orchestration belong here.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from core.database.transaction_manager import TransactionManager
from core.documents.storage_service import (
    copy_supplier_quotation_files,
    delete_empty_supplier_quotation_folder,
    delete_stored_file,
)
from core.logging.activity_logger import ActivityLogger
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)
from modules.quotation.services.supplier_quotation_service import (
    DEFAULT_SUPPLIER_QUOTATION_STATUS,
    SupplierQuotationService,
)


class SupplierQuotationProcess:
    """Coordinate complete Phase 1 Supplier Quotation workflows."""

    def __init__(
        self,
        quotation_service: SupplierQuotationService | None = None,
        material_request_repository: MaterialRequestRepository | None = None,
        transaction_factory: Callable[[], Any] | None = None,
        file_copy_function: Callable[..., list[dict[str, Any]]] | None = None,
    ) -> None:
        self._quotation_service = (
            quotation_service or SupplierQuotationService()
        )
        self._material_request_repository = (
            material_request_repository or MaterialRequestRepository()
        )
        self._transaction_factory = (
            transaction_factory or TransactionManager
        )
        self._file_copy_function = (
            file_copy_function or copy_supplier_quotation_files
        )

    # ========================================================
    # READ
    # ========================================================

    def get_by_id(
        self,
        supplier_quotation_id: UUID | str,
    ) -> dict[str, Any] | None:
        """Return one Supplier Quotation record."""
        return self._quotation_service.get_by_id(
            supplier_quotation_id
        )

    def list_by_material_request(
        self,
        material_request_id: UUID | str,
        status_filter: str = "Active",
    ) -> list[dict[str, Any]]:
        """Return Supplier Quotations for one Material Request."""
        return self._quotation_service.list_by_material_request(
            material_request_id,
            status_filter=status_filter,
        )

    def list_files(
        self,
        supplier_quotation_id: UUID | str,
    ) -> list[dict[str, Any]]:
        """Return registered files for one Supplier Quotation."""
        return self._quotation_service.list_files(
            supplier_quotation_id
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        material_request_id: UUID | str,
        supplier_name: str,
        current_user: dict[str, Any],
        quotation_reference: str | None = None,
        quotation_date: date | datetime | str | None = None,
        remarks: str | None = None,
        status: str = DEFAULT_SUPPLIER_QUOTATION_STATUS,
        files: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a Supplier Quotation and register its copied files atomically.

        Database changes participate in one transaction. Files copied before a
        database failure are removed during compensation.
        """
        copied_files: list[dict[str, Any]] = []
        normalized_files = self._normalize_file_paths(files)

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

                quotation = self._quotation_service.create(
                    material_request_id=material_request["id"],
                    supplier_name=supplier_name,
                    current_user=current_user,
                    quotation_reference=quotation_reference,
                    quotation_date=quotation_date,
                    remarks=remarks,
                    status=status,
                    cursor=cursor,
                )

                if normalized_files:
                    copied_files = self._file_copy_function(
                        files=normalized_files,
                        project_code=storage_context["project_code"],
                        project_name=storage_context["project_name"],
                        request_no=storage_context["request_no"],
                        supplier_name=quotation["supplier_name"],
                    )

                file_records = self._register_copied_files(
                    quotation_id=quotation["id"],
                    copied_files=copied_files,
                    current_user=current_user,
                    cursor=cursor,
                )

                ActivityLogger.log_create(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=quotation["id"],
                    details=(
                        "Created Supplier Quotation from "
                        f"{quotation['supplier_name']} for "
                        f"{storage_context['request_no']}."
                    ),
                )

                return {
                    "supplier_quotation": quotation,
                    "files": file_records,
                    "material_request": material_request,
                }

        except Exception:
            self._cleanup_copied_files(copied_files)
            raise

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        supplier_quotation_id: UUID | str,
        supplier_name: str,
        current_user: dict[str, Any],
        quotation_reference: str | None = None,
        quotation_date: date | datetime | str | None = None,
        remarks: str | None = None,
        status: str = DEFAULT_SUPPLIER_QUOTATION_STATUS,
    ) -> dict[str, Any]:
        with self._transaction_factory() as cursor:
            previous = self._quotation_service.require_by_id(
                supplier_quotation_id,
                cursor=cursor,
            )

            updated = self._quotation_service.update(
                supplier_quotation_id=supplier_quotation_id,
                supplier_name=supplier_name,
                current_user=current_user,
                quotation_reference=quotation_reference,
                quotation_date=quotation_date,
                remarks=remarks,
                status=status,
                cursor=cursor,
            )

            ActivityLogger.log_update(
                cursor,
                user_id=self._get_user_id(current_user),
                module=ActivityLogger.MODULE_QUOTATION,
                record_id=updated["id"],
                details=(
                    "Updated Supplier Quotation from "
                    f"{previous['supplier_name']} to "
                    f"{updated['supplier_name']}."
                ),
            )

            return updated

    def update_status(
        self,
        supplier_quotation_id: UUID | str,
        status: str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        with self._transaction_factory() as cursor:
            previous = self._quotation_service.require_by_id(
                supplier_quotation_id,
                cursor=cursor,
            )

            updated = self._quotation_service.update_status(
                supplier_quotation_id=supplier_quotation_id,
                status=status,
                current_user=current_user,
                cursor=cursor,
            )

            ActivityLogger.log(
                cursor,
                user_id=self._get_user_id(current_user),
                action=ActivityLogger.ACTION_STATUS_CHANGE,
                module=ActivityLogger.MODULE_QUOTATION,
                record_id=updated["id"],
                details=(
                    "Changed Supplier Quotation status from "
                    f"{previous['status']} to {updated['status']} "
                    f"for {updated['supplier_name']}."
                ),
            )

            return updated

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def upload_files(
        self,
        supplier_quotation_id: UUID | str,
        files: Iterable[str],
        current_user: dict[str, Any],
    ) -> list[dict[str, Any]]:
        copied_files: list[dict[str, Any]] = []
        normalized_files = self._normalize_file_paths(files)

        if not normalized_files:
            raise ValueError(
                "Select at least one Supplier Quotation file."
            )

        try:
            with self._transaction_factory() as cursor:
                quotation = self._quotation_service.require_by_id(
                    supplier_quotation_id,
                    cursor=cursor,
                )
                material_request = self._require_material_request(
                    quotation["material_request_id"],
                    cursor=cursor,
                )
                storage_context = self._get_storage_context(
                    material_request,
                    cursor=cursor,
                )

                copied_files = self._file_copy_function(
                    files=normalized_files,
                    project_code=storage_context["project_code"],
                    project_name=storage_context["project_name"],
                    request_no=storage_context["request_no"],
                    supplier_name=quotation["supplier_name"],
                )

                file_records = self._register_copied_files(
                    quotation_id=quotation["id"],
                    copied_files=copied_files,
                    current_user=current_user,
                    cursor=cursor,
                )

                ActivityLogger.log_update(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=quotation["id"],
                    details=(
                        f"Uploaded {len(file_records)} file(s) for "
                        f"Supplier Quotation from "
                        f"{quotation['supplier_name']}."
                    ),
                )

                return file_records

        except Exception:
            self._cleanup_copied_files(copied_files)
            raise

    def delete_file(
        self,
        supplier_quotation_file_id: UUID | str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Delete one file using a reversible quarantine step.

        The file is renamed before database metadata is removed. If the
        transaction fails, the original filename is restored. After a
        successful commit, the quarantined file is permanently removed.
        """
        quarantined_path: Path | None = None
        original_path: Path | None = None
        deleted_metadata: dict[str, Any] | None = None

        try:
            with self._transaction_factory() as cursor:
                file_record = self._quotation_service.get_file_by_id(
                    supplier_quotation_file_id,
                    cursor=cursor,
                )
                if file_record is None:
                    raise ValueError(
                        "Supplier Quotation File not found."
                    )

                quotation = self._quotation_service.require_by_id(
                    file_record["supplier_quotation_id"],
                    cursor=cursor,
                )

                original_path, quarantined_path = (
                    self._quarantine_file(file_record)
                )

                deleted_metadata = (
                    self._quotation_service.delete_file_metadata(
                        supplier_quotation_file_id,
                        current_user=current_user,
                        cursor=cursor,
                    )
                )

                ActivityLogger.log_update(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=quotation["id"],
                    details=(
                        "Deleted Supplier Quotation file "
                        f"{file_record['original_filename']} from "
                        f"{quotation['supplier_name']}."
                    ),
                )

            self._delete_quarantined_file(quarantined_path)
            self._remove_empty_folder(
                deleted_metadata.get("folder_path")
                if deleted_metadata
                else None
            )
            return deleted_metadata

        except Exception:
            self._restore_quarantined_file(
                original_path,
                quarantined_path,
            )
            raise

    # ========================================================
    # ARCHIVE / RESTORE / DELETE
    # ========================================================

    def archive(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        with self._transaction_factory() as cursor:
            archived = self._quotation_service.archive(
                supplier_quotation_id,
                current_user=current_user,
                cursor=cursor,
            )

            ActivityLogger.log_archive(
                cursor,
                user_id=self._get_user_id(current_user),
                module=ActivityLogger.MODULE_QUOTATION,
                record_id=archived["id"],
                details=(
                    "Archived Supplier Quotation from "
                    f"{archived['supplier_name']}."
                ),
            )

            return archived

    def restore(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        with self._transaction_factory() as cursor:
            restored = self._quotation_service.restore(
                supplier_quotation_id,
                current_user=current_user,
                cursor=cursor,
            )

            ActivityLogger.log_restore(
                cursor,
                user_id=self._get_user_id(current_user),
                module=ActivityLogger.MODULE_QUOTATION,
                record_id=restored["id"],
                details=(
                    "Restored Supplier Quotation from "
                    f"{restored['supplier_name']}."
                ),
            )

            return restored

    def delete(
        self,
        supplier_quotation_id: UUID | str,
        current_user: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Permanently delete an archived quotation and its managed files.

        Every existing managed file is quarantined first. A failed database
        transaction restores all files to their original names.
        """
        quarantined_files: list[tuple[Path, Path]] = []
        deleted_quotation: dict[str, Any] | None = None
        file_records: list[dict[str, Any]] = []

        try:
            with self._transaction_factory() as cursor:
                quotation = self._quotation_service.require_by_id(
                    supplier_quotation_id,
                    cursor=cursor,
                )
                file_records = self._quotation_service.list_files(
                    supplier_quotation_id,
                    cursor=cursor,
                )

                for file_record in file_records:
                    original_path, quarantined_path = (
                        self._quarantine_file(file_record)
                    )
                    if (
                        original_path is not None
                        and quarantined_path is not None
                    ):
                        quarantined_files.append(
                            (original_path, quarantined_path)
                        )

                ActivityLogger.log(
                    cursor,
                    user_id=self._get_user_id(current_user),
                    action="DELETE",
                    module=ActivityLogger.MODULE_QUOTATION,
                    record_id=quotation["id"],
                    details=(
                        "Permanently deleted archived Supplier "
                        f"Quotation from {quotation['supplier_name']}."
                    ),
                )

                deleted_quotation = self._quotation_service.delete(
                    supplier_quotation_id,
                    current_user=current_user,
                    cursor=cursor,
                )

            for _, quarantined_path in quarantined_files:
                self._delete_quarantined_file(quarantined_path)

            for folder_path in {
                record.get("folder_path")
                for record in file_records
                if record.get("folder_path")
            }:
                self._remove_empty_folder(folder_path)

            return deleted_quotation

        except Exception:
            for original_path, quarantined_path in reversed(
                quarantined_files
            ):
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
        material_request = (
            self._material_request_repository.get_by_id(
                material_request_id,
                cursor=cursor,
            )
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
        """
        Resolve project storage information using the active transaction.

        MaterialRequestRepository intentionally owns only Material Request
        persistence, so the process resolves the cross-table project context.
        """
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

    def _register_copied_files(
        self,
        quotation_id: UUID | str,
        copied_files: list[dict[str, Any]],
        current_user: dict[str, Any],
        *,
        cursor,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        for file_data in copied_files:
            record = self._quotation_service.register_file(
                supplier_quotation_id=quotation_id,
                original_filename=file_data["original_filename"],
                stored_filename=file_data["stored_filename"],
                folder_path=file_data["folder_path"],
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
    def _get_user_id(current_user: dict[str, Any]) -> Any:
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
        folders: set[str] = set()

        for file_data in reversed(copied_files):
            folder_path = file_data.get("folder_path")
            stored_filename = file_data.get("stored_filename")

            if folder_path:
                folders.add(str(folder_path))

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

        for folder_path in folders:
            SupplierQuotationProcess._remove_empty_folder(
                folder_path
            )

    @staticmethod
    def _quarantine_file(
        file_record: dict[str, Any],
    ) -> tuple[Path | None, Path | None]:
        folder_path = str(
            file_record.get("folder_path") or ""
        ).strip()
        stored_filename = str(
            file_record.get("stored_filename") or ""
        ).strip()

        if not folder_path or not stored_filename:
            raise ValueError(
                "Supplier Quotation File storage metadata is incomplete."
            )

        original_path = Path(folder_path) / stored_filename

        if not original_path.exists():
            # Metadata may outlive a manually removed file. The database
            # operation can still proceed without a physical quarantine.
            return None, None

        if not original_path.is_file():
            raise ValueError(
                f"Stored quotation path is not a file: {original_path}"
            )

        quarantine_name = (
            f".{original_path.name}.deleting-{uuid4().hex}"
        )
        quarantined_path = original_path.with_name(
            quarantine_name
        )
        os.replace(original_path, quarantined_path)

        return original_path, quarantined_path

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
    def _remove_empty_folder(
        folder_path: str | None,
    ) -> None:
        if not folder_path:
            return

        try:
            delete_empty_supplier_quotation_folder(
                str(folder_path)
            )
        except OSError:
            pass