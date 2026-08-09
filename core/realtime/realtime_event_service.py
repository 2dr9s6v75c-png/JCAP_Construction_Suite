"""
JCAP Construction Suite
Real-Time Event Service
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from core.database.connection import get_connection


REALTIME_CHANNEL = "jcap_events"
MAX_PAYLOAD_BYTES = 7900


class RealtimeEventService:
    """Publish small application events through PostgreSQL NOTIFY."""

    @classmethod
    def publish(
        cls,
        event_type: str,
        *,
        entity_type: str | None = None,
        entity_id: UUID | str | None = None,
        action: str | None = None,
        actor_user_id: UUID | str | None = None,
        data: dict[str, Any] | None = None,
        cursor=None,
    ) -> dict[str, Any]:
        event = cls._build_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_user_id=actor_user_id,
            data=data,
        )

        payload = json.dumps(
            event,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        if len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ValueError(
                "Real-time event payload is too large. "
                "Publish identifiers and small metadata only."
            )

        if cursor is not None:
            cursor.execute(
                "SELECT pg_notify(%s, %s)",
                (REALTIME_CHANNEL, payload),
            )
            return event

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "SELECT pg_notify(%s, %s)",
                (REALTIME_CHANNEL, payload),
            )
            conn.commit()
            return event
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def _build_event(
        *,
        event_type: str,
        entity_type: str | None,
        entity_id: UUID | str | None,
        action: str | None,
        actor_user_id: UUID | str | None,
        data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        normalized_event_type = str(event_type or "").strip()
        if not normalized_event_type:
            raise ValueError("Real-time event type is required.")

        return {
            "event_type": normalized_event_type,
            "entity_type": (
                str(entity_type).strip()
                if entity_type is not None
                else None
            ),
            "entity_id": (
                str(entity_id)
                if entity_id is not None
                else None
            ),
            "action": (
                str(action).strip()
                if action is not None
                else None
            ),
            "actor_user_id": (
                str(actor_user_id)
                if actor_user_id is not None
                else None
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
