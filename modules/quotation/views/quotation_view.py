from aiohttp import request
import customtkinter as ctk
from datetime import datetime, date

from modules.quotation.services.material_request_service import get_material_requests


class QuotationView(ctk.CTkFrame):
    def __init__(self, parent, user, on_new_request=None, on_open_request=None):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)
        self.user = user
        self.on_new_request = on_new_request
        self.on_open_request = on_open_request
        self.requests = []
        self.build_ui()
        self.load_requests()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.build_header()
        self.build_toolbar()
        self.build_request_list()

    def build_header(self):
        ctk.CTkLabel(
            self,
            text="Quotation Monitoring",
            font=("Segoe UI", 28, "bold"),
            text_color="#0A2E63",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

    def build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        toolbar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            toolbar,
            text="+ New Material Request",
            width=190,
            height=38,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            font=("Segoe UI", 13, "bold"),
            command=self.on_new_request,
        ).grid(row=0, column=0, padx=15, pady=12)

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=100,
            height=38,
            fg_color="#607D8B",
            hover_color="#455A64",
            font=("Segoe UI", 13),
            command=self.load_requests,
        ).grid(row=0, column=1, padx=(0, 15), pady=12)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            height=38,
            placeholder_text="Search MR No., project, description, assigned to...",
            font=("Segoe UI", 13),
        )
        self.search_entry.grid(row=0, column=2, sticky="ew", padx=(0, 15), pady=12)
        self.search_entry.bind("<KeyRelease>", lambda event: self.render_requests())

    def build_request_list(self):
        container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=14)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            container,
            text="Material Requests",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 8))

        self.list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def load_requests(self):
        try:
            self.requests = get_material_requests()
        except Exception as e:
            print("Failed to load material requests:")
            print(e)
            self.requests = []

        self.render_requests()

    def render_requests(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        keyword = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""

        filtered = []
        for request in self.requests:
            searchable_text = " ".join([
                str(request.get("mr_number", "")),
                str(request.get("project_code", "")),
                str(request.get("project_name", "")),
                str(request.get("description", "")),
                str(request.get("requested_by", "")),
                str(request.get("assigned_to", "")),
                str(request.get("priority", "")),
                str(request.get("status", "")),
            ]).lower()

            if keyword in searchable_text:
                filtered.append(request)

        if not filtered:
            ctk.CTkLabel(
                self.list_frame,
                text="No material requests found.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).pack(pady=40)
            return

        for request in filtered:
            self.create_request_card(request)

    def create_request_card(self, request):
        card = ctk.CTkFrame(self.list_frame, fg_color="#FFFFFF", corner_radius=14)
        card.pack(fill="x", padx=10, pady=8)
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top,
            text=request["mr_number"],
            font=("Segoe UI", 17, "bold"),
            text_color="#0D47A1",
        ).grid(row=0, column=0, sticky="w")

        badges = ctk.CTkFrame(top, fg_color="transparent")
        badges.grid(row=0, column=2, sticky="e")

        ctk.CTkLabel(
            badges,
            text=request["priority"],
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            fg_color=self.get_priority_color(request["priority"]),
            corner_radius=14,
            width=95,
            height=28,
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            badges,
            text=request["status"],
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            fg_color=self.get_status_color(request["status"]),
            corner_radius=14,
            width=95,
            height=28,
        ).pack(side="left", padx=6)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))
        content.grid_columnconfigure(1, weight=1)

        self.add_info_row(content, 0, "Project:", self.format_project(request))
        self.add_info_row(content, 1, "Material Request:", request["description"])
        self.add_info_row(content, 2, "Requested By:", request["requested_by"])
        self.add_info_row(content, 3, "Assigned To:", request["assigned_to"])
        self.add_info_row(content, 4, "Due Date:", self.format_date(request.get("due_date")))
        self.add_info_row(content, 5, "Created:", self.format_datetime(request.get("created_at")))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        bottom.grid_columnconfigure(0, weight=1)

        attachment_count = request.get("attachment_count", 0)
        attachment_text = f"📎 {attachment_count} Attachment" if attachment_count == 1 else f"📎 {attachment_count} Attachments"

        ctk.CTkLabel(
            bottom,
            text=attachment_text,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            bottom,
            text="Open",
            width=85,
            height=32,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=lambda r=request: self.open_request_placeholder(r),
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            bottom,
            text="Open Folder",
            width=110,
            height=32,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=lambda r=request: self.open_folder_placeholder(r),
        ).grid(row=0, column=2, padx=5)

    def add_info_row(self, parent, row, label, value):
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
            width=120,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=2)

        ctk.CTkLabel(
            parent,
            text=str(value or ""),
            font=("Segoe UI", 13),
            text_color="#111827",
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=2)

    def format_project(self, request):
        code = request.get("project_code") or ""
        name = request.get("project_name") or ""
        return f"{code} - {name}" if code else name

    def format_date(self, value):
        if not value:
            return ""

        if isinstance(value, date):
            return value.strftime("%d %b %Y")

        return str(value)

    def format_datetime(self, value):
        if not value:
            return ""

        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %I:%M %p")

        return str(value)

    def open_request_placeholder(self, request):
        print("========== OPEN CLICKED ==========")
        print(request)
        print("Callback:", self.on_open_request)

        if self.on_open_request:
            print("Calling callback...")
            self.on_open_request(request["id"])
        else:
            print("Callback is None")

    def open_folder_placeholder(self, request):
        print(f"Open folder for: {request['mr_number']}")

    def get_priority_color(self, priority):
        colors = {
            "High": "#E53935",
            "Medium": "#FB8C00",
            "Low": "#43A047",
        }
        return colors.get(priority, "#607D8B")

    def get_status_color(self, status):
        colors = {
            "New": "#1976D2",
            "Assigned": "#00ACC1",
            "In Progress": "#FB8C00",
            "Waiting Supplier Quote": "#8E24AA",
            "Completed": "#43A047",
            "Archived": "#607D8B",
        }
        return colors.get(status, "#607D8B")