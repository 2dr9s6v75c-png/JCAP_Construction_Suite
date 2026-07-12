from tkinter import messagebox
from typing import Iterable

from core.database.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationService:
    """
    Centralized notification service for the JCAP Construction Suite.

    The service provides two notification channels:

    1. Immediate user-facing application dialogs.
    2. Persistent database notifications for multi-user workflows.

    Persistent notifications are stored in core.notifications and may
    later be displayed through a notification center, dashboard badge,
    or Windows toast integration.
    """

    APP_TITLE = "JCAP Construction Suite"

    # ============================================================
    # UI DIALOG NOTIFICATIONS
    # ============================================================

    @classmethod
    def success(
        cls,
        message: str,
        *,
        title: str = "Success",
    ) -> None:
        messagebox.showinfo(
            title,
            cls._clean_message(message),
        )

    @classmethod
    def info(
        cls,
        message: str,
        *,
        title: str = "Information",
    ) -> None:
        messagebox.showinfo(
            title,
            cls._clean_message(message),
        )

    @classmethod
    def warning(
        cls,
        message: str,
        *,
        title: str = "Warning",
    ) -> None:
        messagebox.showwarning(
            title,
            cls._clean_message(message),
        )

    @classmethod
    def error(
        cls,
        message: str,
        *,
        title: str = "Error",
        error: Exception | None = None,
    ) -> None:
        full_message = cls._clean_message(
            message
        )

        if error is not None:
            error_text = str(
                error
            ).strip()

            if error_text:
                full_message = (
                    f"{full_message}\n\n"
                    f"Technical details:\n"
                    f"{error_text}"
                )

        messagebox.showerror(
            title,
            full_message,
        )

    @classmethod
    def confirm(
        cls,
        message: str,
        *,
        title: str = "Confirm Action",
    ) -> bool:
        return messagebox.askyesno(
            title,
            cls._clean_message(message),
        )

    @classmethod
    def validation(
        cls,
        errors: Iterable[str],
        *,
        title: str = "Validation Required",
    ) -> None:
        clean_errors = [
            str(error).strip()
            for error in errors
            if str(error).strip()
        ]

        if not clean_errors:
            return

        message = (
            "Please correct the following:\n\n"
            + "\n".join(
                f"• {error}"
                for error in clean_errors
            )
        )

        messagebox.showwarning(
            title,
            message,
        )

    # ============================================================
    # PERSISTENT NOTIFICATIONS
    # ============================================================

    @classmethod
    def create_notification(
        cls,
        recipient_user_id,
        notification_type: str,
        title: str,
        message: str,
        *,
        entity_type: str | None = None,
        entity_id=None,
        created_by=None,
        cursor=None,
    ) -> str:
        """
        Create a persistent user notification.

        When cursor is supplied, the notification joins the caller's
        transaction.

        This allows business services such as ClarificationService to
        save workflow records and notifications atomically.
        """

        if not recipient_user_id:
            raise ValueError(
                "Notification recipient is required."
            )

        notification_type = cls._clean_required_text(
            notification_type,
            "Notification type is required.",
        )

        title = cls._clean_required_text(
            title,
            "Notification title is required.",
        )

        message = cls._clean_required_text(
            message,
            "Notification message is required.",
        )

        entity_type = cls._clean_optional_text(
            entity_type
        )

        return NotificationRepository.create(
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by=created_by,
            cursor=cursor,
        )

    @classmethod
    def get_notification(
        cls,
        notification_id,
    ):
        if not notification_id:
            return None

        return NotificationRepository.get_by_id(
            notification_id
        )

    @classmethod
    def get_user_notifications(
        cls,
        user: dict | None,
        *,
        limit: int = 100,
    ) -> list[dict]:
        user_id = cls._get_user_id(
            user
        )

        if not user_id:
            return []

        return (
            NotificationRepository
            .get_by_recipient(
                user_id,
                unread_only=False,
                limit=limit,
            )
        )

    @classmethod
    def get_unread_notifications(
        cls,
        user: dict | None,
        *,
        limit: int = 100,
    ) -> list[dict]:
        user_id = cls._get_user_id(
            user
        )

        if not user_id:
            return []

        return (
            NotificationRepository
            .get_by_recipient(
                user_id,
                unread_only=True,
                limit=limit,
            )
        )

    @classmethod
    def count_unread(
        cls,
        user: dict | None,
    ) -> int:
        user_id = cls._get_user_id(
            user
        )

        if not user_id:
            return 0

        return NotificationRepository.count_unread(
            user_id
        )

    @classmethod
    def mark_as_read(
        cls,
        notification_id,
        user: dict | None,
    ) -> bool:
        if not notification_id:
            raise ValueError(
                "Notification ID is required."
            )

        user_id = cls._require_user_id(
            user
        )

        return NotificationRepository.mark_as_read(
            notification_id,
            user_id,
        )

    @classmethod
    def mark_all_as_read(
        cls,
        user: dict | None,
    ) -> int:
        user_id = cls._require_user_id(
            user
        )

        return (
            NotificationRepository
            .mark_all_as_read(
                user_id
            )
        )

    @classmethod
    def notification_exists_for_entity(
        cls,
        recipient_user_id,
        notification_type: str,
        entity_type: str,
        entity_id,
        *,
        unread_only: bool = False,
        cursor=None,
    ) -> bool:
        if not recipient_user_id:
            return False

        notification_type = cls._clean_optional_text(
            notification_type
        )

        entity_type = cls._clean_optional_text(
            entity_type
        )

        if (
            not notification_type
            or not entity_type
            or not entity_id
        ):
            return False

        return (
            NotificationRepository
            .exists_for_entity(
                recipient_user_id,
                notification_type,
                entity_type,
                entity_id,
                unread_only=unread_only,
                cursor=cursor,
            )
        )

    # ============================================================
    # NOTIFICATION TYPE CONSTANTS
    # ============================================================

    CLARIFICATION_REQUESTED = (
        "CLARIFICATION_REQUESTED"
    )

    CLARIFICATION_RESPONSE_RECEIVED = (
        "CLARIFICATION_RESPONSE_RECEIVED"
    )

    CLARIFICATION_FORWARDED = (
        "CLARIFICATION_FORWARDED"
    )

    CLARIFICATION_RESOLVED = (
        "CLARIFICATION_RESOLVED"
    )

    CLARIFICATION_REOPENED = (
        "CLARIFICATION_REOPENED"
    )

    ADDITIONAL_DOCUMENT_UPLOADED = (
        "ADDITIONAL_DOCUMENT_UPLOADED"
    )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _clean_message(
        message: str,
    ) -> str:
        cleaned = str(
            message or ""
        ).strip()

        if cleaned:
            return cleaned

        return (
            "No additional information "
            "is available."
        )

    @staticmethod
    def _clean_required_text(
        value,
        error_message: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise ValueError(
                error_message
            )

        return cleaned

    @staticmethod
    def _clean_optional_text(
        value,
    ):
        if value is None:
            return None

        cleaned = str(
            value
        ).strip()

        return cleaned or None

    @staticmethod
    def _get_user_id(
        user: dict | None,
    ):
        if not user:
            return None

        return user.get(
            "id"
        )

    @classmethod
    def _require_user_id(
        cls,
        user: dict | None,
    ):
        user_id = cls._get_user_id(
            user
        )

        if not user_id:
            raise ValueError(
                "Authenticated user is required."
            )

        return user_id