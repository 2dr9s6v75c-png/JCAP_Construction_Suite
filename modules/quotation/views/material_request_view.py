import os
from datetime import date
from tkinter import filedialog, messagebox

import customtkinter as ctk

from modules.master_data.projects.project_service import ProjectService
from modules.master_data.sites.site_service import SiteService
from modules.quotation.components.request_toolbar import RequestToolbar
from modules.quotation.services.material_request_service import (
    create_material_request,
)


class MaterialRequestView(ctk.CTkFrame):
    """Create a new unassigned Phase 1 Material Request."""

    PROJECT_PLACEHOLDER = "Select an active project"
    SITE_PLACEHOLDER = "Select an active site"
    NO_PROJECTS_MESSAGE = "No active projects available"
    NO_SITES_MESSAGE = "No active sites available"

    def __init__(self, parent, user, on_back=None):
        super().__init__(
            parent,
            fg_color="#F5F7FA",
            corner_radius=0,
        )

        self.user = user
        self.on_back = on_back
        self.attachments = []

        self.projects = []
        self.sites = []
        self.project_lookup = {}
        self.site_lookup = {}

        self._load_projects()
        self.build_ui()

    # ============================================================
    # DATA LOADING
    # ============================================================

    def _load_projects(self):
        self.projects = ProjectService.get_active(
            current_user=self.user,
        )

        self.project_lookup = {
            self._project_display(project): project
            for project in self.projects
            if project.get("id")
        }

    @staticmethod
    def _project_display(project):
        code = str(project.get("project_code") or "").strip()
        name = str(project.get("project_name") or "").strip()
        return f"{code} | {name}" if code else name

    @staticmethod
    def _site_display(site):
        code = str(site.get("site_code") or "").strip()
        name = str(site.get("site_name") or "").strip()
        return f"{code} | {name}" if code else name

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

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
        section = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        section.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )
        section.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            section,
            text="Request Information",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
        ).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            padx=20,
            pady=(15, 10),
        )

        self.request_no_entry = self.add_readonly_field(
            section, "MR No.", "Auto-generated", 1, 0
        )
        self.date_requested_entry = self.add_readonly_field(
            section, "Date Requested", str(date.today()), 1, 1
        )
        self.requested_by_entry = self.add_readonly_field(
            section,
            "Requested By",
            self.user["full_name"],
            1,
            2,
        )
        self.status_entry = self.add_readonly_field(
            section, "Workflow Status", "New", 1, 3
        )

        project_values = (
            list(self.project_lookup.keys())
            or [self.NO_PROJECTS_MESSAGE]
        )
        self.project_option = self.add_option(
            section,
            "Project",
            project_values,
            3,
            0,
            command=self.on_project_selected,
        )

        self.site_option = self.add_option(
            section,
            "Site",
            [self.SITE_PLACEHOLDER],
            3,
            1,
        )

        self.client_entry = self.add_readonly_field(
            section, "Client", "", 3, 2
        )
        self.assignment_entry = self.add_readonly_field(
            section, "Assignment", "Unassigned", 3, 3
        )

        self.material_description_entry = self.add_field(
            section,
            "Material Request Description",
            5,
            0,
            columnspan=2,
        )

        self.priority_option = self.add_option(
            section,
            "Priority",
            ["High", "Medium", "Low"],
            5,
            2,
        )
        self.priority_option.set("Medium")

        self.due_date_entry = self.add_field(
            section,
            "Due Date (YYYY-MM-DD)",
            5,
            3,
        )

        self.remarks_box = self.add_textbox(
            section,
            "Remarks",
            6,
            0,
            columnspan=4,
            height=60,
        )

        if self.projects:
            first_project = project_values[0]
            self.project_option.set(first_project)
            self.on_project_selected(first_project)

    def build_attachments_section(self):
        section = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        section.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(section, fg_color="transparent")
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(15, 10),
        )

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
        self.attachments_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 20),
        )

        self.refresh_attachment_list()

    # ============================================================
    # PROJECT / SITE SELECTION
    # ============================================================

    def on_project_selected(self, project_display):
        project = self.project_lookup.get(project_display)

        self.sites = []
        self.site_lookup = {}
        self.site_option.configure(values=[self.SITE_PLACEHOLDER])
        self.site_option.set(self.SITE_PLACEHOLDER)
        self.set_readonly_value(self.client_entry, "")

        if not project:
            return

        self.set_readonly_value(
            self.client_entry,
            project.get("client_name", ""),
        )

        try:
            self.sites = SiteService.get_by_project(
                project.get("id"),
                status_filter="Active",
                current_user=self.user,
            )
        except Exception as error:
            messagebox.showerror(
                "Unable to Load Sites",
                f"Sites for the selected project could not be loaded.\n\n{error}",
            )
            return

        self.site_lookup = {
            self._site_display(site): site
            for site in self.sites
            if site.get("id")
        }

        site_values = (
            list(self.site_lookup.keys())
            or [self.NO_SITES_MESSAGE]
        )
        self.site_option.configure(values=site_values)
        self.site_option.set(site_values[0])

    # ============================================================
    # ATTACHMENTS
    # ============================================================

    def upload_attachment(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Material Request Files",
            filetypes=[
                (
                    "Supported Files",
                    "*.pdf *.png *.jpg *.jpeg *.xlsx *.xls *.docx *.doc",
                ),
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
                text=(
                    "No files attached yet. Click '+ Upload File' "
                    "to attach Material Request files."
                ),
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).pack(pady=40)
            return

        for file_path in self.attachments:
            row = ctk.CTkFrame(
                self.attachments_frame,
                fg_color="#FFFFFF",
                corner_radius=10,
            )
            row.pack(fill="x", padx=10, pady=6)

            ctk.CTkLabel(
                row,
                text=os.path.basename(file_path),
                font=("Segoe UI", 13),
                text_color="#111827",
                anchor="w",
            ).pack(
                side="left",
                padx=15,
                pady=12,
                fill="x",
                expand=True,
            )

            ctk.CTkButton(
                row,
                text="Remove",
                width=90,
                fg_color="#E53935",
                hover_color="#B71C1C",
                command=lambda path=file_path: self.remove_attachment(path),
            ).pack(side="right", padx=10, pady=8)

    def remove_attachment(self, file_path):
        if file_path in self.attachments:
            self.attachments.remove(file_path)
        self.refresh_attachment_list()

    def open_folder_placeholder(self):
        messagebox.showinfo(
            "Folder Unavailable",
            "The Material Request folder becomes available after the request is saved.",
        )

    # ============================================================
    # FIELD HELPERS
    # ============================================================

    def add_field(self, parent, label, row, column, columnspan=1):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
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
        ).grid(row=0, column=0, sticky="w")

        entry = ctk.CTkEntry(wrapper, height=36)
        entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return entry

    def add_textbox(
        self,
        parent,
        label,
        row,
        column,
        columnspan=1,
        height=70,
    ):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
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
        ).grid(row=0, column=0, sticky="w")

        textbox = ctk.CTkTextbox(wrapper, height=height)
        textbox.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return textbox

    def add_readonly_field(
        self,
        parent,
        label,
        value,
        row,
        column,
        columnspan=1,
    ):
        entry = self.add_field(
            parent,
            label,
            row,
            column,
            columnspan,
        )
        self.set_readonly_value(entry, value)
        return entry

    @staticmethod
    def set_readonly_value(entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value or "")
        entry.configure(state="disabled")

    def add_option(
        self,
        parent,
        label,
        values,
        row,
        column,
        command=None,
    ):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
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

    # ============================================================
    # VALIDATION AND SAVE
    # ============================================================

    def validate_request(self):
        errors = []
        first_invalid = None

        project = self.project_lookup.get(self.project_option.get())
        site = self.site_lookup.get(self.site_option.get())
        description = self.material_description_entry.get().strip()
        due_date = self.due_date_entry.get().strip()

        if not project:
            errors.append("Project is required.")

        if not site:
            errors.append("An active Site belonging to the Project is required.")

        if not description:
            errors.append("Material Request Description is required.")
            first_invalid = self.material_description_entry

        if not self.priority_option.get():
            errors.append("Priority is required.")

        if not due_date:
            errors.append("Due Date is required.")
            first_invalid = first_invalid or self.due_date_entry
        else:
            try:
                date.fromisoformat(due_date)
            except ValueError:
                errors.append("Due Date must use YYYY-MM-DD format.")
                first_invalid = first_invalid or self.due_date_entry

        return errors, first_invalid

    def save_request(self):
        errors, first_invalid = self.validate_request()

        if errors:
            messagebox.showwarning(
                "Validation Required",
                "Please correct the following:\n\n"
                + "\n".join(f"• {error}" for error in errors),
            )
            if first_invalid:
                first_invalid.focus_set()
            return

        project = self.project_lookup[self.project_option.get()]
        site = self.site_lookup[self.site_option.get()]

        data = {
            "project_id": project["id"],
            "site_id": site["id"],
            "project_code": project.get("project_code", ""),
            "project_name": project.get("project_name", ""),
            "client": project.get("client_name", ""),
            "site_name": site.get("site_name", ""),
            "requested_by": self.user["full_name"],
            "assigned_to": None,
            "assigned_to_id": None,
            "material_request_description": (
                self.material_description_entry.get().strip()
            ),
            "priority": self.priority_option.get(),
            "status": "New",
            "workflow_status": "New",
            "due_date": self.due_date_entry.get().strip(),
            "remarks": self.remarks_box.get("1.0", "end").strip(),
            "attachments": list(self.attachments),
        }

        try:
            mr_number = create_material_request(data, self.user)
            messagebox.showinfo(
                "Material Request Created",
                (
                    f"Material Request {mr_number} was created successfully.\n\n"
                    "It is currently unassigned and ready for manager assignment."
                ),
            )
            if self.on_back:
                self.on_back()
        except Exception as error:
            messagebox.showerror(
                "Save Failed",
                f"Unable to save the Material Request.\n\n{error}",
            )