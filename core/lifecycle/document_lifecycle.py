from enum import Enum


class DocumentLifecycle(str, Enum):
    """
    Standard system lifecycle states shared by business documents.

    Business-specific statuses may still exist, such as:
    - Waiting Supplier Quote
    - Submitted
    - Approved
    - Partially Delivered

    These lifecycle values describe the document's general system state.
    """

    DRAFT = "Draft"
    ACTIVE = "Active"
    LOCKED = "Locked"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"
    RESTORED = "Restored"

    @classmethod
    def active_states(cls) -> tuple[str, ...]:
        """
        Lifecycle states treated as active records.
        """
        return (
            cls.DRAFT.value,
            cls.ACTIVE.value,
            cls.LOCKED.value,
            cls.COMPLETED.value,
            cls.RESTORED.value,
        )

    @classmethod
    def is_archived(cls, status: str | None) -> bool:
        return cls.normalize(status) == cls.ARCHIVED.value

    @classmethod
    def is_active(cls, status: str | None) -> bool:
        return cls.normalize(status) in cls.active_states()

    @classmethod
    def normalize(cls, status: str | None) -> str:
        """
        Convert inconsistent casing and spacing into a standard value.

        Examples:
            " archived " -> "Archived"
            "ACTIVE"     -> "Active"
        """
        if not status:
            return ""

        cleaned = str(status).strip().lower()

        for lifecycle_state in cls:
            if lifecycle_state.value.lower() == cleaned:
                return lifecycle_state.value

        return str(status).strip()

    @classmethod
    def values(cls) -> list[str]:
        return [state.value for state in cls]