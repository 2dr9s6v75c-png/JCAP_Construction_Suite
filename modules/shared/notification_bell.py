import customtkinter as ctk

from core.notifications.notification_service import (
    NotificationService,
)
from core.theme import JCAPTheme


class NotificationBell(ctk.CTkFrame):
    """
    Reusable notification bell with unread-count badge.

    Responsibilities:
    - Display the notification bell
    - Load the authenticated user's unread count
    - Hide the badge when the count is zero
    - Expose an on_click callback for the future panel
    - Allow manual and scheduled refreshes

    Notification loading and persistence remain inside
    NotificationService.
    """

    DEFAULT_REFRESH_INTERVAL_MS = 60_000

    def __init__(
        self,
        parent,
        user,
        on_click=None,
        *,
        refresh_interval_ms=None,
        auto_refresh=True,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.user = user
        self.on_click = on_click

        self.refresh_interval_ms = (
            int(refresh_interval_ms)
            if refresh_interval_ms is not None
            else self.DEFAULT_REFRESH_INTERVAL_MS
        )

        self.auto_refresh = bool(
            auto_refresh
        )

        self.unread_count = 0
        self.refresh_job = None

        self.build_ui()
        self.refresh()

        if self.auto_refresh:
            self.schedule_refresh()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.bell_button = ctk.CTkButton(
            self,
            text="🔔",
            width=42,
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=JCAPTheme.BACKGROUND,
            text_color=JCAPTheme.DARK_BLUE,
            font=("Segoe UI Emoji", 19),
            command=self.handle_click,
        )

        self.bell_button.grid(
            row=0,
            column=0,
            padx=2,
            pady=2,
        )

        self.badge_label = ctk.CTkLabel(
            self,
            text="",
            width=20,
            height=20,
            corner_radius=10,
            fg_color=JCAPTheme.DELETE,
            text_color="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
        )

        self.hide_badge()

    # ============================================================
    # DATA
    # ============================================================

    def refresh(self):
        """
        Reload the authenticated user's unread count.

        Errors are intentionally contained so a temporary database
        issue does not crash the main application header.
        """

        try:
            unread_count = (
                NotificationService.count_unread(
                    self.user
                )
            )

            self.set_unread_count(
                unread_count
            )

        except Exception as error:
            print(
                "Unable to refresh notification count:",
                error,
            )

    def set_unread_count(
        self,
        unread_count,
    ):
        try:
            count = max(
                int(unread_count or 0),
                0,
            )

        except (TypeError, ValueError):
            count = 0

        self.unread_count = count

        if count <= 0:
            self.hide_badge()
            return

        badge_text = (
            "99+"
            if count > 99
            else str(count)
        )

        self.badge_label.configure(
            text=badge_text
        )

        self.show_badge()

    # ============================================================
    # BADGE
    # ============================================================

    def show_badge(self):
        self.badge_label.place(
            relx=1.0,
            rely=0.0,
            anchor="ne",
            x=2,
            y=-2,
        )

        self.badge_label.lift()

    def hide_badge(self):
        self.badge_label.place_forget()

    # ============================================================
    # CLICK
    # ============================================================

    def handle_click(self):
        if self.on_click:
            self.on_click()

    # ============================================================
    # AUTO REFRESH
    # ============================================================

    def schedule_refresh(self):
        self.cancel_scheduled_refresh()

        if not self.auto_refresh:
            return

        if self.refresh_interval_ms < 1_000:
            self.refresh_interval_ms = 1_000

        self.refresh_job = self.after(
            self.refresh_interval_ms,
            self.run_scheduled_refresh,
        )

    def run_scheduled_refresh(self):
        self.refresh_job = None

        if not self.winfo_exists():
            return

        self.refresh()
        self.schedule_refresh()

    def cancel_scheduled_refresh(self):
        if self.refresh_job is None:
            return

        try:
            self.after_cancel(
                self.refresh_job
            )
        except Exception:
            pass

        self.refresh_job = None

    # ============================================================
    # CLEANUP
    # ============================================================

    def destroy(self):
        self.cancel_scheduled_refresh()
        super().destroy()