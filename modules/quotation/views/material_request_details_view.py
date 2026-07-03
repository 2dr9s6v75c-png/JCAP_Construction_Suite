import customtkinter as ctk
from datetime import datetime, date

from modules.quotation.services.material_request_service import (
    get_material_request,
    get_material_request_activity,
)


class MaterialRequestDetailsView(ctk.CTkFrame):
    def __init__(self, parent, user, material_request_id, on_back=None):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)

        self.user = user
        self.material_request_id = material_request_id
        self.on_back = on_back

        self.request = get_material_request(material_request_id)
        self.activities = get_material_request_activity(material_request_id)

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_summary()
        self.build_tabs()

    def build_header(self):
        header = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        title = self.request["mr_number"] if self.request else "Material Request"

        ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 26, "bold"),
            text_color="#0A2E63",
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkButton(
            header,
            text="Back",
            width=100,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.on_back,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            header,
            text="Edit",
            width=100,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.edit_placeholder,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            header,
            text="Open Folder",
            width=130,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.open_folder_placeholder,
        ).pack(side="right", padx=10)

    def build_summary(self):
        summary = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        summary.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        summary.grid_columnconfigure((0, 1, 2, 3), weight=1)

        if not self.request:
            ctk.CTkLabel(
                summary,
                text="Material Request not found.",
                font=("Segoe UI", 16, "bold"),
                text_color="#E53935",
            ).grid(row=0, column=0, padx=20, pady=20)
            return

        items = [
            ("Project", self.format_project()),
            ("Status", self.request["status"]),
            ("Priority", self.request["priority"]),
            ("Attachments", str(len(self.request["attachments"]))),
        ]

        for index, (label, value) in enumerate(items):
            box = ctk.CTkFrame(summary, fg_color="#F5F7FA", corner_radius=10)
            box.grid(row=0, column=index, sticky="ew", padx=10, pady=15)

            ctk.CTkLabel(
                box,
                text=label,
                font=("Segoe UI", 12, "bold"),
                text_color="#607D8B",
            ).pack(pady=(12, 3))

            ctk.CTkLabel(
                box,
                text=value,
                font=("Segoe UI", 14, "bold"),
                text_color="#0A2E63",
                wraplength=220,
            ).pack(pady=(0, 12))

    def build_tabs(self):
        tabview = ctk.CTkTabview(self, fg_color="#FFFFFF", corner_radius=14)
        tabview.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        info_tab = tabview.add("Information")
        attachments_tab = tabview.add("Attachments")
        activity_tab = tabview.add("Activity Timeline")

        self.build_information_tab(info_tab)
        self.build_attachments_tab(attachments_tab)
        self.build_activity_tab(activity_tab)

    def build_information_tab(self, parent):
        parent.grid_columnconfigure((0, 1), weight=1)

        fields = [
            ("MR Number", self.request["mr_number"]),
            ("Project", self.format_project()),
            ("Client", self.request["client_name"]),
            ("Location", self.request["location"]),
            ("Requested By", self.request["requested_by"]),
            ("Assigned To", self.request["assigned_to"]),
            ("Description", self.request["material_request_description"]),
            ("Due Date", self.format_date(self.request["due_date"])),
            ("Created", self.format_datetime(self.request["created_at"])),
            ("Remarks", self.request["remarks"]),
        ]

        for index, (label, value) in enumerate(fields):
            row = index // 2
            col = index % 2
            self.add_info_field(parent, label, value, row, col)

    def build_attachments_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        if not self.request["attachments"]:
            ctk.CTkLabel(
                parent,
                text="No attachments found.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).pack(pady=40)
            return

        for attachment in self.request["attachments"]:
            row = ctk.CTkFrame(parent, fg_color="#F5F7FA", corner_radius=10)
            row.pack(fill="x", padx=15, pady=8)

            ctk.CTkLabel(
                row,
                text=attachment["stored_filename"],
                font=("Segoe UI", 13, "bold"),
                text_color="#111827",
            ).pack(side="left", padx=15, pady=12)

            ctk.CTkLabel(
                row,
                text=f"{attachment['file_extension']} | {attachment['file_size']} bytes",
                font=("Segoe UI", 12),
                text_color="#607D8B",
            ).pack(side="right", padx=15)

    def build_activity_tab(self, parent):
        if not self.activities:
            ctk.CTkLabel(
                parent,
                text="No activity recorded.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).pack(pady=40)
            return

        for activity in self.activities:
            row = ctk.CTkFrame(parent, fg_color="#F5F7FA", corner_radius=10)
            row.pack(fill="x", padx=15, pady=8)

            ctk.CTkLabel(
                row,
                text=activity["details"],
                font=("Segoe UI", 13, "bold"),
                text_color="#111827",
            ).pack(anchor="w", padx=15, pady=(10, 2))

            ctk.CTkLabel(
                row,
                text=f"{activity['user']} | {self.format_datetime(activity['created_at'])}",
                font=("Segoe UI", 12),
                text_color="#607D8B",
            ).pack(anchor="w", padx=15, pady=(0, 10))

    def add_info_field(self, parent, label, value, row, column):
        box = ctk.CTkFrame(parent, fg_color="#F5F7FA", corner_radius=10)
        box.grid(row=row, column=column, sticky="ew", padx=12, pady=8)

        ctk.CTkLabel(
            box,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
        ).pack(anchor="w", padx=15, pady=(10, 2))

        ctk.CTkLabel(
            box,
            text=str(value or ""),
            font=("Segoe UI", 13),
            text_color="#111827",
            wraplength=500,
        ).pack(anchor="w", padx=15, pady=(0, 10))

    def format_project(self):
        code = self.request.get("project_code") or ""
        name = self.request.get("project_name") or ""
        return f"{code} - {name}" if code else name

    def format_date(self, value):
        if isinstance(value, date):
            return value.strftime("%d %b %Y")
        return str(value or "")

    def format_datetime(self, value):
        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %I:%M %p")
        return str(value or "")

    def open_folder_placeholder(self):
        print(f"Open folder for {self.request['mr_number']}")

    def edit_placeholder(self):
        print(f"Edit {self.request['mr_number']}")