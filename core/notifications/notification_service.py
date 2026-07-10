from tkinter import messagebox
from typing import Iterable


class NotificationService:
    """
    Centralized user-facing notification service.

    Version 1 uses native Windows/Tkinter dialogs.
    Later, the implementation can be replaced with toast notifications
    without changing every view in the application.
    """

    APP_TITLE = "JCAP Construction Suite"

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
        full_message = cls._clean_message(message)

        if error is not None:
            error_text = str(error).strip()

            if error_text:
                full_message = (
                    f"{full_message}\n\n"
                    f"Technical details:\n{error_text}"
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

    @staticmethod
    def _clean_message(message: str) -> str:
        cleaned = str(message or "").strip()

        if cleaned:
            return cleaned

        return "No additional information is available."