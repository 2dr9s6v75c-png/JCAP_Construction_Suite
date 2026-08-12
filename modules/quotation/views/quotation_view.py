import customtkinter as ctk
from datetime import datetime, date

from core.security.permissions import PermissionService

from modules.quotation.services.material_request_service import (
    get_material_requests,
)


class QuotationView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        user,
        on_new_request=None,
        on_open_request=None,
    ):
        super().__init__(
            parent,
            fg_color="#F5F7FA",
            corner_radius=0,
        )

        self.user = user
        self.on_new_request = on_new_request
        self.on_open_request = on_open_request

        self.status_filter = "Active"
        self.requests = []
        self.all_requests = []
        self.filter_buttons = {}
        self._realtime_refresh_after_id = None
        self._pending_full_rebuild = False

        self.request_cards = {}
        self._empty_state_label = None

        self.build_ui()
        self.load_requests()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.build_header()
        self.build_toolbar()
        self.build_filter_bar()
        self.build_request_list()

    def build_header(self):
        ctk.CTkLabel(
            self,
            text="Quotation Monitoring",
            font=("Segoe UI", 28, "bold"),
            text_color="#0A2E63",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(20, 8),
        )

    def build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10),
        )

        toolbar.grid_columnconfigure(2, weight=1)

        # ========================================================
        # CREATE MATERIAL REQUEST
        # RBAC V1 CONTROLLED
        # ========================================================

        if PermissionService.can_create_material_request(
            self.user
        ):
            self.new_request_button = ctk.CTkButton(
                toolbar,
                text="+ New Material Request",
                width=190,
                height=38,
                fg_color="#0D47A1",
                hover_color="#0A2E63",
                font=("Segoe UI", 13, "bold"),
                command=self._handle_new_request,
            )
            self.new_request_button.grid(
                row=0,
                column=0,
                padx=15,
                pady=12,
            )
        else:
            self.new_request_button = None

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=100,
            height=38,
            fg_color="#607D8B",
            hover_color="#455A64",
            font=("Segoe UI", 13),
            command=self.load_requests,
        ).grid(
            row=0,
            column=1,
            padx=(15, 15),
            pady=12,
        )

        self.search_entry = ctk.CTkEntry(
            toolbar,
            height=38,
            placeholder_text=(
                "Search MR No., project, description, "
                "assigned to..."
            ),
            font=("Segoe UI", 13),
        )
        self.search_entry.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(0, 15),
            pady=12,
        )

        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.render_requests(),
        )

    def build_filter_bar(self):
        self.filter_frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        self.filter_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10),
        )

        filters = [
            "All",
            "Active",
            "New",
            "Assigned",
            "In Progress",
            "Completed",
            "Archived",
        ]

        for index, status in enumerate(filters):
            self.filter_frame.grid_columnconfigure(
                index,
                weight=1,
            )

            card = ctk.CTkButton(
                self.filter_frame,
                text=f"{status}\n0",
                height=58,
                fg_color="#F5F7FA",
                hover_color="#E3EAF2",
                text_color="#0A2E63",
                font=("Segoe UI", 13, "bold"),
                corner_radius=12,
                command=lambda s=status: (
                    self.set_status_filter(s)
                ),
            )
            card.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=8,
                pady=12,
            )

            self.filter_buttons[status] = card

    def build_request_list(self):
        container = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        container.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 20),
        )

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        self.list_title = ctk.CTkLabel(
            container,
            text="Material Requests",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
        )
        self.list_title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(15, 8),
        )

        self.list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        self.list_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 20),
        )

    # ============================================================
    # RBAC ACTION HANDLERS
    # ============================================================

    def _handle_new_request(self):
        """
        Defense-in-depth permission check.

        The button is hidden when the user does not have permission,
        but the action itself is also protected.
        """

        if not PermissionService.can_create_material_request(
            self.user
        ):
            print(
                "Permission denied: "
                "material_requests.create"
            )
            return

        if self.on_new_request:
            self.on_new_request()

    # ============================================================
    # FILTERS AND DATA LOADING
    # ============================================================

    def set_status_filter(self, status):
        self.status_filter = status
        self.load_requests()

    def load_requests(self):
        try:
            self.all_requests = get_material_requests(
                "All"
            )

            self.requests = get_material_requests(
                self.status_filter
            )

        except Exception as e:
            print(
                "Failed to load material requests:"
            )
            print(e)

            self.all_requests = []
            self.requests = []

        self.update_filter_counts()
        self.render_requests()

    def update_filter_counts(self):
        counts = {
            "All": len(self.all_requests),

            "Active": len([
                request
                for request in self.all_requests
                if request.get("status") != "Archived"
            ]),

            "New": len([
                request
                for request in self.all_requests
                if request.get("status") == "New"
            ]),

            "Assigned": len([
                request
                for request in self.all_requests
                if request.get("status") == "Assigned"
            ]),

            "In Progress": len([
                request
                for request in self.all_requests
                if request.get("status") == "In Progress"
            ]),

            "Completed": len([
                request
                for request in self.all_requests
                if request.get("status") == "Completed"
            ]),

            "Archived": len([
                request
                for request in self.all_requests
                if request.get("status") == "Archived"
            ]),
        }

        for status, button in self.filter_buttons.items():
            is_active = (
                status == self.status_filter
            )

            button.configure(
                text=(
                    f"{status}\n"
                    f"{counts.get(status, 0)}"
                ),
                fg_color=(
                    "#0D47A1"
                    if is_active
                    else "#F5F7FA"
                ),
                hover_color=(
                    "#0A2E63"
                    if is_active
                    else "#E3EAF2"
                ),
                text_color=(
                    "#FFFFFF"
                    if is_active
                    else "#0A2E63"
                ),
            )

        self.list_title.configure(
            text=(
                "Material Requests - "
                f"{self.status_filter}"
            )
        )

    # ============================================================
    # REQUEST LIST RENDERING
    # ============================================================

    def render_requests(self):
        """
        Render the current search/filter result.

        This method is used for manual search/filter changes and may rebuild
        the visible list. Normal real-time events use incremental syncing.
        """
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.request_cards = {}
        self._empty_state_label = None

        filtered = self._get_visible_requests()

        if not filtered:
            self._show_empty_state()
            return

        for request in filtered:
            self.create_request_card(
                request
            )

    def _get_visible_requests(self):
        keyword = ""

        if hasattr(self, "search_entry"):
            keyword = (
                self.search_entry
                .get()
                .strip()
                .lower()
            )

        filtered = []

        for request in self.requests:
            searchable_text = " ".join([
                str(request.get("mr_number", "")),
                str(request.get("project_code", "")),
                str(request.get("project_name", "")),
                str(request.get("description", "")),
                str(request.get("requested_by", "")),
                str(request.get("assigned_to_name", "")),
                str(request.get("priority", "")),
                str(request.get("status", "")),
            ]).lower()

            if keyword in searchable_text:
                filtered.append(request)

        return filtered

    def _show_empty_state(self):
        if self._empty_state_label is not None:
            return

        self._empty_state_label = ctk.CTkLabel(
            self.list_frame,
            text="No material requests found.",
            font=("Segoe UI", 14),
            text_color="#607D8B",
        )
        self._empty_state_label.pack(
            pady=40
        )

    def _hide_empty_state(self):
        if self._empty_state_label is None:
            return

        try:
            self._empty_state_label.destroy()
        except Exception:
            pass

        self._empty_state_label = None

    def create_request_card(
        self,
        request,
    ):
        request_id = str(
            request.get("id") or ""
        )

        if not request_id:
            return

        card = ctk.CTkFrame(
            self.list_frame,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        card.pack(
            fill="x",
            padx=10,
            pady=8,
        )

        card.grid_columnconfigure(
            0,
            weight=1,
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        top.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(14, 6),
        )

        top.grid_columnconfigure(
            1,
            weight=1,
        )

        mr_label = ctk.CTkLabel(
            top,
            font=("Segoe UI", 17, "bold"),
            text_color="#0D47A1",
        )
        mr_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        badges = ctk.CTkFrame(
            top,
            fg_color="transparent",
        )
        badges.grid(
            row=0,
            column=2,
            sticky="e",
        )

        priority_label = ctk.CTkLabel(
            badges,
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            corner_radius=14,
            width=95,
            height=28,
        )
        priority_label.pack(
            side="left",
            padx=6,
        )

        status_label = ctk.CTkLabel(
            badges,
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            corner_radius=14,
            width=95,
            height=28,
        )
        status_label.pack(
            side="left",
            padx=6,
        )

        content = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        content.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 8),
        )

        content.grid_columnconfigure(
            1,
            weight=1,
        )

        project_value = self._add_info_row_widgets(
            content,
            0,
            "Project:",
        )
        description_value = self._add_info_row_widgets(
            content,
            1,
            "Material Request:",
        )
        requested_by_value = self._add_info_row_widgets(
            content,
            2,
            "Requested By:",
        )
        assigned_to_value = self._add_info_row_widgets(
            content,
            3,
            "Assigned To:",
        )
        due_date_value = self._add_info_row_widgets(
            content,
            4,
            "Due Date:",
        )
        created_value = self._add_info_row_widgets(
            content,
            5,
            "Created:",
        )

        bottom = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 14),
        )

        bottom.grid_columnconfigure(
            0,
            weight=1,
        )

        attachment_label = ctk.CTkLabel(
            bottom,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
        )
        attachment_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkButton(
            bottom,
            text="Open",
            width=85,
            height=32,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=lambda rid=request_id: (
                self._open_request_id(rid)
            ),
        ).grid(
            row=0,
            column=1,
            padx=5,
        )

        ctk.CTkButton(
            bottom,
            text="Open Folder",
            width=110,
            height=32,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=lambda rid=request_id: (
                self._open_folder_by_id(rid)
            ),
        ).grid(
            row=0,
            column=2,
            padx=5,
        )

        self.request_cards[
            request_id
        ] = {
            "frame": card,
            "record": {},
            "mr_label": mr_label,
            "priority_label": priority_label,
            "status_label": status_label,
            "project_value": project_value,
            "description_value": description_value,
            "requested_by_value": requested_by_value,
            "assigned_to_value": assigned_to_value,
            "due_date_value": due_date_value,
            "created_value": created_value,
            "attachment_label": attachment_label,
        }

        self._update_request_card(
            request_id,
            request,
            force=True,
        )

    def _add_info_row_widgets(
        self,
        parent,
        row,
        label,
    ):
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
            width=120,
            anchor="w",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=2,
        )

        value_widget = ctk.CTkLabel(
            parent,
            text="",
            font=("Segoe UI", 13),
            text_color="#111827",
            anchor="w",
        )
        value_widget.grid(
            row=row,
            column=1,
            sticky="w",
            pady=2,
        )

        return value_widget

    def _update_request_card(
        self,
        request_id,
        request,
        *,
        force=False,
    ):
        card = self.request_cards.get(
            request_id
        )

        if not card:
            return

        if (
            not force
            and card.get("record") == request
        ):
            return

        card["mr_label"].configure(
            text=request.get("mr_number", "")
        )

        priority = request.get("priority", "")
        status = request.get("status", "")

        card["priority_label"].configure(
            text=priority,
            fg_color=self.get_priority_color(
                priority
            ),
        )

        card["status_label"].configure(
            text=status,
            fg_color=self.get_status_color(
                status
            ),
        )

        card["project_value"].configure(
            text=self.format_project(
                request
            )
        )
        card["description_value"].configure(
            text=str(
                request.get("description", "")
                or ""
            )
        )
        card["requested_by_value"].configure(
            text=str(
                request.get("requested_by", "")
                or ""
            )
        )
        card["assigned_to_value"].configure(
            text=(
                request.get("assigned_to_name")
                or "Unassigned"
            )
        )
        card["due_date_value"].configure(
            text=self.format_date(
                request.get("due_date")
            )
        )
        card["created_value"].configure(
            text=self.format_datetime(
                request.get("created_at")
            )
        )

        attachment_count = int(
            request.get(
                "attachment_count",
                0,
            )
            or 0
        )

        attachment_text = (
            f"📎 {attachment_count} Attachment"
            if attachment_count == 1
            else f"📎 {attachment_count} Attachments"
        )

        card["attachment_label"].configure(
            text=attachment_text
        )

        card["record"] = dict(
            request
        )

    def _sync_visible_request_cards(
        self,
    ):
        visible = self._get_visible_requests()

        new_ids = {
            str(request.get("id"))
            for request in visible
            if request.get("id")
        }

        existing_ids = set(
            self.request_cards.keys()
        )

        for request_id in (
            existing_ids - new_ids
        ):
            info = self.request_cards.pop(
                request_id,
                None,
            )

            if not info:
                continue

            try:
                info["frame"].destroy()
            except Exception:
                pass

        for request in visible:
            request_id = str(
                request.get("id") or ""
            )

            if not request_id:
                continue

            if request_id not in self.request_cards:
                self.create_request_card(
                    request
                )
            else:
                self._update_request_card(
                    request_id,
                    request,
                )

        # Reorder without rebuilding.
        for request in visible:
            request_id = str(
                request.get("id") or ""
            )
            info = self.request_cards.get(
                request_id
            )

            if not info:
                continue

            try:
                info["frame"].pack_forget()
                info["frame"].pack(
                    fill="x",
                    padx=10,
                    pady=8,
                )
            except Exception:
                pass

        if visible:
            self._hide_empty_state()
        else:
            self._show_empty_state()

    def _open_request_id(
        self,
        request_id,
    ):
        if self.on_open_request:
            self.on_open_request(
                request_id
            )

    def _open_folder_by_id(
        self,
        request_id,
    ):
        request = next(
            (
                item
                for item in self.all_requests
                if str(item.get("id")) == str(request_id)
            ),
            None,
        )

        if request is not None:
            self.open_folder_placeholder(
                request
            )

    # ============================================================
    # UI HELPERS
    # ============================================================

    def add_info_row(
        self,
        parent,
        row,
        label,
        value,
    ):
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
            width=120,
            anchor="w",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=2,
        )

        ctk.CTkLabel(
            parent,
            text=str(value or ""),
            font=("Segoe UI", 13),
            text_color="#111827",
            anchor="w",
        ).grid(
            row=row,
            column=1,
            sticky="w",
            pady=2,
        )

    def format_project(
        self,
        request,
    ):
        code = request.get(
            "project_code"
        ) or ""

        name = request.get(
            "project_name"
        ) or ""

        if code:
            return f"{code} - {name}"

        return name

    def format_date(
        self,
        value,
    ):
        if not value:
            return ""

        if isinstance(
            value,
            date,
        ):
            return value.strftime(
                "%d %b %Y"
            )

        return str(value)

    def format_datetime(
        self,
        value,
    ):
        if not value:
            return ""

        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(value)

    # ============================================================
    # REAL-TIME SYNCHRONIZATION
    # ============================================================

    def handle_realtime_event(self, event):
        if not isinstance(event, dict):
            return

        event_type = str(
            event.get("event_type") or ""
        ).strip()

        entity_type = str(
            event.get("entity_type") or ""
        ).strip().lower()

        if event_type == "reconciliation_refresh":
            self._schedule_realtime_refresh(
                full_rebuild=True
            )
            return

        is_material_request_event = (
            entity_type == "material_request"
            or event_type.startswith(
                "material_request_"
            )
        )

        if not is_material_request_event:
            return

        self._schedule_realtime_refresh(
            full_rebuild=False
        )

    def _schedule_realtime_refresh(
        self,
        *,
        full_rebuild=False,
    ):
        if self._realtime_refresh_after_id is not None:
            try:
                self.after_cancel(
                    self._realtime_refresh_after_id
                )
            except Exception:
                pass

        self._pending_full_rebuild = bool(
            full_rebuild
        )

        self._realtime_refresh_after_id = self.after(
            150,
            self._run_realtime_refresh,
        )

    def _run_realtime_refresh(self):
        self._realtime_refresh_after_id = None

        try:
            exists = self.winfo_exists()
        except Exception:
            exists = False

        if not exists:
            return

        if self._pending_full_rebuild:
            self._pending_full_rebuild = False
            self.load_requests()
            return

        self._refresh_requests_incrementally()

    def _refresh_requests_incrementally(self):
        try:
            new_all_requests = get_material_requests(
                "All"
            )

            new_requests = get_material_requests(
                self.status_filter
            )

        except Exception as error:
            print(
                "Failed to refresh material requests "
                "after real-time event:"
            )
            print(error)
            return

        if (
            new_all_requests == self.all_requests
            and new_requests == self.requests
        ):
            return

        self.all_requests = new_all_requests
        self.requests = new_requests

        self.update_filter_counts()
        self._sync_visible_request_cards()

    # ============================================================
    # ACTIONS
    # ============================================================

    def open_request_placeholder(
        self,
        request,
    ):
        if self.on_open_request:
            self.on_open_request(
                request["id"]
            )

    def open_folder_placeholder(
        self,
        request,
    ):
        print(
            "Open Folder from list view will be "
            "connected after Details View Open Folder."
        )

    # ============================================================
    # COLORS
    # ============================================================

    def get_priority_color(
        self,
        priority,
    ):
        colors = {
            "High": "#E53935",
            "Medium": "#FB8C00",
            "Low": "#43A047",
        }

        return colors.get(
            priority,
            "#607D8B",
        )

    def get_status_color(
        self,
        status,
    ):
        colors = {
            "New": "#1976D2",
            "Assigned": "#00ACC1",
            "In Progress": "#FB8C00",
            "Waiting Supplier Quote": "#8E24AA",
            "Completed": "#43A047",
            "Archived": "#607D8B",
        }

        return colors.get(
            status,
            "#607D8B",
        )