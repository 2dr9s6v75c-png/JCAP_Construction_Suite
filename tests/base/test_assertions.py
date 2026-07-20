"""
JCAP Construction Suite
Reusable Test Assertions

Provides expressive assertion helpers for service, repository, and process tests.
This module is testing infrastructure and should not be collected as a test file.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

__test__ = False


def assert_is_uuid(
    test_case: Any,
    value: Any,
    message: str | None = None,
) -> None:
    """Assert that ``value`` is a UUID instance."""
    test_case.assertIsInstance(
        value,
        UUID,
        message or (
            f"Expected a UUID instance, but received "
            f"{type(value).__name__}."
        ),
    )


def assert_repository_called(
    test_case: Any,
    repository: Any,
    method_name: str,
    expected_count: int = 1,
) -> None:
    """
    Assert that a fake repository method was called the expected number of times.
    """
    if not isinstance(method_name, str) or not method_name.strip():
        raise ValueError("Method name must be a non-empty string.")

    if expected_count < 0:
        raise ValueError("Expected call count cannot be negative.")

    call_count_method = getattr(repository, "call_count", None)

    if not callable(call_count_method):
        raise TypeError(
            "Repository test double must provide a callable call_count() method."
        )

    actual_count = call_count_method(method_name)

    test_case.assertEqual(
        actual_count,
        expected_count,
        (
            f"Expected repository method '{method_name}' to be called "
            f"{expected_count} time(s), but it was called "
            f"{actual_count} time(s)."
        ),
    )


def assert_repository_not_called(
    test_case: Any,
    repository: Any,
    method_name: str,
) -> None:
    """Assert that a fake repository method was never called."""
    assert_repository_called(
        test_case,
        repository,
        method_name,
        expected_count=0,
    )


def assert_repository_last_call(
    test_case: Any,
    repository: Any,
    method_name: str,
    **expected_arguments: Any,
) -> dict[str, Any]:
    """
    Assert that the latest repository call contains the expected arguments.

    Extra recorded arguments are allowed. Only explicitly supplied expectations
    are compared.
    """
    if not isinstance(method_name, str) or not method_name.strip():
        raise ValueError("Method name must be a non-empty string.")

    last_call_method = getattr(repository, "last_call", None)

    if not callable(last_call_method):
        raise TypeError(
            "Repository test double must provide a callable last_call() method."
        )

    actual_arguments = last_call_method(method_name)

    test_case.assertIsNotNone(
        actual_arguments,
        f"Repository method '{method_name}' was not called.",
    )

    for argument_name, expected_value in expected_arguments.items():
        test_case.assertIn(
            argument_name,
            actual_arguments,
            (
                f"Argument '{argument_name}' was not recorded for repository "
                f"method '{method_name}'."
            ),
        )
        test_case.assertEqual(
            actual_arguments[argument_name],
            expected_value,
            (
                f"Unexpected value for argument '{argument_name}' in repository "
                f"method '{method_name}'."
            ),
        )

    return actual_arguments


def assert_validation_error(
    test_case: Any,
    callback: Callable[[], Any],
    expected_message: str | None = None,
    exception_type: type[Exception] = ValueError,
) -> Exception:
    """Assert that ``callback`` raises a validation-related exception."""
    if not callable(callback):
        raise TypeError("callback must be callable.")

    with test_case.assertRaises(exception_type) as context:
        callback()

    if expected_message is not None:
        test_case.assertIn(
            expected_message,
            str(context.exception),
        )

    return context.exception


def assert_permission_denied(
    test_case: Any,
    callback: Callable[[], Any],
    expected_message: str | None = None,
    exception_type: type[Exception] = PermissionError,
) -> Exception:
    """Assert that ``callback`` raises a permission-related exception."""
    if not callable(callback):
        raise TypeError("callback must be callable.")

    with test_case.assertRaises(exception_type) as context:
        callback()

    if expected_message is not None:
        test_case.assertIn(
            expected_message,
            str(context.exception),
        )

    return context.exception