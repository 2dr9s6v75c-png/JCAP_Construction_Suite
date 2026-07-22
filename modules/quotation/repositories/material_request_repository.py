"""
Material Request Repository.

Purpose:
    Provide PostgreSQL persistence operations for material-request records.

Responsibilities:
    - Retrieve material-request records.
    - Update assignment linkage and assignee context.
    - Clear assignment linkage and assignee context.
    - Persist material-request workflow status.
    - Map raw PostgreSQL rows into dictionaries.
    - Support standalone operations and shared transactions.

Restrictions:
    - No assignment-history persistence.
    - No permission validation.
    - No workflow-transition validation.
    - No notifications.
    - No activity logging.
    - No UI logic.
    - No business-process coordination.

Engineering standards:
    ES-001 - Repository Isolation
    ES-002 - No Magic Strings
    ES-007 - UUID Everywhere
    ES-009 - Stable Public APIs
    ES-011 - SQL Constants
    ES-012 - Centralized Row Mapping
    ES-014 - Repository Template Standard
    ES-020 - Database Ownership
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
    updated_at = CURRENT_TIMESTAMP
WHERE material_request.id = %s
RETURNING
    {_MATERIAL_REQUEST_COLUMNS};
"""


_UPDATE_WORKFLOW_STATUS_SQL = f"""
UPDATE quotation.material_requests AS material_request
SET
    workflow_status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE material_request.id = %s
RETURNING
    {_MATERIAL_REQUEST_COLUMNS};
"""


class MaterialRequestRepository(BaseRepository):
    """
    PostgreSQL repository for material requests.

    When cursor is supplied, the caller owns commit and rollback.
    When cursor is not supplied, BaseRepository owns the transaction.
    """

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
            "assigned_to": row[5],
            "priority": row[6],
            "status": row[7],
            "due_date": row[8],
            "remarks": row[9],
            "folder_name": row[10],
            "created_by": row[11],
            "created_at": row[12],
            "updated_at": row[13],
            "material_request_description": row[14],
            "mr_number": row[15],
            "locked_by": row[16],
            "locked_at": row[17],
            "lock_expires_at": row[18],
            "workflow_status": row[19],
            "current_assignment_id": row[20],
        }

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
        return cls._map_material_request_row(row)

    @classmethod
    def update_assignment_context(
        cls,
        material_request_id: UUID,
        assignment_id: UUID,
        assigned_to: str,
        workflow_status: str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Atomically update current assignment, assignee, and workflow status.
        """
        row = cls.execute_returning(
            _UPDATE_ASSIGNMENT_CONTEXT_SQL,
            (
                assignment_id,
                assigned_to,
                workflow_status,
                material_request_id,
            ),
            cursor=cursor,
        )
        return cls._map_material_request_row(row)

    @classmethod
    def clear_assignment_context(
        cls,
        material_request_id: UUID,
        workflow_status: str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Clear current assignment and assignee, then set workflow status.
        """
        row = cls.execute_returning(
            _CLEAR_ASSIGNMENT_CONTEXT_SQL,
            (
                workflow_status,
                material_request_id,
            ),
            cursor=cursor,
        )
        return cls._map_material_request_row(row)

    @classmethod
    def update_workflow_status(
        cls,
        material_request_id: UUID,
        workflow_status: str,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Update workflow_status without changing lifecycle status.
        """
        row = cls.execute_returning(
            _UPDATE_WORKFLOW_STATUS_SQL,
            (
                workflow_status,
                material_request_id,
            ),
            cursor=cursor,
        )
        return cls._map_material_request_row(row)