"""
JCAP Construction Suite
Notification Service

Centralized popup notifications and persistent notification access.
"""

from tkinter import messagebox
from typing import Iterable

from core.database.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationService:
    """Popup dialogs + notification center access."""

    # ==========================================================
    # POPUP MESSAGES
    # ==========================================================

    @staticmethod
    def success(message, title="Success", parent=None):
        return messagebox.showinfo(title, message, parent=parent)

    @staticmethod
    def info(message, title="Information", parent=None):
        return messagebox.showinfo(title, message, parent=parent)

    @staticmethod
    def warning(message, title="Warning", parent=None):
        return messagebox.showwarning(title, message, parent=parent)

    @staticmethod
    def error(
        message,
        title="Error",
        parent=None,
        error=None,
    ):
        final_message = str(message)

        if error is not None:
            final_message += f"\n\nDetails: {error}"

        return messagebox.showerror(
            title,
            final_message,
            parent=parent,
        )

    @staticmethod
    def validation(
        errors: Iterable[str],
        title="Validation Required",
        parent=None,
    ):
        error_list = [
            str(error).strip()
            for error in errors
            if str(error).strip()
        ]

        if not error_list:
            error_list = [
                "Please review the form fields."
            ]

        message = (
            "Please correct the following:\n\n"
            + "\n".join(
                f"• {error}"
                for error in error_list
            )
        )

        return messagebox.showwarning(
            title,
            message,
            parent=parent,
        )

    @staticmethod
    def confirm(
        message,
        title="Confirm",
        parent=None,
    ):
        return messagebox.askyesno(
            title,
            message,
            parent=parent,
        )

    # ==========================================================
    # PERSISTENT NOTIFICATIONS
    # ==========================================================

    @staticmethod
    def count_unread(
        user,
        *,
        cursor=None,
    ):
        if not user:
            return 0

        return NotificationRepository.count_unread(
            user["id"],
            cursor=cursor,
        )

    @staticmethod
    def get_user_notifications(
        user,
        *,
        limit=50,
        unread_only=False,
        cursor=None,
    ):
        if not user:
            return []

        return NotificationRepository.get_by_recipient(
            user["id"],
            unread_only=unread_only,
            limit=limit,
            cursor=cursor,
        )

    @staticmethod
    def mark_as_read(
        notification_id,
        user,
        *,
        cursor=None,
    ):
        return NotificationRepository.mark_as_read(
            notification_id,
            user["id"],
            cursor=cursor,
        )

    @staticmethod
    def mark_all_as_read(
        user,
        *,
        cursor=None,
    ):
        return NotificationRepository.mark_all_as_read(
            user["id"],
            cursor=cursor,
        )