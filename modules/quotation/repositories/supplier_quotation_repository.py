"""
Supplier Quotation Repository.

Database-only access layer for the Phase 1 Supplier Quotation Repository.

Responsibilities:
- Supplier quotation CRUD
- Archive / restore
- Status updates
- Supplier quotation file metadata CRUD
- Counts and simple repository statistics

Business validation, permissions, activity logging, and file-system operations
belong in the service layer.
"""

from typing import Any
from uuid import UUID

from core.database.repositories.base_repository import BaseRepository


_SUPPLIER_QUOTATION_COLUMNS = """
    supplier_quotation.id,
    supplier_quotation.material_request_id,
    supplier_quotation.supplier_name,
    supplier_quotation.quotation_reference,
    supplier_quotation.quotation_date,
    supplier_quotation.remarks,
    supplier_quotation.status,
    supplier_quotation.is_archived,
    supplier_quotation.created_at,
    supplier_quotation.created_by,
    supplier_quotation.updated_at,
    supplier_quotation.updated_by
"""


_SUPPLIER_QUOTATION_FILE_COLUMNS = """
    quotation_file.id,
    quotation_file.supplier_quotation_id,
    quotation_file.original_filename,
    quotation_file.stored_filename,
    quotation_file.folder_path,
    quotation_file.file_extension,
    quotation_file.file_size,
    quotation_file.uploaded_at,
    quotation_file.uploaded_by
"""


_CREATE_SUPPLIER_QUOTATION_SQL = f"""
INSERT INTO quotation.supplier_quotations (
    material_request_id,
    supplier_name,
    quotation_reference,
    quotation_date,
    remarks,
    status,
    created_by,
    updated_by
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING
    {_SUPPLIER_QUOTATION_COLUMNS};
"""


_GET_SUPPLIER_QUOTATION_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_COLUMNS}
FROM quotation.supplier_quotations AS supplier_quotation
WHERE supplier_quotation.id = %s;
"""


_LIST_BY_MATERIAL_REQUEST_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_COLUMNS},
    COUNT(quotation_file.id) AS file_count
FROM quotation.supplier_quotations AS supplier_quotation
LEFT JOIN quotation.supplier_quotation_files AS quotation_file
    ON quotation_file.supplier_quotation_id = supplier_quotation.id
WHERE supplier_quotation.material_request_id = %s
  AND (
      %s = 'All'
      OR (%s = 'Active' AND supplier_quotation.is_archived = FALSE)
      OR (%s = 'Archived' AND supplier_quotation.is_archived = TRUE)
      OR supplier_quotation.status = %s
  )
GROUP BY
    supplier_quotation.id,
    supplier_quotation.material_request_id,
    supplier_quotation.supplier_name,
    supplier_quotation.quotation_reference,
    supplier_quotation.quotation_date,
    supplier_quotation.remarks,
    supplier_quotation.status,
    supplier_quotation.is_archived,
    supplier_quotation.created_at,
    supplier_quotation.created_by,
    supplier_quotation.updated_at,
    supplier_quotation.updated_by
ORDER BY
    supplier_quotation.is_archived,
    supplier_quotation.quotation_date DESC NULLS LAST,
    supplier_quotation.created_at DESC;
"""


_LIST_ALL_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_COLUMNS},
    COUNT(quotation_file.id) AS file_count
FROM quotation.supplier_quotations AS supplier_quotation
LEFT JOIN quotation.supplier_quotation_files AS quotation_file
    ON quotation_file.supplier_quotation_id = supplier_quotation.id
WHERE
    %s = 'All'
    OR (%s = 'Active' AND supplier_quotation.is_archived = FALSE)
    OR (%s = 'Archived' AND supplier_quotation.is_archived = TRUE)
    OR supplier_quotation.status = %s
GROUP BY
    supplier_quotation.id,
    supplier_quotation.material_request_id,
    supplier_quotation.supplier_name,
    supplier_quotation.quotation_reference,
    supplier_quotation.quotation_date,
    supplier_quotation.remarks,
    supplier_quotation.status,
    supplier_quotation.is_archived,
    supplier_quotation.created_at,
    supplier_quotation.created_by,
    supplier_quotation.updated_at,
    supplier_quotation.updated_by
