"""
JCAP Construction Suite
Fake UUID Provider

Provides deterministic UUID generation for unit and process tests.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from copy import deepcopy
from typing import Final
from uuid import UUID, uuid4


class FakeUUIDProvider:
    """
    Deterministic UUID provider for tests.

    UUIDs may be supplied up front or queued later. When the queue is empty,
    the provider can either generate a fallback UUID or raise an error,
    depending on configuration.
    """

    DEFAULT_NAMESPACE_PREFIX: Final[str] = "00000000-0000-0000-0000-"

    def __init__(
        self,
        values: Iterable[UUID | str] | None = None,
        *,
        allow_fallback: bool = True,
    ) -> None:
        self._initial_values = tuple(
            self._normalize_uuid(value)
            for value in (values or ())
        )
        self._queue: deque[UUID] = deque(self._initial_values)
        self._generated: list[UUID] = []
        self._allow_fallback = allow_fallback

    def new(self) -> UUID:
        """
        Return the next UUID.

        Queued values are consumed first. When no queued UUID remains, a new
        random UUID is generated only when fallback generation is enabled.
        """
        if self._queue:
            value = self._queue.popleft()
        elif self._allow_fallback:
            value = uuid4()
        else:
            raise RuntimeError(
                "FakeUUIDProvider has no queued UUID values remaining."
            )

        self._generated.append(value)
        return value

    def __call__(self) -> UUID:
        """Allow the provider to be injected as a callable UUID factory."""
        return self.new()

    def queue(self, *values: UUID | str) -> None:
        """Append one or more UUID values to the generation queue."""
        for value in values:
            self._queue.append(self._normalize_uuid(value))

    def queue_many(self, values: Iterable[UUID | str]) -> None:
        """Append an iterable of UUID values to the generation queue."""
        for value in values:
            self._queue.append(self._normalize_uuid(value))

    @property
    def remaining_count(self) -> int:
        """Return the number of deterministic UUIDs still queued."""
        return len(self._queue)

    @property
    def generated_count(self) -> int:
        """Return the total number of UUIDs returned by this provider."""
        return len(self._generated)

    @property
    def generated_values(self) -> tuple[UUID, ...]:
        """Return an immutable snapshot of generated UUIDs."""
        return tuple(deepcopy(self._generated))

    @property
    def remaining_values(self) -> tuple[UUID, ...]:
        """Return an immutable snapshot of queued UUIDs."""
        return tuple(deepcopy(list(self._queue)))

    def last_generated(self) -> UUID | None:
        """Return the most recently generated UUID, when available."""
        return self._generated[-1] if self._generated else None

    def clear_queue(self) -> None:
        """Remove all queued UUID values."""
        self._queue.clear()

    def reset(self) -> None:
        """
        Restore the provider to its construction state.

        Generated history is cleared and the original UUID queue is restored.
        """
        self._queue = deque(self._initial_values)
        self._generated.clear()

    @staticmethod
    def sequential_uuid(sequence: int) -> UUID:
        """
        Create a stable UUID from a positive sequence number.

        This helper is useful for readable deterministic fixtures.
        """
        if not isinstance(sequence, int):
            raise TypeError("sequence must be an integer.")

        if sequence < 0:
            raise ValueError("sequence cannot be negative.")

        if sequence > 999_999_999_999:
            raise ValueError(
                "sequence must not exceed 999999999999."
            )

        return UUID(
            f"{FakeUUIDProvider.DEFAULT_NAMESPACE_PREFIX}"
            f"{sequence:012d}"
        )

    @staticmethod
    def _normalize_uuid(value: UUID | str) -> UUID:
        """Validate and normalize a UUID-compatible value."""
        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid UUID value: {value!r}."
                ) from exc

        raise TypeError(
            "UUID values must be UUID instances or UUID strings, "
            f"not {type(value).__name__}."
        )