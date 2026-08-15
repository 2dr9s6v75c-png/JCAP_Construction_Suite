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


_GET_AUTO_ASSIGNMENT_CANDIDATES_SQL = f"""
SELECT
    {_MATERIAL_REQUEST_COLUMNS},
    EXTRACT(
        EPOCH FROM (
            CURRENT_TIMESTAMP - material_request.created_at
        )
    ) / 60.0 AS age_minutes
FROM quotation.material_requests AS material_request
WHERE material_request.status = 'New'
  AND material_request.workflow_status = 'Submitted'
  AND material_request.assigned_to IS NULL
  AND material_request.current_assignment_id IS NULL
  AND material_request.created_at <= (
        CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
  )
ORDER BY
    material_request.created_at ASC,
    material_request.id ASC;
"""


_CLAIM_NEXT_AUTO_ASSIGNMENT_CANDIDATE_SQL = f"""
SELECT
    {_MATERIAL_REQUEST_COLUMNS},
    EXTRACT(
        EPOCH FROM (
            CURRENT_TIMESTAMP - material_request.created_at
        )
    ) / 60.0 AS age_minutes
FROM quotation.material_requests AS material_request
WHERE material_request.status = 'New'
  AND material_request.workflow_status = 'Submitted'
  AND material_request.assigned_to IS NULL
  AND material_request.current_assignment_id IS NULL
  AND material_request.created_at <= (
        CURRENT_TIMESTAMP - (%s * INTERVAL '1 minute')
  )
ORDER BY
    material_request.created_at ASC,
    material_request.id ASC
FOR UPDATE OF material_request SKIP LOCKED
LIMIT 1;
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
    def get_auto_assignment_candidates(
        cls,
        threshold_minutes: int,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        """
        Return New, unassigned Material Requests whose age meets or exceeds
        the supplied auto-assignment threshold.

        This is a read-only query. It does not lock or modify records.
        PostgreSQL CURRENT_TIMESTAMP is used as the authoritative clock.
        """
        try:
            normalized_threshold = int(threshold_minutes)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Auto-assignment threshold must be a positive integer."
            ) from exc

        if normalized_threshold < 1:
            raise ValueError(
                "Auto-assignment threshold must be at least 1 minute."
            )

        rows = cls.fetch_all(
            _GET_AUTO_ASSIGNMENT_CANDIDATES_SQL,
            (normalized_threshold,),
            cursor=cursor,
        )

        candidates: list[dict[str, Any]] = []

        for row in rows:
            mapped = cls._map_material_request_row(
                row[:22]
            )

            if mapped is None:
                continue

            try:
                age_minutes = float(row[22])
            except (TypeError, ValueError):
                age_minutes = 0.0

            mapped["age_minutes"] = age_minutes
            candidates.append(mapped)

        return candidates

    @classmethod
    def claim_next_auto_assignment_candidate(
        cls,
        threshold_minutes: int,
        *,
        cursor,
    ) -> dict[str, Any] | None:
        """
        Lock and return the oldest Material Request currently eligible for
        auto-assignment.

        This method must be called inside a caller-owned transaction.
        FOR UPDATE SKIP LOCKED prevents two worker instances from claiming
        the same Material Request concurrently.
        """
        if cursor is None:
            raise ValueError(
                "A shared transaction cursor is required to claim "
                "an auto-assignment candidate."
            )

        try:
            normalized_threshold = int(threshold_minutes)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Auto-assignment threshold must be a positive integer."
            ) from exc

        if normalized_threshold < 1:
            raise ValueError(
                "Auto-assignment threshold must be at least 1 minute."
            )

        cursor.execute(
            _CLAIM_NEXT_AUTO_ASSIGNMENT_CANDIDATE_SQL,
            (normalized_threshold,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        mapped = cls._map_material_request_row(
            row[:22]
        )

        if mapped is None:
            return None

        try:
            mapped["age_minutes"] = float(row[22])
        except (TypeError, ValueError):
            mapped["age_minutes"] = 0.0

        return mapped

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