ORDER BY
    supplier_quotation.is_archived,
    supplier_quotation.created_at DESC;
"""


_UPDATE_SUPPLIER_QUOTATION_SQL = f"""
UPDATE quotation.supplier_quotations AS supplier_quotation
SET
    supplier_name = %s,
    quotation_reference = %s,
    quotation_date = %s,
    remarks = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = %s
WHERE supplier_quotation.id = %s
RETURNING
    {_SUPPLIER_QUOTATION_COLUMNS};
"""


_UPDATE_STATUS_SQL = f"""
UPDATE quotation.supplier_quotations AS supplier_quotation
SET
    status = %s,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = %s
WHERE supplier_quotation.id = %s
RETURNING
    {_SUPPLIER_QUOTATION_COLUMNS};
"""


_ARCHIVE_SQL = f"""
UPDATE quotation.supplier_quotations AS supplier_quotation
SET
    is_archived = TRUE,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = %s
WHERE supplier_quotation.id = %s
RETURNING
    {_SUPPLIER_QUOTATION_COLUMNS};
"""


_RESTORE_SQL = f"""
UPDATE quotation.supplier_quotations AS supplier_quotation
SET
    is_archived = FALSE,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = %s
WHERE supplier_quotation.id = %s
RETURNING
    {_SUPPLIER_QUOTATION_COLUMNS};
"""


_DELETE_SUPPLIER_QUOTATION_SQL = """
DELETE FROM quotation.supplier_quotations
WHERE id = %s;
"""


_SUPPLIER_QUOTATION_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM quotation.supplier_quotations
    WHERE id = %s
);
"""


_COUNT_BY_MATERIAL_REQUEST_SQL = """
SELECT COUNT(*)
FROM quotation.supplier_quotations
WHERE material_request_id = %s
  AND (
      %s = 'All'
      OR (%s = 'Active' AND is_archived = FALSE)
      OR (%s = 'Archived' AND is_archived = TRUE)
      OR status = %s
  );
"""


_GET_LATEST_BY_MATERIAL_REQUEST_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_COLUMNS}
FROM quotation.supplier_quotations AS supplier_quotation
WHERE supplier_quotation.material_request_id = %s
  AND supplier_quotation.is_archived = FALSE
ORDER BY
    supplier_quotation.quotation_date DESC NULLS LAST,
    supplier_quotation.created_at DESC
LIMIT 1;
"""


_GET_STATISTICS_SQL = """
SELECT
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE is_archived = FALSE) AS active_count,
    COUNT(*) FILTER (WHERE is_archived = TRUE) AS archived_count,
    COUNT(*) FILTER (WHERE status = 'Received') AS received_count,
    COUNT(*) FILTER (WHERE status = 'Under Review') AS under_review_count,
    COUNT(*) FILTER (
        WHERE status = 'Clarification Required'
    ) AS clarification_required_count,
    COUNT(*) FILTER (WHERE status = 'Accepted') AS accepted_count,
    COUNT(*) FILTER (WHERE status = 'Rejected') AS rejected_count
FROM quotation.supplier_quotations
WHERE material_request_id = %s;
"""


_CREATE_FILE_SQL = f"""
INSERT INTO quotation.supplier_quotation_files (
    supplier_quotation_id,
    original_filename,
    stored_filename,
    folder_path,
    file_extension,
    file_size,
    uploaded_by
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING
    {_SUPPLIER_QUOTATION_FILE_COLUMNS};
"""


_GET_FILE_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_FILE_COLUMNS}
FROM quotation.supplier_quotation_files AS quotation_file
WHERE quotation_file.id = %s;
"""


_LIST_FILES_SQL = f"""
SELECT
    {_SUPPLIER_QUOTATION_FILE_COLUMNS}
FROM quotation.supplier_quotation_files AS quotation_file
WHERE quotation_file.supplier_quotation_id = %s
ORDER BY quotation_file.uploaded_at, quotation_file.original_filename;
"""


_DELETE_FILE_SQL = """
DELETE FROM quotation.supplier_quotation_files
WHERE id = %s;
"""


_FILE_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM quotation.supplier_quotation_files
    WHERE id = %s
);
"""


_STORED_FILENAME_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM quotation.supplier_quotation_files
    WHERE supplier_quotation_id = %s
      AND LOWER(stored_filename) = LOWER(%s)
);
"""


