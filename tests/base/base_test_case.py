"""
JCAP Construction Suite
Base Test Case

Provides reusable helpers and cleanup behavior for unit tests.
"""

from __future__ import annotations

import unittest
from collections.abc import Callable
from typing import Any, TypeVar
from uuid import UUID, uuid4

from tests.base.test_assertions import (
    assert_is_uuid,
    assert_permission_denied,
    assert_repository_called,
    assert_repository_not_called,
    assert_validation_error,
)

T = TypeVar("T")


class BaseTestCase(unittest.TestCase):
    """Base class for JCAP Construction Suite unit tests."""

    def setUp(self) -> None:
        """Initialize per-test cleanup tracking."""
        super().setUp()
        self._resettable_test_doubles: list[Any] = []

    def tearDown(self) -> None:
        """Reset registered test doubles after every test."""
        for test_double in reversed(self._resettable_test_doubles):
            reset_method = getattr(test_double, "reset", None)

            if callable(reset_method):
                reset_method()

        self._resettable_test_doubles.clear()
        super().tearDown()

    def register_test_double(self, test_double: T) -> T:
        """
        Register a fake, stub, or spy for automatic reset during tearDown.

        The same object is returned so it can be assigned inline.
        """
        self._resettable_test_doubles.append(test_double)
        return test_double

    @staticmethod
    def new_uuid() -> UUID:
        """Create a new UUID for isolated test data."""
        return uuid4()

    def assertUUID(
        self,
        value: Any,
        message: str | None = None,
    ) -> None:
        """Assert that a value is a UUID instance."""
        assert_is_uuid(
            self,
            value,
            message,
        )

    def assertRepositoryCalled(
        self,
        repository: Any,
        method_name: str,
        expected_count: int = 1,
    ) -> None:
        """Assert that a fake repository method was called."""
        assert_repository_called(
            self,
            repository,
            method_name,
            expected_count,
        )

    def assertRepositoryNotCalled(
        self,
        repository: Any,
        method_name: str,
    ) -> None:
        """Assert that a fake repository method was not called."""
        assert_repository_not_called(
            self,
            repository,
            method_name,
        )

    def assertValidationError(
        self,
        callback: Callable[[], Any],
        expected_message: str | None = None,
        exception_type: type[Exception] = ValueError,
    ) -> Exception:
        """Assert that a callback raises a validation exception."""
        return assert_validation_error(
            self,
            callback,
            expected_message,
            exception_type,
        )

    def assertPermissionDenied(
        self,
        callback: Callable[[], Any],
        expected_message: str | None = None,
        exception_type: type[Exception] = PermissionError,
    ) -> Exception:
        """Assert that a callback raises a permission exception."""
        return assert_permission_denied(
            self,
            callback,
            expected_message,
            exception_type,
        )