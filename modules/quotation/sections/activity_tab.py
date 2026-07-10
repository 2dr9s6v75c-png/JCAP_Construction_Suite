from datetime import date, datetime

import customtkinter as ctk


class ActivityTab(ctk.CTkFrame):
    def __init__(self, parent, activities=None):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.activities = activities or []

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        if not self.activities:
            ctk.CTkLabel(
                self,
                text="No activity recorded.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).grid(
                row=0,
                column=0,
                pady=40,
            )
            return

        for index, activity in enumerate(self.activities):
            self.create_activity_card(
                activity=activity,
                row=index,
            )

    def create_activity_card(self, activity, row):
        activity_card = ctk.CTkFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        activity_card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=15,
            pady=8,
        )
        activity_card.grid_columnconfigure(0, weight=1)

        details = activity.get("details") or "Activity recorded."
        user_name = activity.get("user") or "System"
        created_at = self.format_datetime(
            activity.get("created_at")
        )

        ctk.CTkLabel(
            activity_card,
            text=details,
            font=("Segoe UI", 13, "bold"),
            text_color="#111827",
            anchor="w",
            justify="left",
            wraplength=900,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(10, 2),
        )

        ctk.CTkLabel(
            activity_card,
            text=f"{user_name} | {created_at}",
            font=("Segoe UI", 12),
            text_color="#607D8B",
            anchor="w",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=15,
            pady=(0, 10),
        )

    @staticmethod
    def format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %I:%M %p")

        if isinstance(value, date):
            return value.strftime("%d %b %Y")

        return str(value or "")