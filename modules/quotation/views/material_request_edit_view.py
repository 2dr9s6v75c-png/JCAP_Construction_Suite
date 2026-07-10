import customtkinter as ctk

from tkinter import messagebox

from modules.quotation.services.material_request_service import (
    get_material_request,
    get_material_request_lock_status,
    lock_material_request,
    unlock_material_request,
    update_material_request,
)


class MaterialRequestEditView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        user,
        material_request_id,
        on_cancel=None,
    ):
        super().__init__(
            parent,
            fg_color="#F5F7FA",
            corner_radius=0,
        )

        self.user = user
        self.material_request_id = material_request_id
        self.on_cancel = on_cancel

        self.request = None
        self.lock_acquired = False
        self.lock_released = False
        self.navigation_started = False

        self.try_open_for_edit()

    def try_open_for_edit(self):
        try:
            lock_status = get_material_request_lock_status(
                self.material_request_id
            )

            locked_by = lock_status.get("locked_by")
            current_user_id = str(self.user.get("id"))

            if (
                lock_status.get("locked")
                and str(locked_by) != current_user_id
            ):
                locked_by_name = lock_status.get(
                    "locked_by_name",
                    "another user",
                )
                locked_at = lock_status.get("locked_at")

                message = (
                    "This Material Request is currently being edited "
                    f"by {locked_by_name}."
                )

                if locked_at:
                    message += f"\n\nEditing started: {locked_at}"

                self.show_locked_message(message)
                return

            result = lock_material_request(
                self.material_request_id,
                self.user,
            )

            if not result.get("success"):
                self.show_locked_message(
                    result.get(
                        "message",
                        "Unable to acquire the edit lock.",
                    )
                )
                return

            self.lock_acquired = True
            self.lock_released = False

            self.request = get_material_request(
                self.material_request_id
            )

            if not self.request:
                self.release_lock()
                self.show_locked_message(
                    "Material Request could not be loaded."
                )
                return

            self.build_ui()

        except Exception as error:
            self.release_lock()

            messagebox.showerror(
                "Open Edit View Failed",
                (
                    "Unable to open this Material Request for editing."
                    f"\n\n{error}"
                ),
            )

            self.navigate_back()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_toolbar()
        self.build_form()

    def build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )
        toolbar.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(
            toolbar,
            fg_color="transparent",
        )
        title_block.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=14,
        )

        ctk.CTkLabel(
            title_block,
            text=f"Edit {self.request['mr_number']}",
            font=("Segoe UI", 24, "bold"),
            text_color="#0A2E63",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text="Update Material Request information.",
            font=("Segoe UI", 13),
            text_color="#607D8B",
        ).pack(anchor="w", pady=(2, 0))

        button_frame = ctk.CTkFrame(
            toolbar,
            fg_color="transparent",
        )
        button_frame.grid(
            row=0,
            column=1,
            sticky="e",
            padx=15,
            pady=14,
        )

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.cancel_edit,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Save Changes",
            width=140,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.save_changes,
        ).pack(side="left", padx=5)

    def build_form(self):
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
            pady=(10, 20),
        )

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.add_readonly_field(
            body,
            "MR Number",
            self.request["mr_number"],
            0,
            0,
        )

        self.add_readonly_field(
            body,
            "Project",
            self.format_project(),
            0,
            1,
        )

        self.description_entry = self.add_field(
            body,
            "Material Request Description",
            1,
            0,
            columnspan=2,
        )
        self.description_entry.insert(
            0,
            self.request["material_request_description"],
        )

        self.priority_option = self.add_option(
            body,
            "Priority",
            ["High", "Medium", "Low"],
            2,
            0,
        )
        self.priority_option.set(
            self.request["priority"]
        )

        self.due_date_entry = self.add_field(
            body,
            "Due Date (YYYY-MM-DD)",
            2,
            1,
        )
        self.due_date_entry.insert(
            0,
            str(self.request["due_date"] or ""),
        )

        self.remarks_box = self.add_textbox(
            body,
            "Remarks",
            3,
            0,
            columnspan=2,
        )
        self.remarks_box.insert(
            "1.0",
            self.request["remarks"] or "",
        )

    def show_locked_message(self, message):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=20,
            pady=20,
        )

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
            justify="center",
            wraplength=600,
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="Back",
            width=120,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.navigate_back,
        ).pack(pady=20)

    def validate_changes(self):
        errors = []
        first_invalid = None

        description = self.description_entry.get().strip()
        due_date = self.due_date_entry.get().strip()
        priority = self.priority_option.get().strip()

        if not description:
            errors.append(
                "Material Request Description is required."
            )
            first_invalid = self.description_entry

        if not priority:
            errors.append("Priority is required.")

        if not due_date:
            errors.append("Due Date is required.")

            if first_invalid is None:
                first_invalid = self.due_date_entry

        return errors, first_invalid

    def save_changes(self):
        errors, first_invalid = self.validate_changes()

        if errors:
            messagebox.showwarning(
                "Validation Required",
                (
                    "Please correct the following:\n\n"
                    + "\n".join(
                        f"• {error}" for error in errors
                    )
                ),
            )

            if first_invalid:
                first_invalid.focus_set()

            return

        data = {
            "material_request_description": (
                self.description_entry.get().strip()
            ),
            "priority": self.priority_option.get(),
            "due_date": self.due_date_entry.get().strip(),
            "remarks": self.remarks_box.get(
                "1.0",
                "end",
            ).strip(),
            "assigned_to": self.request["assigned_to"],
        }

        try:
            mr_number = update_material_request(
                self.material_request_id,
                data,
                self.user,
            )

            self.release_lock()

            messagebox.showinfo(
                "Update Complete",
                (
                    f"Material Request {mr_number} "
                    "was updated successfully."
                ),
            )

            self.navigate_back()

        except Exception as error:
            messagebox.showerror(
                "Update Failed",
                (
                    "Unable to update the Material Request."
                    f"\n\n{error}"
                ),
            )

    def cancel_edit(self):
        self.release_lock()
        self.navigate_back()

    def release_lock(self):
        if (
            not self.lock_acquired
            or self.lock_released
        ):
            return

        try:
            unlock_material_request(
                self.material_request_id,
                self.user,
            )

            self.lock_released = True
            self.lock_acquired = False

        except Exception as error:
            # Do not block navigation if unlocking fails.
            # The database lock will still expire automatically.
            print("Unable to release Material Request lock:")
            print(error)

    def navigate_back(self):
        if self.navigation_started:
            return

        self.navigation_started = True

        if self.on_cancel:
            self.on_cancel()

    def destroy(self):
        """
        Safety net.

        This runs when the navigation system replaces or destroys the
        Edit view, including cases where the user leaves without pressing
        Save or Cancel.
        """
        self.release_lock()
        super().destroy()

    def format_project(self):
        code = self.request.get("project_code") or ""
        name = self.request.get("project_name") or ""

        return f"{code} - {name}" if code else name

    def add_field(
        self,
        parent,
        label,
        row,
        column,
        columnspan=1,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=15,
            pady=8,
        )
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        entry = ctk.CTkEntry(
            wrapper,
            height=36,
        )
        entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        return entry

    def add_readonly_field(
        self,
        parent,
        label,
        value,
        row,
        column,
    ):
        entry = self.add_field(
            parent,
            label,
            row,
            column,
        )

        entry.insert(0, value)
        entry.configure(state="disabled")

        return entry

    def add_option(
        self,
        parent,
        label,
        values,
        row,
        column,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=15,
            pady=8,
        )
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        option = ctk.CTkOptionMenu(
            wrapper,
            values=values,
            height=36,
        )
        option.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        return option

    def add_textbox(
        self,
        parent,
        label,
        row,
        column,
        columnspan=1,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=15,
            pady=8,
        )
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        textbox = ctk.CTkTextbox(
            wrapper,
            height=80,
        )
        textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 0),
        )

        return textbox