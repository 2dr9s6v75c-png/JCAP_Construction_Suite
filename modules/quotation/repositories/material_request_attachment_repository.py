"""
Material Request Attachment Repository.

Database-only access layer for files attached directly to Material Requests.
"""

from typing import Any
from uuid import UUID

from core.database.repositories.base_repository import BaseRepository


_ATTACHMENT_COLUMNS = """
    attachment.id,
    attachment.material_request_id,
    attachment.original_filename,
    attachment.stored_filename,
    attachment.file_extension,
    attachment.file_size,
    attachment.relative_module,
    attachment.uploaded_by,
    attachment.uploaded_at
"""

_ATTACHMENT_RETURNING_COLUMNS = """
    id,
    material_request_id,
    original_filename,
    stored_filename,
    file_extension,
    file_size,
    relative_module,
    uploaded_by,
    uploaded_at
"""

_CREATE_SQL = f"""
INSERT INTO quotation.material_request_attachments (
    material_request_id,
    original_filename,
    stored_filename,
    file_extension,
    file_size,
    relative_module,
    uploaded_by
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING
    {_ATTACHMENT_RETURNING_COLUMNS};
"""

_GET_SQL = f"""
SELECT
    {_ATTACHMENT_COLUMNS}
FROM quotation.material_request_attachments AS attachment
WHERE attachment.id = %s;
"""

_LIST_SQL = f"""
SELECT
    {_ATTACHMENT_COLUMNS}
FROM quotation.material_request_attachments AS attachment
WHERE attachment.material_request_id = %s
ORDER BY
    attachment.uploaded_at DESC,
    attachment.original_filename,
    attachment.id;
"""

_SEARCH_SQL = f"""
SELECT
    {_ATTACHMENT_COLUMNS}
FROM quotation.material_request_attachments AS attachment
WHERE attachment.material_request_id = %s
  AND (
      attachment.original_filename ILIKE %s
      OR attachment.stored_filename ILIKE %s
      OR COALESCE(attachment.file_extension, '') ILIKE %s
  )
ORDER BY
    attachment.uploaded_at DESC,
    attachment.original_filename,
    attachment.id;
"""

_DELETE_SQL = """
DELETE FROM quotation.material_request_attachments
WHERE id = %s;
"""

_EXISTS_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM quotation.material_request_attachments
    WHERE id = %s
);
"""

_COUNT_SQL = """
SELECT COUNT(*)
FROM quotation.material_request_attachments
WHERE material_request_id = %s;
"""


class MaterialRequestAttachmentRepository(BaseRepository):
    """PostgreSQL repository for Material Request attachment metadata."""

    @staticmethod
    def _map_row(
        row: tuple[Any, ...] | None,
    ) -> dict[str, Any] | None:
        if row is None:
            return None

        return {
            "id": row[0],
            "material_request_id": row[1],
            "original_filename": row[2],
            "stored_filename": row[3],
            "file_extension": row[4],
            "file_size": row[5],
            "relative_module": row[6],
            "uploaded_by": row[7],
            "uploaded_at": row[8],
        }

    @classmethod
    def _map_rows(
        cls,
        rows: list[tuple[Any, ...]],
    ) -> list[dict[str, Any]]:
        mapped: list[dict[str, Any]] = []

        for row in rows:
            item = cls._map_row(row)
            if item is not None:
                mapped.append(item)

        return mapped

    @classmethod
    def create_attachment(
        cls,
        *,
        material_request_id: UUID | str,
        original_filename: str,
        stored_filename: str,
        file_extension: str | None,
        file_size: int | None,
        relative_module: str,
        uploaded_by: UUID | str,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.execute_returning(
            _CREATE_SQL,
            (
                material_request_id,
                original_filename,
                stored_filename,
                file_extension,
                file_size,
                relative_module,
                uploaded_by,
            ),
            cursor=cursor,
        )
        return cls._map_row(row)

    @classmethod
    def get_attachment(
        cls,
        attachment_id: UUID | str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.fetch_one(
            _GET_SQL,
            (attachment_id,),
            cursor=cursor,
        )
        return cls._map_row(row)

    @classmethod
    def list_attachments(
        cls,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        rows = cls.fetch_all(
            _LIST_SQL,
            (material_request_id,),
            cursor=cursor,
        )
        return cls._map_rows(rows)

    @classmethod
    def search_attachments(
        cls,
        material_request_id: UUID | str,
        search_text: str,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        term = str(search_text or "").strip()
        if not term:
            return cls.list_attachments(
                material_request_id,
                cursor=cursor,
            )

        pattern = f"%{term}%"
        rows = cls.fetch_all(
            _SEARCH_SQL,
            (
                material_request_id,
                pattern,
                pattern,
                pattern,
            ),
            cursor=cursor,
        )
        return cls._map_rows(rows)

    @classmethod
    def delete_attachment(
        cls,
        attachment_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        return cls.execute(
            _DELETE_SQL,
            (attachment_id,),
            cursor=cursor,
        )

    @classmethod
    def attachment_exists(
        cls,
        attachment_id: UUID | str,
        *,
        cursor=None,
    ) -> bool:
        return cls.exists(
            _EXISTS_SQL,
            (attachment_id,),
            cursor=cursor,
        )

    @classmethod
    def count_attachments(
        cls,
        material_request_id: UUID | str,
        *,
        cursor=None,
    ) -> int:
        return cls.count(
            _COUNT_SQL,
            (material_request_id,),
            cursor=cursor,
        )