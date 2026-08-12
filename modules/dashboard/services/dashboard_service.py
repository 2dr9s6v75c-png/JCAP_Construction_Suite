from __future__ import annotations

from datetime import date
from typing import Any

from core.database.connection import get_connection


class DashboardService:
    ROLE_PURCHASING_MANAGER = "purchasing manager"
    ROLE_ADMINISTRATOR = "administrator"

    STATUS_ARCHIVED = "Archived"
    STATUS_NEW = "New"
    STATUS_ASSIGNED = "Assigned"
    STATUS_IN_PROGRESS = "In Progress"
    STATUS_WAITING_QUOTE = "Waiting Supplier Quote"
    STATUS_COMPLETED = "Completed"

    CLARIFICATION_AWAITING_ENGINEERING = "Awaiting Engineering Response"
    CLARIFICATION_RESPONSE_READY = "Response Ready"

    @classmethod
    def get_dashboard(cls, user: dict[str, Any]) -> dict[str, Any]:
        user_id = cls._require_user_id(user)
        role_name = cls._role_name(user)

        if role_name in {cls.ROLE_PURCHASING_MANAGER, cls.ROLE_ADMINISTRATOR}:
            perspective = "manager"
        elif "purchasing" in role_name:
            perspective = "purchasing"
        else:
            perspective = "engineering"

        records = cls._get_material_requests(user_id, perspective)
        attention_count = cls._get_attention_count(user_id, perspective)

        return {
            "perspective": perspective,
            "title": cls._title_for(perspective),
            "subtitle": cls._subtitle_for(perspective),
            "cards": cls._build_cards(records, perspective, attention_count),
            "records": records,
            "attention_count": attention_count,
        }

    @classmethod
    def _get_material_requests(cls, user_id: str, perspective: str):
        conditions = ["mr.status <> %s"]
        params: list[Any] = [cls.STATUS_ARCHIVED]

        if perspective == "engineering":
            conditions.append("mr.requested_by_user_id = %s")
            params.append(user_id)
        elif perspective == "purchasing":
            conditions.append("mr.assigned_to = %s")
            params.append(user_id)

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                f"""
                SELECT
                    mr.id,
                    mr.mr_number,
                    p.project_code,
                    p.project_name,
                    mr.material_request_description,
                    mr.requested_by,
                    requester.full_name,
                    mr.assigned_to,
                    assigned.full_name,
                    mr.priority,
                    mr.status,
                    mr.due_date,
                    mr.created_at
                FROM quotation.material_requests mr
                JOIN master.projects p ON p.id = mr.project_id
                LEFT JOIN core.users requester
                    ON requester.id = mr.requested_by_user_id
                LEFT JOIN core.users assigned
                    ON assigned.id::text = mr.assigned_to
                WHERE {" AND ".join(conditions)}
                ORDER BY
                    CASE mr.priority
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                        ELSE 4
                    END,
                    CASE WHEN mr.due_date IS NULL THEN 1 ELSE 0 END,
                    mr.due_date ASC,
                    mr.created_at DESC
                """,
                params,
            )
            rows = cur.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "mr_number": row[1] or "",
                    "project_code": row[2] or "",
                    "project_name": row[3] or "",
                    "description": row[4] or "",
                    "requested_by": row[6] or row[5] or "",
                    "assigned_to_id": str(row[7]) if row[7] else None,
                    "assigned_to_name": row[8] or "Unassigned",
                    "priority": row[9] or "",
                    "status": row[10] or "",
                    "due_date": row[11],
                    "created_at": row[12],
                    "is_overdue": cls._is_overdue(row[11], row[10]),
                }
                for row in rows
            ]
        finally:
            cur.close()
            conn.close()

    @classmethod
    def _get_attention_count(cls, user_id: str, perspective: str) -> int:
        conn = get_connection()
        cur = conn.cursor()
        try:
            if perspective == "engineering":
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM quotation.clarifications c
                    JOIN quotation.material_requests mr
                        ON mr.id = c.material_request_id
                    WHERE mr.requested_by_user_id = %s
                      AND mr.status <> %s
                      AND c.status = %s
                    """,
                    (user_id, cls.STATUS_ARCHIVED, cls.CLARIFICATION_AWAITING_ENGINEERING),
                )
            elif perspective == "purchasing":
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM quotation.clarifications c
                    JOIN quotation.material_requests mr
                        ON mr.id = c.material_request_id
                    WHERE mr.assigned_to = %s
                      AND mr.status <> %s
                      AND c.status = %s
                    """,
                    (user_id, cls.STATUS_ARCHIVED, cls.CLARIFICATION_RESPONSE_READY),
                )
            else:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM quotation.material_requests mr
                    WHERE mr.status <> %s
                      AND (mr.assigned_to IS NULL OR BTRIM(mr.assigned_to) = '')
                    """,
                    (cls.STATUS_ARCHIVED,),
                )
            row = cur.fetchone()
            return int(row[0] or 0) if row else 0
        finally:
            cur.close()
            conn.close()

    @classmethod
    def _build_cards(cls, records, perspective, attention_count):
        def status_count(value):
            return sum(1 for r in records if r.get("status") == value)

        if perspective == "engineering":
            first_label = "My Requests"
            second_label = "New / Assigned"
            second_value = sum(
                1 for r in records
                if r.get("status") in {cls.STATUS_NEW, cls.STATUS_ASSIGNED}
            )
        elif perspective == "purchasing":
            first_label = "My Assigned Requests"
            second_label = "Assigned"
            second_value = status_count(cls.STATUS_ASSIGNED)
        else:
            first_label = "Active Requests"
            second_label = "Unassigned"
            second_value = sum(1 for r in records if not r.get("assigned_to_id"))

        return [
            {"label": first_label, "value": len(records)},
            {"label": second_label, "value": second_value},
            {"label": "In Progress", "value": status_count(cls.STATUS_IN_PROGRESS)},
            {"label": "Waiting Supplier Quote", "value": status_count(cls.STATUS_WAITING_QUOTE)},
            {"label": "Completed", "value": status_count(cls.STATUS_COMPLETED)},
            {"label": "Attention Required", "value": attention_count},
        ]

    @staticmethod
    def _is_overdue(due_date, status):
        if not due_date or status in {"Completed", "Archived"}:
            return False
        due_value = due_date.date() if hasattr(due_date, "date") else due_date
        return isinstance(due_value, date) and due_value < date.today()

    @staticmethod
    def _require_user_id(user):
        user_id = user.get("id") if isinstance(user, dict) else None
        if not user_id:
            raise ValueError("Authenticated user ID is required for the Dashboard.")
        return str(user_id)

    @staticmethod
    def _role_name(user):
        return str(user.get("role_name") or user.get("role") or "").strip().lower()

    @staticmethod
    def _title_for(perspective):
        return {
            "engineering": "My Material Requests",
            "purchasing": "My Purchasing Work",
            "manager": "Purchasing Overview",
        }[perspective]

    @staticmethod
    def _subtitle_for(perspective):
        return {
            "engineering": "Track your requests, Purchasing assignment, quotation progress, and clarifications.",
            "purchasing": "Review Material Requests currently assigned to you and items requiring action.",
            "manager": "Monitor active Material Requests, assignment needs, and current Purchasing workload.",
        }[perspective]
