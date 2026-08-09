"""
JCAP Construction Suite
PostgreSQL Real-Time Listener
"""

from __future__ import annotations

import json
import select
import threading
import time
from collections.abc import Callable
from typing import Any

from core.database.connection import get_connection
from core.realtime.realtime_event_service import REALTIME_CHANNEL


class RealtimeListener:
    """Background PostgreSQL LISTEN client with automatic reconnect."""

    def __init__(
        self,
        on_event: Callable[[dict[str, Any]], None],
        *,
        on_status_change: Callable[[bool], None] | None = None,
        reconnect_delay_seconds: float = 2.0,
        select_timeout_seconds: float = 1.0,
        heartbeat_interval_seconds: float = 5.0,
    ) -> None:
        self._on_event = on_event
        self._on_status_change = on_status_change
        self._reconnect_delay_seconds = reconnect_delay_seconds
        self._select_timeout_seconds = select_timeout_seconds
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection = None
        self._connected = False

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        if self.is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="JCAP-RealtimeListener",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close_connection()

        thread = self._thread
        if (
            thread
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=2.0)

        self._thread = None
        self._set_connected(False)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._connect_and_listen()
                self._listen_loop()
            except Exception:
                self._set_connected(False)
                self._close_connection()

                if self._stop_event.wait(
                    self._reconnect_delay_seconds
                ):
                    break

        self._set_connected(False)
        self._close_connection()

    def _connect_and_listen(self) -> None:
        conn = get_connection(
            connect_timeout=3,
            keepalives=1,
            keepalives_idle=5,
            keepalives_interval=2,
            keepalives_count=3,
        )
        conn.set_session(autocommit=True)

        cur = conn.cursor()
        try:
            cur.execute(
                f"LISTEN {REALTIME_CHANNEL};"
            )
        finally:
            cur.close()

        self._connection = conn
        self._set_connected(True)

    def _listen_loop(self) -> None:
        conn = self._connection
        if conn is None:
            return

        last_heartbeat = time.monotonic()

        while not self._stop_event.is_set():
            readable, _, _ = select.select(
                [conn],
                [],
                [],
                self._select_timeout_seconds,
            )

            if readable:
                conn.poll()

                while conn.notifies:
                    notification = conn.notifies.pop(0)
                    event = self._decode_payload(
                        notification.payload
                    )
                    if event is not None:
                        try:
                            self._on_event(event)
                        except Exception:
                            pass

            now = time.monotonic()

            if (
                now - last_heartbeat
                >= self._heartbeat_interval_seconds
            ):
                self._run_heartbeat(conn)
                last_heartbeat = now

    @staticmethod
    def _run_heartbeat(conn) -> None:
        """
        Force a lightweight round-trip so an interrupted network
        connection is detected even while no NOTIFY events are arriving.
        """
        cur = conn.cursor()

        try:
            cur.execute("SELECT 1;")
            cur.fetchone()
        finally:
            cur.close()

    @staticmethod
    def _decode_payload(
        payload: str,
    ) -> dict[str, Any] | None:
        try:
            decoded = json.loads(payload)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        return decoded if isinstance(decoded, dict) else None

    def _set_connected(
        self,
        connected: bool,
    ) -> None:
        if self._connected == connected:
            return

        self._connected = connected

        if self._on_status_change is not None:
            try:
                self._on_status_change(connected)
            except Exception:
                pass

    def _close_connection(self) -> None:
        conn = self._connection
        self._connection = None

        if conn is None:
            return

        try:
            conn.close()
        except Exception:
            pass