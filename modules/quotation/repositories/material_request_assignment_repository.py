"""
Material Request Assignment Repository.

Purpose:
    Provide PostgreSQL persistence operations for material-request
    assignment records.

Responsibilities:
    - Create assignment-history records.
    - Retrieve assignment records and history.
    - Persist assignment lifecycle timestamps and statuses.
    - Map raw PostgreSQL rows into dictionaries.
    - Support standalone operations and shared transactions.

Restrictions:
    - No permission validation.
    - No workflow-transition validation.
    - No notifications.
    - No activity logging.
    - No UI logic.
    - No cross-domain table updates.
    - No business-process coordination.

Engineering standards:
    ES-001 - Repository Isolation
    ES-002 - No Magic Strings
    ES-003 - Immutable Business History
    ES-004 - Soft Delete by Default
    ES-007 - UUID Everywhere
    ES-009 - Stable Public APIs
    ES-011 - SQL Constants
    ES-012 - Centralized Row Mapping
    ES-014 - Repository Template Standard
    ES-018 - Explicit Result Ordering
    ES-020 - Database Ownership
"""

# =============================================================================
# Imports
# =============================================================================

from typing import Any
from uuid import UUID

from core.database.repositories.base_repository import BaseRepository


# =============================================================================
# SQL Constants
# =============================================================================

_ASSIGNMENT_COLUMNS = """
    assignment.id,
    assignment.material_request_id,
    assignment.assigned_to,
    assignment.assigned_by,
    assignment.assignment_status,
    assignment.assigned_at,
    assignment.accepted_at,
    assignment.started_at,
    assignment.completed_at,
    assignment.ended_at,
    assignment.remarks,
    assignment.created_at,
    assignment.updated_at
"""


_GET_BY_ID_SQL = f"""
SELECT
    {_ASSIGNMENT_COLUMNS}
FROM quotation.material_request_assignments AS assignment
WHERE assignment.id = %s;
"""


_GET_CURRENT_ASSIGNMENT_SQL = f"""
SELECT
    {_ASSIGNMENT_COLUMNS}
FROM quotation.material_requests AS material_request
INNER JOIN quotation.material_request_assignments AS assignment
    ON assignment.id = material_request.current_assignment_id
WHERE material_request.id = %s;
"""


_GET_ASSIGNMENT_HISTORY_SQL = f"""
SELECT
    {_ASSIGNMENT_COLUMNS}
FROM quotation.material_request_assignments AS assignment
WHERE assignment.material_request_id = %s
ORDER BY
    assignment.assigned_at DESC,
    assignment.created_at DESC,
    assignment.id DESC;
"""


_GET_ACTIVE_ASSIGNMENT_SQL = f"""
SELECT
    {_ASSIGNMENT_COLUMNS}
FROM quotation.material_request_assignments AS assignment
WHERE assignment.material_request_id = %s
  AND assignment.ended_at IS NULL
ORDER BY
    assignment.assigned_at DESC,
    assignment.created_at DESC,
    assignment.id DESC
LIMIT 1;
"""


_HAS_ACTIVE_ASSIGNMENT_SQL = """
SELECT EXISTS (
    SELECT 1
    FROM quotation.material_request_assignments AS assignment
    WHERE assignment.material_request_id = %s
      AND assignment.ended_at IS NULL
);
"""


_GET_OFFICER_WORKLOAD_SQL = """
SELECT
    COUNT(*)
FROM quotation.material_request_assignments AS assignment
WHERE assignment.assigned_to = %s
  AND assignment.ended_at IS NULL;
"""


_CREATE_ASSIGNMENT_SQL = """
INSERT INTO quotation.material_request_assignments (
    material_request_id,
    assigned_to,
    assigned_by,
    assignment_status,
    remarks
)
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s
)
RETURNING id;
"""


