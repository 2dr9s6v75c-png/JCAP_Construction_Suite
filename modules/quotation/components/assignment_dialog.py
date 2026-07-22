"""
JCAP Construction Suite
Material Request Assignment Dialog

Reusable Phase 1 dialog for assigning or reassigning a Material Request.
The dialog collects user input only. Business rules and persistence remain
inside MaterialRequestAssignmentProcess.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from core.organization.organization_service import OrganizationService


class AssignmentDialog(ctk.CTkToplevel):
    """Collect a purchasing officer and optional assignment remarks."""

    MODE_ASSIGN = "assign"
    MODE_REASSIGN = "reassign"

    def __init__(
        self,
        parent,
        *,
        mode: str = MODE_ASSIGN,
        current_assignee_id=None,
        on_submit: Callable[[dict[str, Any]], None] | None = None,
    ):
        super().__init__(parent)

        if mode not in {self.MODE_ASSIGN, self.MODE_REASSIGN}:
            raise ValueError(
                "Assignment dialog mode must be 'assign' or 'reassign'."
            )

        self.mode = mode
        self.current_assignee_id = (
            str(current_assignee_id)
            if current_assignee_id
            else None
        )
        self.on_submit = on_submit

        self.user_lookup: dict[str, dict[str, Any]] = {}

        self.title(
            "Assign Material Request"
            if self.mode == self.MODE_ASSIGN
            else "Reassign Material Request"
        )
        self.geometry("520x430")
        self.resizable(False, False)
        self.configure(fg_color="#F5F7FA")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)

        self.build_ui()
        self.load_users()
        self.center_on_parent(parent)
        self.after(100, self.focus_dialog)

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=(
                "Assign Material Request"
                if self.mode == self.MODE_ASSIGN
                else "Reassign Material Request"
            ),
            font=("Segoe UI", 22, "bold"),
            text_color="#0A2E63",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(18, 4),
        )

        ctk.CTkLabel(
            header,
            text="Select the purchasing officer responsible for this request.",
            font=("Segoe UI", 13),
            text_color="#607D8B",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

        body = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        body.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=20,
        )
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            body,
            text="Purchasing Officer",
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(18, 6),
        )

        self.assignee_option = ctk.CTkOptionMenu(
            body,
            values=["Loading users..."],
            height=38,
            fg_color="#0D47A1",
            button_color="#0A2E63",
            button_hover_color="#08254F",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#111827",
            text_color="#FFFFFF",
        )
        self.assignee_option.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
        )

        ctk.CTkLabel(
            body,
            text="Remarks (Optional)",
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=20,
            pady=(18, 6),
        )

        self.remarks_box = ctk.CTkTextbox(
            body,
            height=105,
            fg_color="#F5F7FA",
            text_color="#111827",
            border_width=1,
            border_color="#D8E0EA",
        )
        self.remarks_box.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
        )

        actions = ctk.CTkFrame(
            body,
            fg_color="transparent",
        )
        actions.grid(
            row=4,
            column=0,
            sticky="e",
            padx=20,
            pady=20,
        )

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=100,
            height=36,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.close_dialog,
        ).pack(side="left", padx=(0, 8))

        self.submit_button = ctk.CTkButton(
            actions,
            text=(
                "Assign"
                if self.mode == self.MODE_ASSIGN
                else "Reassign"
            ),
            width=110,
            height=36,
            fg_color=(
                "#00ACC1"
                if self.mode == self.MODE_ASSIGN
                else "#8E24AA"
            ),
            hover_color=(
                "#00838F"
                if self.mode == self.MODE_ASSIGN
                else "#6A1B9A"
            ),
            command=self.submit,
        )
        self.submit_button.pack(side="left")

    # ============================================================
    # USER DATA
    # ============================================================

    def load_users(self):
        try:
            users = OrganizationService.get_active_users()
            selectable_users = []

            for user in users:
                user_id = user.get("id")
                full_name = str(
                    user.get("full_name") or ""
                ).strip()

                if not user_id or not full_name:
                    continue

                if (
                    self.mode == self.MODE_REASSIGN
                    and self.current_assignee_id
                    and str(user_id) == self.current_assignee_id
                ):
                    continue

                selectable_users.append(user)

            self.user_lookup = {
                self.format_user_name(user): user
                for user in selectable_users
            }

            user_names = list(self.user_lookup.keys())

            if not user_names:
                self.assignee_option.configure(
                    values=["No active users available"],
                    state="disabled",
                )
                self.assignee_option.set(
                    "No active users available"
                )
                self.submit_button.configure(state="disabled")
                return

            self.assignee_option.configure(
                values=user_names,
                state="normal",
            )
            self.assignee_option.set(user_names[0])

        except Exception as error:
            self.assignee_option.configure(
                values=["Unable to load users"],
                state="disabled",
            )
            self.assignee_option.set("Unable to load users")
            self.submit_button.configure(state="disabled")

            NotificationService.error(
                "Unable to load active users.",
                title="Assignment Unavailable",
                error=error,
            )

    @staticmethod
    def format_user_name(user):
        full_name = str(
            user.get("full_name") or ""
        ).strip()
        username = str(
            user.get("username") or ""
        ).strip()

        if username:
            return f"{full_name} ({username})"

        return full_name

    # ============================================================
    # SUBMISSION
    # ============================================================

    def submit(self):
        selected_name = self.assignee_option.get()
        selected_user = self.user_lookup.get(selected_name)

        if not selected_user:
            NotificationService.validation(
                ["Purchasing Officer is required."]
            )
            return

        remarks = (
            self.remarks_box
            .get("1.0", "end")
            .strip()
        )

        payload = {
            "assigned_to": selected_user["id"],
            "assigned_to_name": selected_user["full_name"],
            "remarks": remarks or None,
        }

        try:
            if self.on_submit:
                self.on_submit(payload)

            self.close_dialog()

        except Exception as error:
            NotificationService.error(
                "Unable to complete the assignment request.",
                title="Assignment Failed",
                error=error,
            )

    # ============================================================
    # WINDOW HELPERS
    # ============================================================

    def focus_dialog(self):
        self.lift()
        self.focus_force()

    def close_dialog(self):
        try:
            self.grab_release()
        except Exception:
            pass

        self.destroy()

    def center_on_parent(self, parent):
        self.update_idletasks()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = self.winfo_width()
        height = self.winfo_height()

        x = parent_x + max(
            (parent_width - width) // 2,
            0,
        )
        y = parent_y + max(
            (parent_height - height) // 2,
            0,
        )

        self.geometry(f"+{x}+{y}")