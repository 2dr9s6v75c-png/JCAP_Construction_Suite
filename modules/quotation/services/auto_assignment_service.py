"""
JCAP Construction Suite
Auto Assignment Service

Patch 2B: read-only recommendation plus transactional auto-assignment.

The write path rechecks eligibility inside PostgreSQL, locks the candidate
row, assigns the least-loaded active Purchasing Officer, updates Material
Request state, writes an AUTO ASSIGN activity, creates dedicated automatic
assignment notifications, and publishes a realtime event in one transaction.
"""

from __future__ import annotations

from typing import Any

from core.database.transaction_manager import TransactionManager
from core.logging.activity_logger import ActivityLogger
from core.notifications.persistent_notification_service import (
    PersistentNotificationService,
)
from core.organization.organization_service import OrganizationService
from core.realtime.realtime_event_service import RealtimeEventService
from core.workflow.material_request_workflow import MaterialRequestState
from modules.quotation.repositories.material_request_repository import (
    MaterialRequestRepository,
)
from modules.quotation.services.material_request_assignment_service import (
    MaterialRequestAssignmentService,
)


class AutoAssignmentService:
    """Read-only Auto Assignment candidate and recommendation service."""

    PURCHASING_OFFICER_ROLE = "Purchasing Officer"
    AUTOMATION_USERNAME = "jcap_auto_assignment"

    def __init__(
        self,
        *,
        material_request_repository: MaterialRequestRepository | None = None,
        assignment_service: MaterialRequestAssignmentService | None = None,
        transaction_factory=None,
    ) -> None:
        self._material_request_repository = (
            material_request_repository or MaterialRequestRepository()
        )
        self._assignment_service = (
            assignment_service or MaterialRequestAssignmentService()
        )
        self._transaction_factory = (
            transaction_factory or TransactionManager
        )

    @staticmethod
    def _normalize_threshold_minutes(value: int) -> int:
        try:
            minutes = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Auto-assignment threshold must be a positive integer."
            ) from exc

        if minutes < 1:
            raise ValueError(
                "Auto-assignment threshold must be at least 1 minute."
            )

        return minutes

    def get_eligible_material_requests(
        self,
        threshold_minutes: int = 60,
    ) -> list[dict[str, Any]]:
        """
        Return New and unassigned Material Requests that have reached the
        auto-assignment threshold.

        PostgreSQL server time is used by the repository query.
        """
        threshold_minutes = self._normalize_threshold_minutes(
            threshold_minutes
        )

        return self._material_request_repository.get_auto_assignment_candidates(
            threshold_minutes
        )

    def get_active_purchasing_officer_workloads(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return active Purchasing Officers and their current non-ended
        assignment counts.

        Sorting is deterministic:
        1. lowest active workload
        2. full name
        3. username
        4. user id
        """
        officers = OrganizationService.get_active_users_by_role(
            self.PURCHASING_OFFICER_ROLE
        )

        workloads: list[dict[str, Any]] = []

        for officer in officers:
            officer_id = officer.get("id")

            if not officer_id:
                continue

            workload = self._assignment_service.get_officer_workload(
                officer_id
            )

            workloads.append(
                {
                    "id": officer_id,
                    "username": officer.get("username") or "",
                    "full_name": (
                        officer.get("full_name")
                        or officer.get("username")
                        or str(officer_id)
                    ),
                    "active_workload": int(workload or 0),
                }
            )

        workloads.sort(
            key=lambda item: (
                item["active_workload"],
                str(item["full_name"]).lower(),
                str(item["username"]).lower(),
                str(item["id"]),
            )
        )

        return workloads

    def _get_automation_user(self) -> dict[str, Any]:
        automation_user = OrganizationService.get_user_by_username(
            self.AUTOMATION_USERNAME
        )

        if not automation_user:
            raise ValueError(
                "JCAP Auto Assignment account was not found. "
                f"Create the active user '{self.AUTOMATION_USERNAME}' "
                "before running automatic assignment."
            )

        if not automation_user.get("is_active", True):
            raise ValueError(
                "JCAP Auto Assignment account is disabled."
            )

        return automation_user

    def _get_least_loaded_officer_in_transaction(
        self,
        *,
        cursor,
    ) -> dict[str, Any] | None:
        officers = OrganizationService.get_active_users_by_role(
            self.PURCHASING_OFFICER_ROLE
        )

        ranked: list[dict[str, Any]] = []

        for officer in officers:
            officer_id = officer.get("id")

            if not officer_id:
                continue

            workload = self._assignment_service.get_officer_workload(
                officer_id,
                cursor=cursor,
            )

            ranked.append(
                {
                    **officer,
                    "active_workload": int(workload or 0),
                }
            )

        if not ranked:
            return None

        ranked.sort(
            key=lambda officer: (
                officer["active_workload"],
                str(
                    officer.get("full_name")
                    or officer.get("username")
                    or ""
                ).lower(),
                str(officer.get("username") or "").lower(),
                str(officer.get("id") or ""),
            )
        )

        return ranked[0]

    def auto_assign_next(
        self,
        threshold_minutes: int = 60,
    ) -> dict[str, Any] | None:
        """
        Auto-assign the oldest eligible Material Request atomically.

        Returns None when there is currently nothing eligible.
        """
        threshold_minutes = self._normalize_threshold_minutes(
            threshold_minutes
        )
        automation_user = self._get_automation_user()

        with self._transaction_factory() as cursor:
            candidate = (
                self._material_request_repository
                .claim_next_auto_assignment_candidate(
                    threshold_minutes,
                    cursor=cursor,
                )
            )

            if candidate is None:
                return None

            # Defensive recheck after the row lock is acquired.
            if (
                str(candidate.get("status") or "") != "New"
                or str(candidate.get("workflow_status") or "")
                != "Submitted"
                or candidate.get("assigned_to") is not None
                or candidate.get("current_assignment_id") is not None
            ):
                return None

            officer = self._get_least_loaded_officer_in_transaction(
                cursor=cursor
            )

            if officer is None:
                raise ValueError(
                    "No active Purchasing Officer is available "
                    "for automatic assignment."
                )

            material_request_id = candidate["id"]
            mr_number = candidate.get("mr_number")

            if not mr_number:
                raise ValueError(
                    "Material Request number is unavailable."
                )

            officer_id = officer["id"]
            officer_name = (
                officer.get("full_name")
                or officer.get("username")
                or str(officer_id)
            )

            assignment_id = self._assignment_service.assign(
                material_request_id=material_request_id,
                assigned_to=officer_id,
                current_user=automation_user,
                remarks=(
                    "Automatically assigned after remaining New "
                    f"and unassigned for {threshold_minutes} minutes."
                ),
                cursor=cursor,
            )

            updated_material_request = (
                self._material_request_repository.update_assignment_context(
                    material_request_id=material_request_id,
                    assignment_id=assignment_id,
                    assigned_to=officer_id,
                    workflow_status=MaterialRequestState.ASSIGNED,
                    cursor=cursor,
                )
            )

            if updated_material_request is None:
                raise ValueError(
                    "Material Request assignment context could not be updated."
                )

            ActivityLogger.log(
                cursor,
                user_id=automation_user.get("id"),
                action="AUTO ASSIGN",
                module=ActivityLogger.MODULE_QUOTATION,
                record_id=material_request_id,
                details=(
                    f"Automatically assigned Material Request {mr_number} "
                    f"to {officer_name} after remaining New and "
                    f"unassigned for {threshold_minutes} minutes."
                ),
            )

            PersistentNotificationService.notify_material_request_auto_assigned(
                recipient_user_id=officer_id,
                material_request_id=material_request_id,
                mr_number=mr_number,
                auto_assigned_by=automation_user.get("id"),
                threshold_minutes=threshold_minutes,
                cursor=cursor,
            )

            requester_user_id = candidate.get(
                "requested_by_user_id"
            )

            if requester_user_id:
                PersistentNotificationService.notify_requester_material_request_auto_assigned(
                    recipient_user_id=requester_user_id,
                    material_request_id=material_request_id,
                    mr_number=mr_number,
                    purchasing_officer_name=officer_name,
                    auto_assigned_by=automation_user.get("id"),
                    threshold_minutes=threshold_minutes,
                    cursor=cursor,
                )

            RealtimeEventService.publish(
                "material_request_auto_assigned",
                entity_type="material_request",
                entity_id=material_request_id,
                action="auto_assigned",
                actor_user_id=automation_user.get("id"),
                data={
                    "mr_number": mr_number,
                    "assigned_to": str(officer_id),
                    "assigned_to_name": officer_name,
                    "threshold_minutes": threshold_minutes,
                },
                cursor=cursor,
            )

            return {
                "assignment_id": assignment_id,
                "material_request": updated_material_request,
                "assigned_to": {
                    "id": officer_id,
                    "full_name": officer_name,
                    "username": officer.get("username") or "",
                    "active_workload_before": officer[
                        "active_workload"
                    ],
                },
                "threshold_minutes": threshold_minutes,
                "auto_assigned_by": automation_user.get("id"),
            }

    def auto_assign_all_due(
        self,
        threshold_minutes: int = 60,
        *,
        max_assignments: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Process currently overdue Material Requests one at a time.

        Each assignment uses its own transaction. This keeps locks short and
        allows another worker instance to safely skip records already claimed.
        """
        threshold_minutes = self._normalize_threshold_minutes(
            threshold_minutes
        )

        try:
            normalized_max = int(max_assignments)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Maximum auto assignments must be a positive integer."
            ) from exc

        if normalized_max < 1:
            raise ValueError(
                "Maximum auto assignments must be at least 1."
            )

        results: list[dict[str, Any]] = []

        for _ in range(normalized_max):
            result = self.auto_assign_next(
                threshold_minutes
            )

            if result is None:
                break

            results.append(result)

        return results

    def recommend_assignments(
        self,
        threshold_minutes: int = 60,
    ) -> dict[str, Any]:
        """
        Produce a read-only Auto Assignment recommendation.

        Patch 2A intentionally does not write anything to PostgreSQL.
        """
        threshold_minutes = self._normalize_threshold_minutes(
            threshold_minutes
        )

        candidates = self.get_eligible_material_requests(
            threshold_minutes
        )
        officers = self.get_active_purchasing_officer_workloads()

        recommendations: list[dict[str, Any]] = []

        if officers:
            # Simulate fair least-workload distribution across the current
            # candidate batch without altering real database workloads.
            simulated = {
                str(officer["id"]): int(officer["active_workload"])
                for officer in officers
            }

            for candidate in candidates:
                selected = min(
                    officers,
                    key=lambda officer: (
                        simulated[str(officer["id"])],
                        str(officer["full_name"]).lower(),
                        str(officer["username"]).lower(),
                        str(officer["id"]),
                    ),
                )

                recommendations.append(
                    {
                        "material_request_id": candidate.get("id"),
                        "mr_number": candidate.get("mr_number"),
                        "created_at": candidate.get("created_at"),
                        "age_minutes": candidate.get("age_minutes"),
                        "recommended_officer_id": selected["id"],
                        "recommended_officer_name": selected["full_name"],
                        "recommended_officer_username": selected["username"],
                        "workload_before": simulated[str(selected["id"])],
                    }
                )

                simulated[str(selected["id"])] += 1

        return {
            "threshold_minutes": threshold_minutes,
            "eligible_material_requests": candidates,
            "purchasing_officer_workloads": officers,
            "recommendations": recommendations,
        }