_ACCEPT_ASSIGNMENT_SQL = f"""
UPDATE quotation.material_request_assignments AS assignment
SET
    assignment_status = %s,
    accepted_at = COALESCE(assignment.accepted_at, CURRENT_TIMESTAMP),
    remarks = COALESCE(%s, assignment.remarks),
    updated_at = CURRENT_TIMESTAMP
WHERE assignment.id = %s
  AND assignment.ended_at IS NULL
RETURNING
    {_ASSIGNMENT_COLUMNS};
"""


_MARK_IN_PROGRESS_SQL = f"""
UPDATE quotation.material_request_assignments AS assignment
SET
    assignment_status = %s,
    started_at = COALESCE(assignment.started_at, CURRENT_TIMESTAMP),
    remarks = COALESCE(%s, assignment.remarks),
    updated_at = CURRENT_TIMESTAMP
WHERE assignment.id = %s
  AND assignment.ended_at IS NULL
RETURNING
    {_ASSIGNMENT_COLUMNS};
"""


_COMPLETE_ASSIGNMENT_SQL = f"""
UPDATE quotation.material_request_assignments AS assignment
SET
    assignment_status = %s,
    completed_at = COALESCE(
        assignment.completed_at,
        CURRENT_TIMESTAMP
    ),
    ended_at = COALESCE(
        assignment.ended_at,
        CURRENT_TIMESTAMP
    ),
    remarks = COALESCE(%s, assignment.remarks),
    updated_at = CURRENT_TIMESTAMP
WHERE assignment.id = %s
  AND assignment.ended_at IS NULL
RETURNING
    {_ASSIGNMENT_COLUMNS};
"""


_REASSIGN_ASSIGNMENT_SQL = f"""
UPDATE quotation.material_request_assignments AS assignment
SET
    assignment_status = %s,
    ended_at = COALESCE(
        assignment.ended_at,
        CURRENT_TIMESTAMP
    ),
    remarks = COALESCE(%s, assignment.remarks),
    updated_at = CURRENT_TIMESTAMP
WHERE assignment.id = %s
  AND assignment.ended_at IS NULL
RETURNING
    {_ASSIGNMENT_COLUMNS};
"""


_CANCEL_ASSIGNMENT_SQL = f"""
UPDATE quotation.material_request_assignments AS assignment
SET
    assignment_status = %s,
    ended_at = COALESCE(
        assignment.ended_at,
        CURRENT_TIMESTAMP
    ),
    remarks = COALESCE(%s, assignment.remarks),
    updated_at = CURRENT_TIMESTAMP
WHERE assignment.id = %s
  AND assignment.ended_at IS NULL
RETURNING
    {_ASSIGNMENT_COLUMNS};
"""


# =============================================================================
# Repository
# =============================================================================