_COUNT_FILES_SQL = """
SELECT COUNT(*)
FROM quotation.supplier_quotation_files
WHERE supplier_quotation_id = %s;
"""


class SupplierQuotationRepository(BaseRepository):
    """PostgreSQL repository for supplier quotation records."""

    @staticmethod
    def _map_quotation_row(
        row: tuple[Any, ...] | None,
        *,
        includes_file_count: bool = False,
    ) -> dict[str, Any] | None:
        if row is None:
            return None

        result = {
            "id": row[0],
            "material_request_id": row[1],
            "supplier_name": row[2],
            "quotation_reference": row[3],
            "quotation_date": row[4],
            "remarks": row[5],
            "status": row[6],
            "is_archived": row[7],
            "created_at": row[8],
            "created_by": row[9],
            "updated_at": row[10],
            "updated_by": row[11],
        }

        if includes_file_count:
            result["file_count"] = int(row[12] or 0)

        return result

    @staticmethod
    def _map_file_row(
        row: tuple[Any, ...] | None,
    ) -> dict[str, Any] | None:
        if row is None:
            return None

        return {
            "id": row[0],
            "supplier_quotation_id": row[1],
            "original_filename": row[2],
            "stored_filename": row[3],
            "folder_path": row[4],
            "file_extension": row[5],
            "file_size": row[6],
            "uploaded_at": row[7],
            "uploaded_by": row[8],
        }

    # ========================================================
    # SUPPLIER QUOTATIONS
    # ========================================================

    @classmethod
    def create_supplier_quotation(
        cls,
        *,
        material_request_id: UUID | str,
        supplier_name: str,
        quotation_reference: str | None,
        quotation_date,
        remarks: str | None,
        status: str,
        created_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _CREATE_SUPPLIER_QUOTATION_SQL,
            (
                material_request_id,
                supplier_name,
                quotation_reference,
                quotation_date,
                remarks,
                status,
                created_by,
                created_by,
            ),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def get_supplier_quotation(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.fetch_one(
            _GET_SUPPLIER_QUOTATION_SQL,
            (supplier_quotation_id,),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def list_supplier_quotations_by_material_request(
        cls,
        material_request_id: UUID | str,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        rows = cls.fetch_all(
            _LIST_BY_MATERIAL_REQUEST_SQL,
            (
                material_request_id,
                status_filter,
                status_filter,
                status_filter,
                status_filter,
            ),
            cursor=cursor,
        )
        return [
            cls._map_quotation_row(
                row,
                includes_file_count=True,
            )
            for row in rows
        ]

    @classmethod
    def list_supplier_quotations(
        cls,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        rows = cls.fetch_all(
            _LIST_ALL_SQL,
            (
                status_filter,
                status_filter,
                status_filter,
                status_filter,
            ),
            cursor=cursor,
        )
        return [
            cls._map_quotation_row(
                row,
                includes_file_count=True,
            )
            for row in rows
        ]

    @classmethod
    def update_supplier_quotation(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        supplier_name: str,
        quotation_reference: str | None,
        quotation_date,
        remarks: str | None,
        status: str,
        updated_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _UPDATE_SUPPLIER_QUOTATION_SQL,
            (
                supplier_name,
                quotation_reference,
                quotation_date,
                remarks,
                status,
                updated_by,
                supplier_quotation_id,
            ),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def update_supplier_quotation_status(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        status: str,
        updated_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _UPDATE_STATUS_SQL,
            (
                status,
                updated_by,
                supplier_quotation_id,
            ),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def archive_supplier_quotation(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        updated_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _ARCHIVE_SQL,
            (
                updated_by,
                supplier_quotation_id,
            ),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def restore_supplier_quotation(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        updated_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _RESTORE_SQL,
            (
                updated_by,
                supplier_quotation_id,
            ),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def delete_supplier_quotation(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        return cls.execute(
            _DELETE_SUPPLIER_QUOTATION_SQL,
            (supplier_quotation_id,),
            cursor=cursor,
        )

    @classmethod
    def supplier_quotation_exists(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            _SUPPLIER_QUOTATION_EXISTS_SQL,
            (supplier_quotation_id,),
            cursor=cursor,
        )

    @classmethod
    def count_supplier_quotations(
        cls,
        material_request_id: UUID | str,
        status_filter: str = "Active",
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            _COUNT_BY_MATERIAL_REQUEST_SQL,
            (
                material_request_id,
                status_filter,
                status_filter,
                status_filter,
                status_filter,
            ),
            cursor=cursor,
        )

    @classmethod
    def get_latest_supplier_quotation(
        cls,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.fetch_one(
            _GET_LATEST_BY_MATERIAL_REQUEST_SQL,
            (material_request_id,),
            cursor=cursor,
        )
        return cls._map_quotation_row(row)

    @classmethod
    def get_supplier_statistics(
        cls,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, int]:
        row = cls.fetch_one(
            _GET_STATISTICS_SQL,
            (material_request_id,),
            cursor=cursor,
        )

        if not row:
            return {
                "total": 0,
                "active": 0,
                "archived": 0,
                "received": 0,
                "under_review": 0,
                "clarification_required": 0,
                "accepted": 0,
                "rejected": 0,
            }

        return {
            "total": int(row[0] or 0),
            "active": int(row[1] or 0),
            "archived": int(row[2] or 0),
            "received": int(row[3] or 0),
            "under_review": int(row[4] or 0),
            "clarification_required": int(row[5] or 0),
            "accepted": int(row[6] or 0),
            "rejected": int(row[7] or 0),
        }

    # ========================================================
    # SUPPLIER QUOTATION FILES
    # ========================================================

    @classmethod
    def create_supplier_quotation_file(
        cls,
        *,
        supplier_quotation_id: UUID | str,
        original_filename: str,
        stored_filename: str,
        folder_path: str,
        file_extension: str | None,
        file_size: int | None,
        uploaded_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _CREATE_FILE_SQL,
            (
                supplier_quotation_id,
                original_filename,
                stored_filename,
                folder_path,
                file_extension,
                file_size,
                uploaded_by,
            ),
            cursor=cursor,
        )
        return cls._map_file_row(row)

    @classmethod
    def get_supplier_quotation_file(
        cls,
        supplier_quotation_file_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.fetch_one(
            _GET_FILE_SQL,
            (supplier_quotation_file_id,),
            cursor=cursor,
        )
        return cls._map_file_row(row)

    @classmethod
    def list_supplier_quotation_files(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        rows = cls.fetch_all(
            _LIST_FILES_SQL,
            (supplier_quotation_id,),
            cursor=cursor,
        )
        return [
            cls._map_file_row(row)
            for row in rows
        ]

    @classmethod
    def delete_supplier_quotation_file(
        cls,
        supplier_quotation_file_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        return cls.execute(
            _DELETE_FILE_SQL,
            (supplier_quotation_file_id,),
            cursor=cursor,
        )

    @classmethod
    def supplier_file_exists(
        cls,
        supplier_quotation_file_id: UUID | str,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            _FILE_EXISTS_SQL,
            (supplier_quotation_file_id,),
            cursor=cursor,
        )

    @classmethod
    def stored_filename_exists(
        cls,
        supplier_quotation_id: UUID | str,
        stored_filename: str,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            _STORED_FILENAME_EXISTS_SQL,
            (
                supplier_quotation_id,
                stored_filename,
            ),
            cursor=cursor,
        )

    @classmethod
    def count_supplier_quotation_files(
        cls,
        supplier_quotation_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            _COUNT_FILES_SQL,
            (supplier_quotation_id,),
            cursor=cursor,
        )