"""
JCAP Construction Suite
Fake Transaction

Provides an in-memory transaction test double for service and process tests.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from types import TracebackType
from typing import Any


class FakeTransaction:
    """
    Simulates transactional behavior without a database.

    Supports both explicit lifecycle calls and context-manager usage.
    """

    def __init__(self) -> None:
        self.reset()

    def __enter__(self) -> "FakeTransaction":
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        _ = exc_value
        _ = traceback

        if exc_type is None:
            self.commit()
        else:
            self.rollback()

        return False

    def begin(self) -> None:
        if self._active:
            raise RuntimeError("A transaction is already active.")

        self._active = True
        self._events.append("begin")

    def commit(self) -> None:
        self._require_active()

        self._active = False
        self._commit_count += 1
        self._events.append("commit")

        for callback in list(self._commit_callbacks):
            callback()

    def rollback(self) -> None:
        self._require_active()

        self._active = False
        self._rollback_count += 1
        self._events.append("rollback")

        for callback in list(self._rollback_callbacks):
            callback()

    def execute(self, callback: Callable[[], Any]) -> Any:
        """
        Execute a callback inside a transaction.

        Commits on success and rolls back when the callback raises.
        """
        if not callable(callback):
            raise TypeError("callback must be callable.")

        with self:
            return callback()

    def on_commit(self, callback: Callable[[], Any]) -> None:
        """Register a callback executed after commit."""
        if not callable(callback):
            raise TypeError("callback must be callable.")

        self._commit_callbacks.append(callback)

    def on_rollback(self, callback: Callable[[], Any]) -> None:
        """Register a callback executed after rollback."""
        if not callable(callback):
            raise TypeError("callback must be callable.")

        self._rollback_callbacks.append(callback)

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def committed(self) -> bool:
        return self._commit_count > 0

    @property
    def rolled_back(self) -> bool:
        return self._rollback_count > 0

    @property
    def commit_count(self) -> int:
        return self._commit_count

    @property
    def rollback_count(self) -> int:
        return self._rollback_count

    @property
    def events(self) -> list[str]:
        return deepcopy(self._events)

    def reset(self) -> None:
        """Restore the fake to a clean state."""
        self._active = False
        self._commit_count = 0
        self._rollback_count = 0
        self._events: list[str] = []
        self._commit_callbacks: list[Callable[[], Any]] = []
        self._rollback_callbacks: list[Callable[[], Any]] = []

    def _require_active(self) -> None:
        if not self._active:
            raise RuntimeError("No active transaction.")