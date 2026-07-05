from unittest import result

import customtkinter as ctk

from modules.quotation.services.material_request_service import (
    get_material_request,
    lock_material_request,
    unlock_material_request,
    get_material_request_lock_status,
)


class MaterialRequestEditView(ctk.CTkFrame):
    def __init__(self, parent, user, material_request_id, on_cancel=None):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)

        self.user = user
        self.material_request_id = material_request_id
        self.on_cancel = on_cancel
        self.request = None
        self.lock_acquired = False

        self.try_open_for_edit()

    def try_open_for_edit(self):
        lock_status = get_material_request_lock_status(self.material_request_id)

        if lock_status.get("locked") and lock_status.get("locked_by") != self.user["id"]:
            locked_by = lock_status.get("locked_by_name", "another user")
            locked_at = lock_status.get("locked_at")

            message = f"This Material Request is currently being edited by {locked_by}."

            if locked_at:
                message += f"\n\nEditing started: {locked_at}"

            self.show_locked_message(message)
            return

        result = lock_material_request(self.material_request_id, self.user)

        if not result["success"]:
            self.show_locked_message(result["message"])
            return

        self.lock_acquired = True
        self.request = get_material_request(self.material_request_id)
        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            toolbar,
            text=f"Edit {self.request['mr_number']}",
            font=("Segoe UI", 24, "bold"),
            text_color="#0A2E63",
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkButton(
            toolbar,
            text="Cancel",
            width=100,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.cancel_edit,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            toolbar,
            text="Save Changes",
            width=140,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.save_changes_placeholder,
        ).pack(side="right", padx=10)

        body = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        body.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        body.grid_columnconfigure((0, 1), weight=1)

        self.add_readonly_field(body, "MR Number", self.request["mr_number"], 0, 0)
        self.add_readonly_field(body, "Project", self.format_project(), 0, 1)

        self.description_entry = self.add_field(
            body,
            "Material Request Description",
            1,
            0,
            columnspan=2,
        )
        self.description_entry.insert(0, self.request["material_request_description"])

        self.priority_option = self.add_option(
            body,
            "Priority",
            ["High", "Medium", "Low"],
            2,
            0,
        )
        self.priority_option.set(self.request["priority"])

        self.due_date_entry = self.add_field(body, "Due Date (YYYY-MM-DD)", 2, 1)
        self.due_date_entry.insert(0, str(self.request["due_date"] or ""))

        self.remarks_box = self.add_textbox(body, "Remarks", 3, 0, columnspan=2)
        self.remarks_box.insert("1.0", self.request["remarks"] or "")

    def show_locked_message(self, message):
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Material Request Locked",
            font=("Segoe UI", 24, "bold"),
            text_color="#E53935",
        ).pack(pady=(80, 10))

        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 14),
            text_color="#607D8B",
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="Back",
            width=120,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.on_cancel,
        ).pack(pady=20)

    def cancel_edit(self):
        if self.lock_acquired:
            unlock_material_request(self.material_request_id, self.user)

        if self.on_cancel:
            self.on_cancel()

    def save_changes_placeholder(self):
        data = {
            "material_request_description": self.description_entry.get().strip(),
            "priority": self.priority_option.get(),
            "due_date": self.due_date_entry.get().strip(),
            "remarks": self.remarks_box.get("1.0", "end").strip(),
            "assigned_to": self.request["assigned_to"],
        }

        try:
            from modules.quotation.services.material_request_service import update_material_request

            mr_number = update_material_request(
                self.material_request_id,
                data,
                self.user,
            )

            unlock_material_request(self.material_request_id, self.user)

            print(f"Material Request updated successfully: {mr_number}")

            if self.on_cancel:
                self.on_cancel()

        except Exception as e:
            print("Failed to update Material Request:")
            print(e)

    def format_project(self):
        code = self.request.get("project_code") or ""
        name = self.request.get("project_name") or ""
        return f"{code} - {name}" if code else name

    def add_field(self, parent, label, row, column, columnspan=1):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(row=0, column=0, sticky="w")

        entry = ctk.CTkEntry(wrapper, height=36)
        entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return entry

    def add_readonly_field(self, parent, label, value, row, column):
        entry = self.add_field(parent, label, row, column)
        entry.insert(0, value)
        entry.configure(state="disabled")
        return entry

    def add_option(self, parent, label, values, row, column):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(row=0, column=0, sticky="w")

        option = ctk.CTkOptionMenu(wrapper, values=values, height=36)
        option.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return option

    def add_textbox(self, parent, label, row, column, columnspan=1):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(row=0, column=0, sticky="w")

        textbox = ctk.CTkTextbox(wrapper, height=80)
        textbox.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return textbox