"""
JCAP Construction Suite
Fake Clock

Provides deterministic control over date and time in unit tests.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Final


class FakeClock:
    """
    Deterministic clock for service and process tests.

    The fake stores one current datetime and exposes helpers to read or advance
    it without depending on the operating system clock.
    """

    DEFAULT_DATETIME: Final[datetime] = datetime(
        2026,
        1,
        1,
        8,
        0,
        0,
        tzinfo=timezone.utc,
    )

    def __init__(self, current_datetime: datetime | None = None) -> None:
        self._initial_datetime = self._normalize_datetime(
            current_datetime or self.DEFAULT_DATETIME
        )
        self._current_datetime = self._initial_datetime

    def now(self) -> datetime:
        """Return the current deterministic datetime."""
        return self._current_datetime

    def today(self) -> date:
        """Return the date portion of the current deterministic datetime."""
        return self._current_datetime.date()

    def set(self, value: datetime) -> datetime:
        """
        Set the current deterministic datetime.

        Returns the normalized value for convenient inline use in tests.
        """
        self._current_datetime = self._normalize_datetime(value)
        return self._current_datetime

    def advance(
        self,
        *,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> datetime:
        """
        Advance the clock by the supplied time interval.

        Negative values are supported, allowing tests to move backward when
        needed.
        """
        delta = timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
        )
        self._current_datetime += delta
        return self._current_datetime

    def reset(self) -> None:
        """Restore the clock to the datetime supplied at construction."""
        self._current_datetime = self._initial_datetime

    def is_before(self, value: datetime) -> bool:
        """Return whether the current time is earlier than ``value``."""
        return self._current_datetime < self._normalize_datetime(value)

    def is_after(self, value: datetime) -> bool:
        """Return whether the current time is later than ``value``."""
        return self._current_datetime > self._normalize_datetime(value)

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        """
        Validate and normalize a datetime.

        Naive datetimes are interpreted as UTC so all test comparisons remain
        deterministic across developer machines and CI environments.
        """
        if not isinstance(value, datetime):
            raise TypeError(
                f"value must be a datetime instance, not "
                f"{type(value).__name__}."
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)