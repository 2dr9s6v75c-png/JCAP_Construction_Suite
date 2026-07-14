from datetime import datetime

import customtkinter as ctk

from core.notifications.notification_service import (
    NotificationService,
)
from core.theme import JCAPTheme


class NotificationPanel(ctk.CTkFrame):
    """
    Reusable read-only notification center.

    Version 1 responsibilities:
    - Load notifications for the authenticated user
    - Display read and unread states
    - Display title, message, sender, and timestamp
    - Refresh the notification list
    - Close the panel through a callback

    Navigation and mark-as-read behavior will be added after
    the read-only panel has passed its UI tests.
    """

    def __init__(
        self,
        parent,
        user,
        on_close=None,
        on_notification_selected=None,
        *,
        limit=50,
    ):
        super().__init__(
            parent,
            width=430,
            height=620,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
            border_width=1,
            border_color=JCAPTheme.BORDER,
        )

        self.user = user
        self.on_close = on_close
        self.on_notification_selected = (
            on_notification_selected
        )

        self.limit = max(
            int(limit),
            1,
        )

        self.notifications = []

        self.grid_propagate(False)

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.build_ui()
        self.load_notifications()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.build_header()
        self.build_notification_area()
        self.build_footer()

    def build_header(self):
        self.header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(14, 8),
        )

        self.header.grid_columnconfigure(
            0,
            weight=1,
        )

        title_frame = ctk.CTkFrame(
            self.header,
            fg_color="transparent",
        )

        title_frame.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            title_frame,
            text="Notifications",
            font=("Segoe UI", 20, "bold"),
            text_color=JCAPTheme.TEXT,
        ).pack(
            anchor="w",
        )

        self.summary_label = ctk.CTkLabel(
            title_frame,
            text="Loading notifications...",
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )

        self.summary_label.pack(
            anchor="w",
            pady=(2, 0),
        )

        self.refresh_button = ctk.CTkButton(
            self.header,
            text="Refresh",
            width=80,
            height=32,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.PRIMARY_BLUE_HOVER,
            command=self.load_notifications,
        )

        self.refresh_button.grid(
            row=0,
            column=1,
            padx=(8, 5),
        )

        self.close_button = ctk.CTkButton(
            self.header,
            text="✕",
            width=36,
            height=32,
            fg_color="transparent",
            hover_color=JCAPTheme.BACKGROUND,
            text_color=JCAPTheme.TEXT,
            font=("Segoe UI", 14, "bold"),
            command=self.close_panel,
        )

        self.close_button.grid(
            row=0,
            column=2,
            padx=(5, 0),
        )

    def build_notification_area(self):
        self.notification_area = ctk.CTkScrollableFrame(
            self,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=10,
        )

        self.notification_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(4, 8),
        )

        self.notification_area.grid_columnconfigure(
            0,
            weight=1,
        )

    def build_footer(self):
        self.footer = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        self.footer.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=16,
            pady=(4, 14),
        )

        self.footer.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            self.footer,
            text=(
                "Notification navigation and read controls "
                "will be enabled in the next milestone."
            ),
            font=("Segoe UI", 10),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

    # ============================================================
    # DATA
    # ============================================================

    def load_notifications(self):
        self.set_loading_state(
            True
        )

        try:
            self.notifications = (
                NotificationService
                .get_user_notifications(
                    self.user,
                    limit=self.limit,
                )
            )

            self.render_notifications()

        except Exception as error:
            self.render_error(
                error
            )

        finally:
            self.set_loading_state(
                False
            )

    def set_loading_state(
        self,
        loading,
    ):
        if loading:
            self.refresh_button.configure(
                state="disabled",
                text="Loading...",
            )
        else:
            self.refresh_button.configure(
                state="normal",
                text="Refresh",
            )

    # ============================================================
    # RENDERING
    # ============================================================

    def clear_notifications(self):
        for widget in (
            self.notification_area
            .winfo_children()
        ):
            widget.destroy()

    def render_notifications(self):
        self.clear_notifications()

        total_count = len(
            self.notifications
        )

        unread_count = sum(
            1
            for notification in self.notifications
            if not notification.get(
                "is_read",
                False,
            )
        )

        self.summary_label.configure(
            text=(
                f"{unread_count} unread  |  "
                f"{total_count} total"
            )
        )

        if not self.notifications:
            self.render_empty_state()
            return

        for row, notification in enumerate(
            self.notifications
        ):
            self.build_notification_card(
                notification,
                row,
            )

    def render_empty_state(self):
        empty_frame = ctk.CTkFrame(
            self.notification_area,
            fg_color="transparent",
        )

        empty_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=70,
        )

        ctk.CTkLabel(
            empty_frame,
            text="🔔",
            font=("Segoe UI Emoji", 30),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            pady=(0, 10),
        )

        ctk.CTkLabel(
            empty_frame,
            text="No notifications",
            font=("Segoe UI", 15, "bold"),
            text_color=JCAPTheme.TEXT,
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text=(
                "Workflow notifications assigned to you "
                "will appear here."
            ),
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
            wraplength=330,
            justify="center",
        ).pack(
            pady=(5, 0),
        )

    def render_error(
        self,
        error,
    ):
        self.clear_notifications()

        self.summary_label.configure(
            text="Unable to load notifications"
        )

        error_frame = ctk.CTkFrame(
            self.notification_area,
            fg_color="transparent",
        )

        error_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=60,
        )

        ctk.CTkLabel(
            error_frame,
            text="Notification loading failed",
            font=("Segoe UI", 14, "bold"),
            text_color=JCAPTheme.DELETE,
        ).pack()

        ctk.CTkLabel(
            error_frame,
            text=str(
                error or ""
            ),
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
            wraplength=330,
            justify="center",
        ).pack(
            pady=(8, 0),
        )

    def build_notification_card(
        self,
        notification,
        row,
    ):
        is_read = bool(
            notification.get(
                "is_read",
                False,
            )
        )

        card_color = (
            JCAPTheme.CARD
            if is_read
            else "#EAF3FF"
        )

        card = ctk.CTkFrame(
            self.notification_area,
            fg_color=card_color,
            corner_radius=10,
            border_width=1,
            border_color=JCAPTheme.BORDER,
        )

        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=5,
            pady=5,
        )

        card.grid_columnconfigure(
            1,
            weight=1,
        )

        indicator = ctk.CTkLabel(
            card,
            text=(
                "✓"
                if is_read
                else "●"
            ),
            width=28,
            font=("Segoe UI", 13, "bold"),
            text_color=(
                JCAPTheme.TEXT_SECONDARY
                if is_read
                else JCAPTheme.PRIMARY_BLUE
            ),
        )

        indicator.grid(
            row=0,
            column=0,
            rowspan=4,
            sticky="n",
            padx=(10, 4),
            pady=13,
        )

        title = str(
            notification.get(
                "title",
                "Notification",
            )
            or "Notification"
        ).strip()

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT,
            anchor="w",
            justify="left",
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(4, 12),
            pady=(12, 3),
        )

        message = str(
            notification.get(
                "message",
                "",
            )
            or ""
        ).strip()

        ctk.CTkLabel(
            card,
            text=message,
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=345,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(4, 12),
            pady=(0, 5),
        )

        sender = (
            notification.get(
                "created_by_full_name"
            )
            or notification.get(
                "created_by_username"
            )
            or "System"
        )

        ctk.CTkLabel(
            card,
            text=f"From: {sender}",
            font=("Segoe UI", 10),
            text_color=JCAPTheme.TEXT_SECONDARY,
            anchor="w",
        ).grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(4, 12),
        )

        created_at = self.format_datetime(
            notification.get(
                "created_at"
            )
        )

        ctk.CTkLabel(
            card,
            text=created_at,
            font=("Segoe UI", 10),
            text_color=JCAPTheme.TEXT_SECONDARY,
            anchor="w",
        ).grid(
            row=3,
            column=1,
            sticky="ew",
            padx=(4, 12),
            pady=(3, 12),
        )

        if self.on_notification_selected:
            card.bind(
                "<Button-1>",
                lambda event, item=notification: (
                    self.handle_notification_selected(
                        item
                    )
                ),
            )

            for child in card.winfo_children():
                child.bind(
                    "<Button-1>",
                    lambda event, item=notification: (
                        self.handle_notification_selected(
                            item
                        )
                    ),
                )

                child.configure(
                    cursor="hand2"
                )

            card.configure(
                cursor="hand2"
            )

    # ============================================================
    # CALLBACKS
    # ============================================================

    def handle_notification_selected(
        self,
        notification,
    ):
        if self.on_notification_selected:
            self.on_notification_selected(
                notification
            )

    def close_panel(self):
        if self.on_close:
            self.on_close()
        else:
            self.destroy()

    # ============================================================
    # DISPLAY HELPERS
    # ============================================================

    @staticmethod
    def format_datetime(
        value,
    ):
        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(
            value or ""
        )