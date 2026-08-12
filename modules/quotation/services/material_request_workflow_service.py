"""
JCAP Construction Suite
Material Request Workflow Service

Centralizes Phase 1 Material Request status transitions.
Participates in the caller's existing transaction.
"""

from typing import Any

from core.logging.activity_logger import ActivityLogger
from core.realtime.realtime_event_service import RealtimeEventService
from core.workflow.material_request_workflow import MaterialRequestState
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)


class MaterialRequestWorkflowService:
    BLOCKING_CLARIFICATION_STATUSES = (
        "Awaiting Engineering Response",
        "Response Ready",
        "Forwarded to Supplier",
    )

    def __init__(self, repository=None):
        self._repository = repository or MaterialRequestRepository()

    # ========================================================
    # ASSIGNED -> IN PROGRESS
    # ========================================================

    def start_purchasing_work(
        self,
        material_request_id,
        current_user: dict[str, Any],
        *,
        trigger: str,
        cursor,
    ) -> bool:
        if cursor is None:
            raise ValueError(
                "An active transaction cursor is required."
            )

        user_id = self._require_user_id(
            current_user
        )

        row = self._get_material_request_for_update(
            material_request_id,
            cursor=cursor,
        )

        if row is None:
            raise ValueError(
                "Material Request not found."
            )

        (
            mr_id,
            mr_number,
            status,
            workflow_status,
            assigned_to,
        ) = row

        if not assigned_to:
            raise ValueError(
                "Material Request must be assigned before "
                "Purchasing work can begin."
            )

        if str(assigned_to) != str(user_id):
            raise PermissionError(
                "Only the Purchasing Officer assigned to this "
                "Material Request may start Purchasing work."
            )

        current_status = str(
            workflow_status
            or status
            or ""
        ).strip()

        if (
            current_status
            != MaterialRequestState.ASSIGNED
        ):
            return False

        self._change_status(
            material_request_id=mr_id,
            mr_number=mr_number,
            previous_status=MaterialRequestState.ASSIGNED,
            new_status=MaterialRequestState.IN_PROGRESS,
            user_id=user_id,
            trigger=trigger,
            cursor=cursor,
        )

        return True

    # ========================================================
    # IN PROGRESS -> WAITING SUPPLIER QUOTE
    # ========================================================

    def evaluate_waiting_supplier_quote(
        self,
        material_request_id,
        current_user: dict[str, Any],
        *,
        trigger: str,
        cursor,
    ) -> bool:
        if cursor is None:
            raise ValueError(
                "An active transaction cursor is required."
            )

        user_id = self._require_user_id(
            current_user
        )

        row = self._get_material_request_for_update(
            material_request_id,
            cursor=cursor,
        )

        if row is None:
            raise ValueError(
                "Material Request not found."
            )

        (
            mr_id,
            mr_number,
            status,
            workflow_status,
            assigned_to,
        ) = row

        if not assigned_to:
            return False

        if str(assigned_to) != str(user_id):
            raise PermissionError(
                "Only the Purchasing Officer assigned to this "
                "Material Request may advance the Purchasing workflow."
            )

        current_status = str(
            workflow_status
            or status
            or ""
        ).strip()

        if (
            current_status
            != MaterialRequestState.IN_PROGRESS
        ):
            return False

        if not self._has_active_supplier_quotation(
            mr_id,
            cursor=cursor,
        ):
            return False

        if self._has_blocking_clarification(
            mr_id,
            cursor=cursor,
        ):
            return False

        self._change_status(
            material_request_id=mr_id,
            mr_number=mr_number,
            previous_status=MaterialRequestState.IN_PROGRESS,
            new_status=MaterialRequestState.WAITING_SUPPLIER_QUOTE,
            user_id=user_id,
            trigger=trigger,
            cursor=cursor,
        )

        return True

    # ========================================================
    # WAITING SUPPLIER QUOTE -> COMPLETED
    # ========================================================

    def evaluate_completed(
        self,
        material_request_id,
        current_user: dict[str, Any],
        *,
        trigger: str,
        cursor,
    ) -> bool:
        """
        Complete the MR only when every active Supplier Quotation
        has at least one registered quotation file.

        Returns True only when a transition occurs.
        """
        if cursor is None:
            raise ValueError(
                "An active transaction cursor is required."
            )

        user_id = self._require_user_id(
            current_user
        )

        row = self._get_material_request_for_update(
            material_request_id,
            cursor=cursor,
        )

        if row is None:
            raise ValueError(
                "Material Request not found."
            )

        (
            mr_id,
            mr_number,
            status,
            workflow_status,
            assigned_to,
        ) = row

        if not assigned_to:
            return False

        if str(assigned_to) != str(user_id):
            raise PermissionError(
                "Only the Purchasing Officer assigned to this "
                "Material Request may complete the Purchasing workflow."
            )

        current_status = str(
            workflow_status
            or status
            or ""
        ).strip()

        if (
            current_status
            != MaterialRequestState.WAITING_SUPPLIER_QUOTE
        ):
            return False

        if not self._all_active_quotations_have_files(
            mr_id,
            cursor=cursor,
        ):
            return False

        self._change_status(
            material_request_id=mr_id,
            mr_number=mr_number,
            previous_status=MaterialRequestState.WAITING_SUPPLIER_QUOTE,
            new_status=MaterialRequestState.COMPLETED,
            user_id=user_id,
            trigger=trigger,
            cursor=cursor,
        )

        return True

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _get_material_request_for_update(
        material_request_id,
        *,
        cursor,
    ):
        cursor.execute(
            """
            SELECT
                id,
                mr_number,
                status,
                workflow_status,
                assigned_to
            FROM quotation.material_requests
            WHERE id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        return cursor.fetchone()

    @staticmethod
    def _has_active_supplier_quotation(
        material_request_id,
        *,
        cursor,
    ) -> bool:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM quotation.supplier_quotations
                WHERE material_request_id = %s
                  AND is_archived = FALSE
            )
            """,
            (material_request_id,),
        )

        row = cursor.fetchone()

        return bool(
            row
            and row[0]
        )

    @classmethod
    def _has_blocking_clarification(
        cls,
        material_request_id,
        *,
        cursor,
    ) -> bool:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM quotation.clarifications
                WHERE material_request_id = %s
                  AND status = ANY(%s)
            )
            """,
            (
                material_request_id,
                list(
                    cls.BLOCKING_CLARIFICATION_STATUSES
                ),
            ),
        )

        row = cursor.fetchone()

        return bool(
            row
            and row[0]
        )

    @staticmethod
    def _all_active_quotations_have_files(
        material_request_id,
        *,
        cursor,
    ) -> bool:
        """
        True only when:
        - at least one active Supplier Quotation exists, and
        - every active Supplier Quotation has at least one file row.
        """
        cursor.execute(
            """
            SELECT
                COUNT(*) AS active_quotation_count,
                COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1
                        FROM quotation.supplier_quotation_files sqf
                        WHERE sqf.supplier_quotation_id = sq.id
                    )
                ) AS quotations_with_files
            FROM quotation.supplier_quotations sq
            WHERE sq.material_request_id = %s
              AND sq.is_archived = FALSE
            """,
            (material_request_id,),
        )

        row = cursor.fetchone()

        if not row:
            return False

        active_count = int(
            row[0] or 0
        )

        with_files = int(
            row[1] or 0
        )

        return (
            active_count > 0
            and active_count == with_files
        )

    def _change_status(
        self,
        *,
        material_request_id,
        mr_number,
        previous_status,
        new_status,
        user_id,
        trigger,
        cursor,
    ):
        updated = (
            self._repository.update_workflow_status(
                material_request_id,
                new_status,
                cursor=cursor,
            )
        )

        if updated is None:
            raise ValueError(
                "Material Request status could not be updated."
            )

        clean_trigger = str(
            trigger
            or "Workflow condition satisfied"
        ).strip()

        ActivityLogger.log(
            cursor,
            user_id=user_id,
            action=ActivityLogger.ACTION_STATUS_CHANGE,
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=(
                f"Material Request {mr_number} moved from "
                f"{previous_status} to {new_status}. "
                f"Trigger: {clean_trigger}."
            ),
        )

        RealtimeEventService.publish(
            "material_request_status_changed",
            entity_type="material_request",
            entity_id=material_request_id,
            action="status_changed",
            actor_user_id=user_id,
            data={
                "mr_number": mr_number,
                "previous_status": previous_status,
                "new_status": new_status,
                "trigger": clean_trigger,
            },
            cursor=cursor,
        )

    @staticmethod
    def _require_user_id(
        user,
    ):
        if not user or not user.get("id"):
            raise ValueError(
                "Authenticated user is required."
            )

        return user["id"]
