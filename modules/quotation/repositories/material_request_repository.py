"""
Material Request Repository.

Persists Material Request records and keeps the legacy display status aligned
with the newer workflow status during assignment operations.
"""

from typing import Any
from uuid import UUID

from core.database.repositories.base_repository import BaseRepository


_MATERIAL_REQUEST_COLUMNS = """
    material_request.id,
    material_request.request_no,
    material_request.project_id,
    material_request.request_description,
    material_request.requested_by,
    material_request.requested_by_user_id,
    material_request.assigned_to,
    material_request.priority,
    material_request.status,
    material_request.due_date,
    material_request.remarks,
    material_request.folder_name,
    material_request.created_by,
    material_request.created_at,
    material_request.updated_at,
    material_request.material_request_description,
    material_request.mr_number,
    material_request.locked_by,
    material_request.locked_at,
    material_request.lock_expires_at,
    material_request.workflow_status,
    material_request.current_assignment_id
"""


_GET_BY_ID_SQL = f"""
SELECT
    {_MATERIAL_REQUEST_COLUMNS}
FROM quotation.material_requests AS material_request
WHERE material_request.id = %s;
"""


_UPDATE_ASSIGNMENT_CONTEXT_SQL = f"""
UPDATE quotation.material_requests AS material_request
SET
    current_assignment_id = %s,
    assigned_to = %s,
    workflow_status = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE material_request.id = %s
RETURNING
    {_MATERIAL_REQUEST_COLUMNS};
"""


_CLEAR_ASSIGNMENT_CONTEXT_SQL = f"""
UPDATE quotation.material_requests AS material_request
SET
    current_assignment_id = NULL,
    assigned_to = NULL,
    workflow_status = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE material_request.id = %s
RETURNING
    {_MATERIAL_REQUEST_COLUMNS};
"""


_UPDATE_WORKFLOW_STATUS_SQL = f"""
UPDATE quotation.material_requests AS material_request
SET
    workflow_status = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE material_request.id = %s
RETURNING
    {_MATERIAL_REQUEST_COLUMNS};
"""


class MaterialRequestRepository(BaseRepository):
    """PostgreSQL repository for Material Request records."""

    @staticmethod
    def _map_material_request_row(
        row: tuple[Any, ...] | None,
    ) -> dict[str, Any] | None:
        if row is None:
            return None

        return {
            "id": row[0],
            "request_no": row[1],
            "project_id": row[2],
            "request_description": row[3],
            "requested_by": row[4],
            "requested_by_user_id": row[5],
            "assigned_to": row[6],
            "priority": row[7],
            "status": row[8],
            "due_date": row[9],
            "remarks": row[10],
            "folder_name": row[11],
            "created_by": row[12],
            "created_at": row[13],
            "updated_at": row[14],
            "material_request_description": row[15],
            "mr_number": row[16],
            "locked_by": row[17],
            "locked_at": row[18],
            "lock_expires_at": row[19],
            "workflow_status": row[20],
            "current_assignment_id": row[21],
        }

    @staticmethod
    def _status_value(status: Any) -> str:
        return (
            status.value
            if hasattr(status, "value")
            else str(status)
        )

    @classmethod
    def get_by_id(
        cls,
        material_request_id: UUID,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        row = cls.fetch_one(
            _GET_BY_ID_SQL,
            (material_request_id,),
            cursor=cursor,
        )

        return cls._map_material_request_row(
            row
        )

    @classmethod
    def update_assignment_context(
        cls,
        material_request_id: UUID,
        assignment_id: UUID,
        assigned_to: UUID | str,
        workflow_status: Any,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Update the assignment pointer, assignee, workflow status, and the
        legacy status used by the current Quotation Monitoring UI.
        """
        status_value = cls._status_value(
            workflow_status
        )

        row = cls.execute_returning(
            _UPDATE_ASSIGNMENT_CONTEXT_SQL,
            (
                assignment_id,
                str(assigned_to),
                status_value,
                status_value,
                material_request_id,
            ),
            cursor=cursor,
        )

        return cls._map_material_request_row(
            row
        )

    @classmethod
    def clear_assignment_context(
        cls,
        material_request_id: UUID,
        workflow_status: Any,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        status_value = cls._status_value(
            workflow_status
        )

        row = cls.execute_returning(
            _CLEAR_ASSIGNMENT_CONTEXT_SQL,
            (
                status_value,
                status_value,
                material_request_id,
            ),
            cursor=cursor,
        )

        return cls._map_material_request_row(
            row
        )

    @classmethod
    def update_workflow_status(
        cls,
        material_request_id: UUID,
        workflow_status: Any,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        status_value = cls._status_value(
            workflow_status
        )

        row = cls.execute_returning(
            _UPDATE_WORKFLOW_STATUS_SQL,
            (
                status_value,
                status_value,
                material_request_id,
            ),
            cursor=cursor,
        )

        return cls._map_material_request_row(
            row
        )