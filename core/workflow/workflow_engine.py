from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class WorkflowError(ValueError):
    """Base error for workflow validation failures."""


class UnknownWorkflowStateError(WorkflowError):
    """Raised when a workflow state is not registered."""


class InvalidWorkflowTransitionError(WorkflowError):
    """Raised when a transition is not allowed."""


@dataclass(frozen=True)
class WorkflowTransition:
    source: str
    target: str


class WorkflowDefinition:
    def __init__(
        self,
        *,
        name: str,
        states: Iterable[str],
        transitions: dict[str, Iterable[str]],
    ) -> None:
        self.name = self._normalize_required(name, field_name="workflow name")
        normalized_states = {
            self._normalize_required(state, field_name="workflow state")
            for state in states
        }
        if not normalized_states:
            raise WorkflowError("A workflow must define at least one state.")

        normalized_transitions: dict[str, frozenset[str]] = {}
        for source, targets in transitions.items():
            normalized_source = self._normalize_required(
                source,
                field_name="transition source",
            )
            normalized_transitions[normalized_source] = frozenset(
                self._normalize_required(target, field_name="transition target")
                for target in targets
            )

        referenced_states = set(normalized_transitions)
        for targets in normalized_transitions.values():
            referenced_states.update(targets)
        unknown_states = referenced_states - normalized_states
        if unknown_states:
            raise WorkflowError(
                "Transitions reference unknown states: "
                + ", ".join(sorted(unknown_states))
            )

        self._states = frozenset(normalized_states)
        self._transitions = normalized_transitions

    @property
    def states(self) -> frozenset[str]:
        return self._states

    def validate_state(self, state: str) -> str:
        normalized_state = self._normalize_required(
            state,
            field_name="workflow state",
        )
        if normalized_state not in self._states:
            raise UnknownWorkflowStateError(
                f"Unknown state '{normalized_state}' for workflow '{self.name}'."
            )
        return normalized_state

    def can_transition(self, current_state: str, target_state: str) -> bool:
        current_state = self.validate_state(current_state)
        target_state = self.validate_state(target_state)
        if current_state == target_state:
            return True
        return target_state in self._transitions.get(current_state, frozenset())

    def require_transition(
        self,
        current_state: str,
        target_state: str,
    ) -> WorkflowTransition:
        current_state = self.validate_state(current_state)
        target_state = self.validate_state(target_state)
        if not self.can_transition(current_state, target_state):
            raise InvalidWorkflowTransitionError(
                f"Workflow '{self.name}' does not allow "
                f"'{current_state}' → '{target_state}'."
            )
        return WorkflowTransition(source=current_state, target=target_state)

    def allowed_targets(self, current_state: str) -> tuple[str, ...]:
        current_state = self.validate_state(current_state)
        return tuple(sorted(self._transitions.get(current_state, frozenset())))

    @staticmethod
    def _normalize_required(value: str, *, field_name: str) -> str:
        normalized_value = str(value or "").strip()
        if not normalized_value:
            raise WorkflowError(f"{field_name.capitalize()} is required.")
        return normalized_value


class WorkflowEngine:
    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}

    def register(
        self,
        definition: WorkflowDefinition,
        *,
        replace: bool = False,
    ) -> None:
        if definition.name in self._definitions and not replace:
            raise WorkflowError(
                f"Workflow '{definition.name}' is already registered."
            )
        self._definitions[definition.name] = definition

    def get(self, workflow_name: str) -> WorkflowDefinition:
        workflow_name = str(workflow_name or "").strip()
        definition = self._definitions.get(workflow_name)
        if definition is None:
            raise WorkflowError(
                f"Workflow '{workflow_name}' is not registered."
            )
        return definition

    def can_transition(
        self,
        workflow_name: str,
        current_state: str,
        target_state: str,
    ) -> bool:
        return self.get(workflow_name).can_transition(
            current_state,
            target_state,
        )

    def require_transition(
        self,
        workflow_name: str,
        current_state: str,
        target_state: str,
    ) -> WorkflowTransition:
        return self.get(workflow_name).require_transition(
            current_state,
            target_state,
        )

    def allowed_targets(
        self,
        workflow_name: str,
        current_state: str,
    ) -> tuple[str, ...]:
        return self.get(workflow_name).allowed_targets(current_state)
