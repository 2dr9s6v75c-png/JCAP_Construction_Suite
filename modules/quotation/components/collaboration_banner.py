from datetime import datetime
from tkinter import messagebox
from core.security.permissions import PermissionService
import customtkinter as ctk

from modules.quotation.services.material_request_service import (
    force_unlock_material_request,
    get_material_request_lock_status,
)


class CollaborationBanner(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        material_request_id,
        current_user,
        on_status_change=None,
    ):
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=14,
        )

        self.material_request_id = material_request_id
        self.current_user = current_user
        self.on_status_change = on_status_change

        self.current_status = None
        self.force_unlock_button = None

        self.build_ui()
        self.refresh_status()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="Record Collaboration Status",
            font=("Segoe UI", 15, "bold"),
            text_color="#0A2E63",
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(12, 2),
        )

        self.status_label = ctk.CTkLabel(
            self,
            text="Checking status...",
            font=("Segoe UI", 13, "bold"),
            text_color="#607D8B",
        )
        self.status_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(2, 4),
        )

        self.detail_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color="#607D8B",
        )
        self.detail_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 12),
        )

        self.button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.button_frame.grid(
            row=0,
            column=1,
            rowspan=3,
            sticky="e",
            padx=18,
            pady=14,
        )

        self.refresh_button = ctk.CTkButton(
            self.button_frame,
            text="Refresh Status",
            width=130,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.refresh_status,
        )
        self.refresh_button.pack(
            side="left",
            padx=5,
        )

        self.force_unlock_button = ctk.CTkButton(
            self.button_frame,
            text="Force Unlock",
            width=120,
            fg_color="#E53935",
            hover_color="#B71C1C",
            command=self.force_unlock,
        )

        # Hidden by default. It appears only when:
        # 1. another user owns the lock, and
        # 2. the current user is an Administrator.
        self.force_unlock_button.pack(
            side="left",
            padx=5,
        )
        self.force_unlock_button.pack_forget()

    def refresh_status(self):
        try:
            status = get_material_request_lock_status(
                self.material_request_id
            )

        except Exception as error:
            self.show_status_error(error)
            return

        self.current_status = status

        is_locked = status.get("locked", False)
        locked_by = status.get("locked_by")
        locked_by_name = (
            status.get("locked_by_name")
            or "Unknown User"
        )
        lock_expires_at = status.get("lock_expires_at")

        current_user_id = str(
            self.current_user.get("id", "")
        )

        if not is_locked:
            self.show_available_status()
            return

        expiry_text = self.format_datetime(
            lock_expires_at
        )

        if str(locked_by) == current_user_id:
            self.show_locked_by_me_status(
                expiry_text=expiry_text
            )
            return

        self.show_locked_by_other_status(
            locked_by_name=locked_by_name,
            expiry_text=expiry_text,
        )

    def show_available_status(self):
        self.configure(
            fg_color="#E8F5E9"
        )

        self.status_label.configure(
            text="🟢 Available for editing",
            text_color="#2E7D32",
        )

        self.detail_label.configure(
            text=(
                "This Material Request is currently "
                "available."
            ),
            text_color="#2E7D32",
        )

        self.hide_force_unlock_button()

        if self.on_status_change:
            self.on_status_change("available")

    def show_locked_by_me_status(
        self,
        expiry_text,
    ):
        self.configure(
            fg_color="#FFF3E0"
        )

        self.status_label.configure(
            text="🟠 Currently locked by you",
            text_color="#EF6C00",
        )

        self.detail_label.configure(
            text=(
                "Your edit lock expires at "
                f"{expiry_text}."
            ),
            text_color="#EF6C00",
        )

        self.hide_force_unlock_button()

        if self.on_status_change:
            self.on_status_change("locked_by_me")

    def show_locked_by_other_status(
        self,
        locked_by_name,
        expiry_text,
    ):
        self.configure(
            fg_color="#FFEBEE"
        )

        self.status_label.configure(
            text=f"🔴 Locked by {locked_by_name}",
            text_color="#C62828",
        )

        self.detail_label.configure(
            text=(
                "Editing is disabled. "
                f"Lock expires at {expiry_text}."
            ),
            text_color="#C62828",
        )

        if self.is_administrator():
            self.show_force_unlock_button()
        else:
            self.hide_force_unlock_button()

        if self.on_status_change:
            self.on_status_change("locked_by_other")

    def show_status_error(self, error):
        self.configure(
            fg_color="#FFF8E1"
        )

        self.status_label.configure(
            text="Unable to check collaboration status",
            text_color="#F57F17",
        )

        self.detail_label.configure(
            text=str(error),
            text_color="#F57F17",
        )

        self.hide_force_unlock_button()

        if self.on_status_change:
            self.on_status_change("status_error")

    def force_unlock(self):
        if not self.is_administrator():
            messagebox.showerror(
                "Permission Denied",
                (
                    "Only an Administrator can "
                    "force-unlock a Material Request."
                ),
            )
            return

        status = self.current_status or {}

        locked_by_name = (
            status.get("locked_by_name")
            or "Unknown User"
        )

        confirmed = messagebox.askyesno(
            "Force Unlock Material Request",
            (
                "Force-unlock this Material Request?\n\n"
                f"Current lock owner: {locked_by_name}\n\n"
                "Use this only when the user cannot "
                "release the lock normally."
            ),
        )

        if not confirmed:
            return

        try:
            mr_number = force_unlock_material_request(
                self.material_request_id,
                self.current_user,
            )

            messagebox.showinfo(
                "Force Unlock Complete",
                (
                    f"Material Request {mr_number} "
                    "is now available for editing."
                ),
            )

            self.refresh_status()

        except Exception as error:
            messagebox.showerror(
                "Force Unlock Failed",
                str(error),
            )

    def is_administrator(self):
        return PermissionService.can_force_unlock_material_request(
            self.current_user
        )

    def show_force_unlock_button(self):
        if not self.force_unlock_button.winfo_manager():
            self.force_unlock_button.pack(
                side="left",
                padx=5,
            )

    def hide_force_unlock_button(self):
        if self.force_unlock_button.winfo_manager():
            self.force_unlock_button.pack_forget()

    @staticmethod
    def format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(value or "")