class MaterialRequestAssignmentRepository(BaseRepository):
    """
    PostgreSQL repository for material-request assignments.

    Transaction ownership:
        When cursor is supplied, the caller owns commit and rollback.

        When cursor is not supplied, BaseRepository manages the connection
        and transaction.

    Public return conventions:
        - Created assignment: UUID
        - Retrieved assignment: dict | None
        - Assignment history: list[dict]
        - Existence result: bool
        - Workload result: int
        - Lifecycle update: dict | None
    """

    # -------------------------------------------------------------------------
    # Row Mapping
    # -------------------------------------------------------------------------

    @staticmethod
    def _map_assignment_row(
        row: tuple[Any, ...] | None,
    ) -> dict[str, Any] | None:
        """
        Convert one raw PostgreSQL assignment row into a dictionary.

        Args:
            row:
                Raw row returned by BaseRepository.

        Returns:
            Mapped assignment dictionary, or None when no row exists.
        """
        if row is None:
            return None

        return {
            "id": row[0],
            "material_request_id": row[1],
            "assigned_to": row[2],
            "assigned_by": row[3],
            "assignment_status": row[4],
            "assigned_at": row[5],
            "accepted_at": row[6],
            "started_at": row[7],
            "completed_at": row[8],
            "ended_at": row[9],
            "remarks": row[10],
            "created_at": row[11],
            "updated_at": row[12],
        }

    @classmethod
    def _map_assignment_rows(
        cls,
        rows: list[tuple[Any, ...]],
    ) -> list[dict[str, Any]]:
        """
        Convert raw PostgreSQL assignment rows into dictionaries.

        Args:
            rows:
                Raw rows returned by BaseRepository.

        Returns:
            List of mapped assignment dictionaries.
        """
        mapped_rows: list[dict[str, Any]] = []

        for row in rows:
            mapped_row = cls._map_assignment_row(row)

            if mapped_row is not None:
                mapped_rows.append(mapped_row)

        return mapped_rows

    # -------------------------------------------------------------------------
    # Read Operations
    # -------------------------------------------------------------------------

    @classmethod
    def get_by_id(
        cls,
        assignment_id: UUID,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Retrieve an assignment using its UUID.

        Args:
            assignment_id:
                Assignment UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Assignment dictionary when found; otherwise None.
        """
        row = cls.fetch_one(
            _GET_BY_ID_SQL,
            (assignment_id,),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def get_current_assignment(
        cls,
        material_request_id: UUID,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Retrieve the assignment referenced by current_assignment_id.

        Args:
            material_request_id:
                Material-request UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Current assignment dictionary when linked; otherwise None.
        """
        row = cls.fetch_one(
            _GET_CURRENT_ASSIGNMENT_SQL,
            (material_request_id,),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def get_assignment_history(
        cls,
        material_request_id: UUID,
        *,
        cursor=None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve complete assignment history for a material request.

        Results are explicitly ordered from newest to oldest.

        Args:
            material_request_id:
                Material-request UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            List of assignment dictionaries.
        """
        rows = cls.fetch_all(
            _GET_ASSIGNMENT_HISTORY_SQL,
            (material_request_id,),
            cursor=cursor,
        )

        return cls._map_assignment_rows(rows)

    @classmethod
    def get_active_assignment(
        cls,
        material_request_id: UUID,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Retrieve the newest assignment where ended_at is NULL.

        This is a persistence-level query only. It does not interpret
        assignment workflow rules.

        Args:
            material_request_id:
                Material-request UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Active assignment dictionary when found; otherwise None.
        """
        row = cls.fetch_one(
            _GET_ACTIVE_ASSIGNMENT_SQL,
            (material_request_id,),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def has_active_assignment(
        cls,
        material_request_id: UUID,
        *,
        cursor=None,
    ) -> bool:
        """
        Check whether a material request has a non-ended assignment.

        Args:
            material_request_id:
                Material-request UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            True when a row with ended_at IS NULL exists.
        """
        return cls.exists(
            _HAS_ACTIVE_ASSIGNMENT_SQL,
            (material_request_id,),
            cursor=cursor,
        )

    @classmethod
    def get_officer_workload(
        cls,
        officer_id: UUID,
        *,
        cursor=None,
    ) -> int:
        """
        Count an officer's non-ended assignments.

        Workload-limit decisions belong in the Service layer.

        Args:
            officer_id:
                Purchasing-officer UUID.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Number of non-ended assignments for the officer.
        """
        return cls.count(
            _GET_OFFICER_WORKLOAD_SQL,
            (officer_id,),
            cursor=cursor,
        )

    # -------------------------------------------------------------------------
    # Write Operations
    # -------------------------------------------------------------------------

    @classmethod
    def create_assignment(
        cls,
        material_request_id: UUID,
        assigned_to: UUID,
        assigned_by: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> UUID:
        """
        Create a material-request assignment-history record.

        This operation modifies only:

            quotation.material_request_assignments

        It does not update:

            quotation.material_requests.current_assignment_id
            quotation.material_requests.assigned_to
            quotation.material_requests.workflow_status

        Cross-table coordination belongs in the Process layer.

        Args:
            material_request_id:
                Material request receiving the assignment.

            assigned_to:
                Purchasing officer receiving the assignment.

            assigned_by:
                User creating the assignment.

            assignment_status:
                Initial status supplied by the Service layer.

            remarks:
                Optional assignment remarks.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            UUID of the newly created assignment.

        Raises:
            RuntimeError:
                When PostgreSQL does not return the inserted UUID.
        """
        row = cls.execute_returning(
            _CREATE_ASSIGNMENT_SQL,
            (
                material_request_id,
                assigned_to,
                assigned_by,
                assignment_status,
                remarks,
            ),
            cursor=cursor,
        )

        if row is None or row[0] is None:
            raise RuntimeError(
                "PostgreSQL did not return the created assignment ID."
            )

        return row[0]

    @classmethod
    def accept_assignment(
        cls,
        assignment_id: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Persist acceptance of a non-ended assignment.

        The original accepted_at timestamp is preserved when the method is
        called more than once. The Service layer is responsible for deciding
        whether acceptance is allowed.

        Args:
            assignment_id:
                Assignment UUID.

            assignment_status:
                Accepted status supplied through centralized constants.

            remarks:
                Optional replacement remarks. When None, existing remarks
                are preserved.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Updated assignment dictionary, or None when no non-ended record
            matched the supplied UUID.
        """
        row = cls.execute_returning(
            _ACCEPT_ASSIGNMENT_SQL,
            (
                assignment_status,
                remarks,
                assignment_id,
            ),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def mark_in_progress(
        cls,
        assignment_id: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Persist the start of work on a non-ended assignment.

        The original started_at timestamp is preserved when this method is
        called more than once.

        Args:
            assignment_id:
                Assignment UUID.

            assignment_status:
                In-progress status supplied through centralized constants.

            remarks:
                Optional replacement remarks. When None, existing remarks
                are preserved.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Updated assignment dictionary, or None when no non-ended record
            matched the supplied UUID.
        """
        row = cls.execute_returning(
            _MARK_IN_PROGRESS_SQL,
            (
                assignment_status,
                remarks,
                assignment_id,
            ),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def complete_assignment(
        cls,
        assignment_id: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Persist completion and closure of a non-ended assignment.

        Both completed_at and ended_at are populated. Existing timestamps
        are preserved when already present.

        Args:
            assignment_id:
                Assignment UUID.

            assignment_status:
                Completed status supplied through centralized constants.

            remarks:
                Optional replacement remarks. When None, existing remarks
                are preserved.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Updated assignment dictionary, or None when no non-ended record
            matched the supplied UUID.
        """
        row = cls.execute_returning(
            _COMPLETE_ASSIGNMENT_SQL,
            (
                assignment_status,
                remarks,
                assignment_id,
            ),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def reassign_assignment(
        cls,
        assignment_id: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Close an existing assignment because it is being reassigned.

        This method does not create the replacement assignment. Creating the
        replacement record and updating the material-request pointer belong
        to the Assignment Process inside one shared transaction.

        Args:
            assignment_id:
                Assignment UUID being closed.

            assignment_status:
                Reassigned status supplied through centralized constants.

            remarks:
                Optional replacement remarks. When None, existing remarks
                are preserved.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Updated closed assignment dictionary, or None when no non-ended
            record matched the supplied UUID.
        """
        row = cls.execute_returning(
            _REASSIGN_ASSIGNMENT_SQL,
            (
                assignment_status,
                remarks,
                assignment_id,
            ),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)

    @classmethod
    def cancel_assignment(
        cls,
        assignment_id: UUID,
        assignment_status: str,
        remarks: str | None = None,
        *,
        cursor=None,
    ) -> dict[str, Any] | None:
        """
        Persist cancellation and closure of a non-ended assignment.

        Args:
            assignment_id:
                Assignment UUID.

            assignment_status:
                Cancelled status supplied through centralized constants.

            remarks:
                Optional replacement remarks. When None, existing remarks
                are preserved.

            cursor:
                Optional shared PostgreSQL cursor.

        Returns:
            Updated cancelled assignment dictionary, or None when no
            non-ended record matched the supplied UUID.
        """
        row = cls.execute_returning(
            _CANCEL_ASSIGNMENT_SQL,
            (
                assignment_status,
                remarks,
                assignment_id,
            ),
            cursor=cursor,
        )

        return cls._map_assignment_row(row)