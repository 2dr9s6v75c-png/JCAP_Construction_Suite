import customtkinter as ctk
from datetime import date
from tkinter import filedialog
from modules.quotation.services.material_request_service import create_material_request
from modules.quotation.components.request_toolbar import RequestToolbar
import os

from core.master_data.project_service import get_active_projects, get_active_users


class MaterialRequestView(ctk.CTkFrame):
    def __init__(self, parent, user, on_back=None):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)

        self.user = user
        self.on_back = on_back
        self.attachments = []

        self.projects = get_active_projects()
        self.users = get_active_users()

        self.project_lookup = {
            project["project_name"]: project for project in self.projects
        }

        self.user_lookup = {
            user["full_name"]: user for user in self.users
        }

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_toolbar()
        self.build_request_info()
        self.build_attachments_section()

    def build_toolbar(self):
        self.toolbar = RequestToolbar(
        self,
        mode="create",
        mr_number=None,
        on_save=self.save_request,
        on_back=self.on_back,
        on_open_folder=self.open_folder_placeholder,
        )

        self.toolbar.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=20,
        pady=(20, 10),
        )

    def build_request_info(self):
        section = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        section.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        section.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            section,
            text="Request Information",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 10))

        self.request_no_entry = self.add_readonly_field(section, "MR No.", "Auto-generated", 1, 0)
        self.date_requested_entry = self.add_readonly_field(section, "Date Requested", str(date.today()), 1, 1)
        self.requested_by_entry = self.add_readonly_field(section, "Requested By", self.user["full_name"], 1, 2)
        self.status_entry = self.add_readonly_field(section, "Status", "New", 1, 3)

        project_names = list(self.project_lookup.keys()) or ["No active projects"]

        self.project_option = self.add_option(
            section,
            "Project / Site",
            project_names,
            3,
            0,
            command=self.on_project_selected,
        )

        self.client_entry = self.add_readonly_field(section, "Client", "", 3, 1)
        self.location_entry = self.add_readonly_field(section, "Location", "", 3, 2)

        user_names = list(self.user_lookup.keys()) or ["No active users"]

        self.assigned_to_option = self.add_option(
            section,
            "Assigned To",
            user_names,
            3,
            3,
        )

        self.material_description_entry = self.add_field(
            section,
            "Material Request Description",
            5,
            0,
        )

        self.priority_option = self.add_option(
            section,
            "Priority",
            ["High", "Medium", "Low"],
            5,
            1,
        )
        self.priority_option.set("Medium")

        self.due_date_entry = self.add_field(section, "Due Date (YYYY-MM-DD)", 5, 2)

        self.remarks_box = self.add_textbox(
            section,
            "Remarks",
            6,
            0,
            columnspan=4,
            height=60,
        )

        if self.projects:
            self.on_project_selected(project_names[0])

    def build_attachments_section(self):
        section = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        section.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(section, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="Material Request Attachments",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Upload File",
            width=140,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.upload_attachment,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header,
            text="Open Folder",
            width=120,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.open_folder_placeholder,
        ).pack(side="right", padx=5)

        self.attachments_frame = ctk.CTkScrollableFrame(
            section,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        self.attachments_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.refresh_attachment_list()

    def upload_attachment(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Material Request Files",
            filetypes=[
                ("Supported Files", "*.pdf *.png *.jpg *.jpeg *.xlsx *.xls *.docx *.doc"),
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.png *.jpg *.jpeg"),
                ("Excel Files", "*.xlsx *.xls"),
                ("Word Files", "*.docx *.doc"),
                ("All Files", "*.*"),
            ],
        )

        for path in file_paths:
            if path and path not in self.attachments:
                self.attachments.append(path)

        self.refresh_attachment_list()

    def refresh_attachment_list(self):
        for widget in self.attachments_frame.winfo_children():
            widget.destroy()

        if not self.attachments:
            ctk.CTkLabel(
                self.attachments_frame,
                text="No files attached yet. Click '+ Upload File' to attach PDFs, screenshots, BOQ files, or material lists.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).pack(pady=40)
            return

        for file_path in self.attachments:
            row = ctk.CTkFrame(self.attachments_frame, fg_color="#FFFFFF", corner_radius=10)
            row.pack(fill="x", padx=10, pady=6)

            file_name = os.path.basename(file_path)

            ctk.CTkLabel(
                row,
                text=file_name,
                font=("Segoe UI", 13),
                text_color="#111827",
                anchor="w",
            ).pack(side="left", padx=15, pady=12, fill="x", expand=True)

            ctk.CTkButton(
                row,
                text="Remove",
                width=90,
                fg_color="#E53935",
                hover_color="#B71C1C",
                command=lambda p=file_path: self.remove_attachment(p),
            ).pack(side="right", padx=10, pady=8)

    def remove_attachment(self, file_path):
        if file_path in self.attachments:
            self.attachments.remove(file_path)

        self.refresh_attachment_list()

    def open_folder_placeholder(self):
        print("Open folder will be available after saving the request.")

    def on_project_selected(self, project_name):
        project = self.project_lookup.get(project_name)

        if not project:
            return

        self.set_readonly_value(self.client_entry, project["client_name"])
        self.set_readonly_value(self.location_entry, project["location"])

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

    def add_textbox(self, parent, label, row, column, columnspan=1, height=70):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(row=0, column=0, sticky="w")

        textbox = ctk.CTkTextbox(wrapper, height=height)
        textbox.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        return textbox

    def add_readonly_field(self, parent, label, value, row, column, columnspan=1):
        entry = self.add_field(parent, label, row, column, columnspan)
        self.set_readonly_value(entry, value)
        return entry

    def set_readonly_value(self, entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="disabled")

    def add_option(self, parent, label, values, row, column, command=None):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=column, sticky="ew", padx=15, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#111827",
        ).grid(row=0, column=0, sticky="w")

        option = ctk.CTkOptionMenu(
            wrapper,
            values=values,
            height=36,
            command=command,
        )
        option.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        option.set(values[0])

        return option

    def validate_request(self):
        errors = []

        selected_project = self.project_option.get()
        selected_assignee = self.assigned_to_option.get()
        material_description = self.material_description_entry.get().strip()
        due_date = self.due_date_entry.get().strip()

        if selected_project == "No active projects":
            errors.append("Project / Site is required.")

        if not material_description:
            errors.append("Material Request Description is required.")

        if selected_assignee == "No active users":
            errors.append("Assigned To is required.")

        if not due_date:
            errors.append("Due Date is required.")

        if not self.attachments:
            errors.append("At least one attachment is required.")

        return errors

    def save_request(self):
        errors = self.validate_request()

        if errors:
            print("Validation errors:")
            for error in errors:
                print("-", error)
            return

        selected_project = self.project_option.get()
        selected_assignee = self.assigned_to_option.get()

        project = self.project_lookup.get(selected_project)
        assigned_user = self.user_lookup.get(selected_assignee)

        data = {
            "project_id": project["id"] if project else None,
            "project_name": selected_project,
            "client": self.client_entry.get(),
            "location": self.location_entry.get(),
            "requested_by": self.user["full_name"],
            "assigned_to": assigned_user["full_name"] if assigned_user else selected_assignee,
            "assigned_to_id": assigned_user["id"] if assigned_user else None,
            "material_request_description": self.material_description_entry.get().strip(),
            "priority": self.priority_option.get(),
            "status": "New",
            "due_date": self.due_date_entry.get().strip(),
            "remarks": self.remarks_box.get("1.0", "end").strip(),
            "attachments": self.attachments,
        }
        try:
            mr_number = create_material_request(data, self.user)

            print(f"Material Request saved successfully: {mr_number}")

            if self.on_back:
                self.on_back()

        except Exception as e:
            print("Failed to save Material Request:")
            print(e)