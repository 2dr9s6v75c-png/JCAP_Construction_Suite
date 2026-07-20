"""
JCAP Construction Suite
Base Builder

Provides a reusable foundation for fluent test-data builders.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Generic, TypeVar

BuiltT = TypeVar("BuiltT")
BuilderT = TypeVar("BuilderT", bound="BaseBuilder[Any]")


class BaseBuilder(ABC, Generic[BuiltT]):
    """
    Abstract foundation for all JCAP test-data builders.

    Subclasses define their default field values and implement ``_build``.
    The base class provides reusable mutation, cloning, reset, and bulk-build
    behavior while preserving test isolation through deep copies.
    """

    def __init__(self) -> None:
        self._defaults: dict[str, Any] = deepcopy(self.default_values())
        self._values: dict[str, Any] = deepcopy(self._defaults)

    @classmethod
    @abstractmethod
    def default_values(cls) -> dict[str, Any]:
        """
        Return the builder's default field values.

        A fresh dictionary must be returned for each call.
        """
        raise NotImplementedError

    @abstractmethod
    def _build(self, values: dict[str, Any]) -> BuiltT:
        """
        Construct the final object from resolved values.

        Subclasses should not mutate ``values``.
        """
        raise NotImplementedError

    def with_value(
        self: BuilderT,
        field_name: str,
        value: Any,
    ) -> BuilderT:
        """Set one field and return the builder for fluent chaining."""
        normalized_name = self._validate_field_name(field_name)

        if normalized_name not in self._defaults:
            raise KeyError(
                f"Unknown builder field: {normalized_name!r}. "
                f"Available fields: {', '.join(sorted(self._defaults))}."
            )

        self._values[normalized_name] = deepcopy(value)
        return self

    def with_values(
        self: BuilderT,
        **values: Any,
    ) -> BuilderT:
        """Set multiple fields and return the builder."""
        for field_name, value in values.items():
            self.with_value(field_name, value)

        return self

    def override(
        self: BuilderT,
        **values: Any,
    ) -> BuilderT:
        """Alias for ``with_values`` for concise test setup."""
        return self.with_values(**values)

    def without(
        self: BuilderT,
        *field_names: str,
    ) -> BuilderT:
        """
        Set one or more fields to ``None``.

        This is useful when building invalid objects for validation tests.
        """
        for field_name in field_names:
            self.with_value(field_name, None)

        return self

    def build(self, **overrides: Any) -> BuiltT:
        """
        Build one object.

        Per-call overrides do not permanently modify the builder state.
        """
        resolved_values = deepcopy(self._values)

        for field_name, value in overrides.items():
            normalized_name = self._validate_field_name(field_name)

            if normalized_name not in self._defaults:
                raise KeyError(
                    f"Unknown builder field: {normalized_name!r}. "
                    f"Available fields: {', '.join(sorted(self._defaults))}."
                )

            resolved_values[normalized_name] = deepcopy(value)

        return self._build(resolved_values)

    def build_many(
        self,
        count: int,
        *,
        overrides: list[dict[str, Any]] | None = None,
    ) -> list[BuiltT]:
        """
        Build multiple objects.

        ``overrides`` may supply a distinct override dictionary for each item.
        When omitted, the builder's current state is reused for every item.
        """
        if not isinstance(count, int):
            raise TypeError("count must be an integer.")

        if count < 0:
            raise ValueError("count cannot be negative.")

        if overrides is not None and len(overrides) != count:
            raise ValueError(
                "The number of override dictionaries must match count."
            )

        objects: list[BuiltT] = []

        for index in range(count):
            item_overrides = overrides[index] if overrides is not None else {}
            objects.append(self.build(**item_overrides))

        return objects

    def clone(self: BuilderT) -> BuilderT:
        """
        Return an independent copy of the builder.

        The clone preserves current values but future changes remain isolated.
        """
        cloned = deepcopy(self)
        return cloned

    def reset(self: BuilderT) -> BuilderT:
        """Restore all fields to their original defaults."""
        self._values = deepcopy(self._defaults)
        return self

    def snapshot(self) -> dict[str, Any]:
        """Return an immutable-style deep copy of current builder values."""
        return deepcopy(self._values)

    def get_value(self, field_name: str) -> Any:
        """Return a deep copy of one current builder value."""
        normalized_name = self._validate_field_name(field_name)

        if normalized_name not in self._values:
            raise KeyError(
                f"Unknown builder field: {normalized_name!r}."
            )

        return deepcopy(self._values[normalized_name])

    def has_field(self, field_name: str) -> bool:
        """Return whether the builder defines a field."""
        normalized_name = self._validate_field_name(field_name)
        return normalized_name in self._defaults

    @property
    def field_names(self) -> tuple[str, ...]:
        """Return all supported field names in stable order."""
        return tuple(self._defaults.keys())

    @staticmethod
    def _validate_field_name(field_name: str) -> str:
        """Validate and normalize a builder field name."""
        if not isinstance(field_name, str):
            raise TypeError("field_name must be a string.")

        normalized_name = field_name.strip()

        if not normalized_name:
            raise ValueError("field_name must be a non-empty string.")

        return normalized_name