"""
JCAP Construction Suite
Notification Service

Centralized user-facing notifications for Phase 1.
"""

from tkinter import messagebox
from typing import Iterable


class NotificationService:
    """Standardized application notifications."""

    @staticmethod
    def success(message, title="Success", parent=None):
        return messagebox.showinfo(
            title,
            message,
            parent=parent,
        )

    @staticmethod
    def info(message, title="Information", parent=None):
        return messagebox.showinfo(
            title,
            message,
            parent=parent,
        )

    @staticmethod
    def warning(message, title="Warning", parent=None):
        return messagebox.showwarning(
            title,
            message,
            parent=parent,
        )

    @staticmethod
    def error(
        message,
        title="Error",
        parent=None,
        error=None,
    ):
        final_message = str(message)

        if error is not None:
            final_message = (
                f"{final_message}\n\n"
                f"Details: {error}"
            )

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
            error_list = ["Please review the form fields."]

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