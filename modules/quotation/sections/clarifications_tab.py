from datetime import datetime

import customtkinter as ctk

from core.theme import JCAPTheme


class ClarificationsTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        clarifications=None,
        can_record=False,
        on_record=None,
        on_open=None,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
        )

        self.clarifications = list(
            clarifications or []
        )
        self.can_record = can_record
        self.on_record = on_record
        self.on_open = on_open

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_list()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=15,
            pady=(15, 10),
        )

        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=(
                "Supplier Clarifications "
                f"({len(self.clarifications)})"
            ),
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        if self.can_record and self.on_record:
            ctk.CTkButton(
                header,
                text="+ Record Supplier Clarification",
                width=220,
                height=36,
                fg_color=JCAPTheme.PRIMARY_BLUE,
                hover_color=JCAPTheme.DARK_BLUE,
                command=self.on_record,
            ).grid(
                row=0,
                column=1,
                sticky="e",
            )

    def build_list(self):
        container = ctk.CTkScrollableFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=12,
        )
        container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=15,
            pady=(0, 15),
        )

        container.grid_columnconfigure(0, weight=1)

        if not self.clarifications:
            self.build_empty_state(container)
            return

        for index, clarification in enumerate(
            self.clarifications
        ):
            self.build_card(
                container,
                clarification,
                index,
            )

    def build_empty_state(self, parent):
        ctk.CTkLabel(
            parent,
            text="No supplier clarifications recorded.",
            font=("Segoe UI", 15, "bold"),
            text_color=JCAPTheme.TEXT_MUTED,
        ).grid(
            row=0,
            column=0,
            pady=(70, 8),
        )

        ctk.CTkLabel(
            parent,
            text=(
                "Supplier questions and Engineering responses "
                "will appear here."
            ),
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_MUTED,
        ).grid(
            row=1,
            column=0,
            pady=(0, 70),
        )

    def build_card(
        self,
        parent,
        clarification,
        row,
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=8,
            pady=7,
        )

        card.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        content.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=18,
            pady=15,
        )

        content.grid_columnconfigure(0, weight=1)

        subject = (
            clarification.get("subject")
            or "Supplier Clarification"
        )

        ctk.CTkLabel(
            content,
            text=subject,
            font=("Segoe UI", 15, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
        )

        status = clarification.get("status") or ""

        status_label = ctk.CTkLabel(
            content,
            text=status,
            width=190,
            height=28,
            corner_radius=14,
            fg_color=self.get_status_color(status),
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
        )
        status_label.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(15, 0),
        )

        supplier = (
            clarification.get("supplier_name")
            or "Not specified"
        )

        assigned_to = (
            clarification.get("assigned_full_name")
            or "Not assigned"
        )

        details = (
            f"Supplier: {supplier}\n"
            f"Assigned To: {assigned_to}\n"
            f"Created: "
            f"{self.format_datetime(clarification.get('created_at'))}"
        )

        ctk.CTkLabel(
            content,
            text=details,
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_MUTED,
            justify="left",
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        if self.on_open:
            ctk.CTkButton(
                content,
                text="Open Clarification",
                width=150,
                height=34,
                fg_color=JCAPTheme.PRIMARY_BLUE,
                hover_color=JCAPTheme.DARK_BLUE,
                command=lambda item=clarification: (
                    self.on_open(item)
                ),
            ).grid(
                row=1,
                column=1,
                sticky="se",
                padx=(15, 0),
            )

    @staticmethod
    def get_status_color(status):
        colors = {
            "Awaiting Engineering Response": "#FB8C00",
            "Response Ready": "#43A047",
            "Forwarded to Supplier": "#00ACC1",
            "Resolved": "#607D8B",
            "Cancelled": "#E53935",
        }

        return colors.get(
            str(status or "").strip(),
            "#607D8B",
        )

    @staticmethod
    def format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(value or "")