from __future__ import annotations

from datetime import date, datetime

import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from core.theme import JCAPTheme
from modules.dashboard.services.dashboard_service import DashboardService


class DashboardView(ctk.CTkFrame):
    """
    Phase 1 role-aware operational Dashboard.

    Normal real-time events update existing widgets incrementally.
    A full rebuild is reserved for manual refresh or reconnect reconciliation.
    """

    def __init__(self, parent, user, on_open_request=None):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BG_LIGHT,
            corner_radius=0,
        )

        self.user = user
        self.on_open_request = on_open_request

        self.dashboard_data = {}
        self._realtime_refresh_after_id = None
        self._pending_full_rebuild = False

        self.summary_value_labels = {}
        self.request_cards = {}
        self.list_frame = None
        self.list_title_label = None
        self.attention_description_label = None
        self._empty_state_label = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.load_data()
        self.build_ui()

    # ========================================================
    # DATA
    # ========================================================

    def load_data(self):
        self.dashboard_data = DashboardService.get_dashboard(
            self.user
        )

    def reload_view(self):
        self.load_data()

        for widget in self.winfo_children():
            widget.destroy()

        self.summary_value_labels = {}
        self.request_cards = {}
        self.list_frame = None
        self.list_title_label = None
        self.attention_description_label = None
        self._empty_state_label = None

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_summary_cards()
        self._build_attention_banner()
        self._build_request_list()

    def _build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=self.dashboard_data.get(
                "title",
                "Dashboard",
            ),
            font=("Segoe UI", 28, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            header,
            text=self.dashboard_data.get(
                "subtitle",
                "",
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_MUTED,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

        ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            height=34,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self._manual_refresh,
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

    def _build_summary_cards(self):
        frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=12,
            pady=(0, 6),
        )

        for column in range(3):
            frame.grid_columnconfigure(
                column,
                weight=1,
            )

        for index, item in enumerate(
            self.dashboard_data.get("cards", [])
        ):
            card = ctk.CTkFrame(
                frame,
                fg_color=JCAPTheme.CARD_BG,
                corner_radius=14,
            )
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=8,
                pady=7,
            )

            label_text = item.get("label", "")

            ctk.CTkLabel(
                card,
                text=label_text,
                font=("Segoe UI", 12, "bold"),
                text_color=JCAPTheme.TEXT_MUTED,
            ).pack(
                pady=(14, 3)
            )

            value_label = ctk.CTkLabel(
                card,
                text=str(item.get("value", 0)),
                font=("Segoe UI", 28, "bold"),
                text_color=JCAPTheme.PRIMARY_BLUE,
            )
            value_label.pack(
                pady=(0, 14)
            )

            self.summary_value_labels[
                label_text
            ] = value_label

    def _build_attention_banner(self):
        frame = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=12,
        )
        frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(5, 10),
        )
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Attention Required",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=16,
            pady=(10, 2),
        )

        self.attention_description_label = ctk.CTkLabel(
            frame,
            text=self._attention_text(
                self.dashboard_data
            ),
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_MUTED,
        )
        self.attention_description_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=16,
            pady=(0, 10),
        )

    def _build_request_list(self):
        records = self.dashboard_data.get(
            "records",
            [],
        )

        container = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD_BG,
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

        self.list_title_label = ctk.CTkLabel(
            container,
            text=f"Material Requests ({len(records)})",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        )
        self.list_title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(14, 8),
        )

        self.list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=JCAPTheme.BG_LIGHT,
            corner_radius=10,
        )
        self.list_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(0, 16),
        )

        self._sync_request_cards(records)

    # ========================================================
    # INCREMENTAL CARD MANAGEMENT
    # ========================================================

    def _sync_request_cards(self, records):
        if self.list_frame is None:
            return

        new_ids = {
            str(record.get("id"))
            for record in records
            if record.get("id")
        }

        for request_id in (
            set(self.request_cards) - new_ids
        ):
            info = self.request_cards.pop(
                request_id,
                None,
            )
            if info:
                try:
                    info["frame"].destroy()
                except Exception:
                    pass

        for record in records:
            request_id = str(
                record.get("id") or ""
            )
            if not request_id:
                continue

            if request_id not in self.request_cards:
                self._create_request_card(record)
            else:
                self._update_request_card(
                    request_id,
                    record,
                )

        # Reorder existing widgets to match service sorting without rebuilding.
        for record in records:
            request_id = str(
                record.get("id") or ""
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
                    padx=8,
                    pady=7,
                )
            except Exception:
                pass

        if self.list_title_label is not None:
            self.list_title_label.configure(
                text=f"Material Requests ({len(records)})"
            )

        self._update_empty_state(records)

    def _update_empty_state(self, records):
        if self.list_frame is None:
            return

        if records:
            if self._empty_state_label is not None:
                try:
                    self._empty_state_label.destroy()
                except Exception:
                    pass
                self._empty_state_label = None
            return

        if self._empty_state_label is None:
            self._empty_state_label = ctk.CTkLabel(
                self.list_frame,
                text="No Material Requests to display.",
                font=("Segoe UI", 14),
                text_color=JCAPTheme.TEXT_MUTED,
            )
            self._empty_state_label.pack(
                pady=45
            )

    def _create_request_card(self, record):
        request_id = str(
            record.get("id") or ""
        )
        if not request_id:
            return

        frame = ctk.CTkFrame(
            self.list_frame,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=12,
        )
        frame.pack(
            fill="x",
            padx=8,
            pady=7,
        )
        frame.grid_columnconfigure(1, weight=1)

        mr_label = ctk.CTkLabel(
            frame,
            font=("Segoe UI", 16, "bold"),
            text_color=JCAPTheme.PRIMARY_BLUE,
        )
        mr_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(16, 10),
            pady=(12, 4),
        )

        project_label = ctk.CTkLabel(
            frame,
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT_DARK,
        )
        project_label.grid(
            row=0,
            column=1,
            sticky="w",
            pady=(12, 4),
        )

        badges = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        badges.grid(
            row=0,
            column=2,
            sticky="e",
            padx=16,
            pady=(10, 4),
        )

        overdue_label = ctk.CTkLabel(
            badges,
            text="OVERDUE",
            width=80,
            height=26,
            fg_color="#C62828",
            text_color="white",
            corner_radius=12,
            font=("Segoe UI", 11, "bold"),
        )

        priority_label = ctk.CTkLabel(
            badges,
            width=82,
            height=26,
            text_color="white",
            corner_radius=12,
            font=("Segoe UI", 11, "bold"),
        )
        priority_label.pack(
            side="left",
            padx=4,
        )

        status_label = ctk.CTkLabel(
            badges,
            width=115,
            height=26,
            text_color="white",
            corner_radius=12,
            font=("Segoe UI", 11, "bold"),
        )
        status_label.pack(
            side="left",
            padx=4,
        )

        description_label = ctk.CTkLabel(
            frame,
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_DARK,
            anchor="w",
            justify="left",
            wraplength=800,
        )
        description_label.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=16,
            pady=(2, 6),
        )

        info_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent",
        )
        info_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            padx=16,
            pady=(0, 12),
        )

        owner_label = ctk.CTkLabel(
            info_frame,
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_MUTED,
        )
        owner_label.pack(
            side="left",
            padx=(0, 18),
        )

        due_label = ctk.CTkLabel(
            info_frame,
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_MUTED,
        )
        due_label.pack(
            side="left",
        )

        ctk.CTkButton(
            frame,
            text="Open",
            width=90,
            height=32,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            command=lambda rid=request_id: (
                self._open_request_id(rid)
            ),
        ).grid(
            row=2,
            column=2,
            sticky="e",
            padx=16,
            pady=(0, 12),
        )

        self.request_cards[request_id] = {
            "frame": frame,
            "record": {},
            "mr_label": mr_label,
            "project_label": project_label,
            "overdue_label": overdue_label,
            "priority_label": priority_label,
            "status_label": status_label,
            "description_label": description_label,
            "owner_label": owner_label,
            "due_label": due_label,
        }

        self._update_request_card(
            request_id,
            record,
            force=True,
        )

    def _update_request_card(
        self,
        request_id,
        record,
        force=False,
    ):
        card = self.request_cards.get(
            request_id
        )
        if not card:
            return

        if (
            not force
            and card.get("record") == record
        ):
            return

        card["mr_label"].configure(
            text=record.get("mr_number", "")
        )
        card["project_label"].configure(
            text=self._format_project(record)
        )
        card["description_label"].configure(
            text=record.get("description", "")
        )
        card["priority_label"].configure(
            text=record.get("priority", ""),
            fg_color=self._priority_color(
                record.get("priority")
            ),
        )
        card["status_label"].configure(
            text=record.get("status", ""),
            fg_color=self._status_color(
                record.get("status")
            ),
        )

        overdue_label = card["overdue_label"]

        if record.get("is_overdue"):
            if not overdue_label.winfo_manager():
                overdue_label.pack(
                    side="left",
                    padx=4,
                    before=card["priority_label"],
                )
        else:
            overdue_label.pack_forget()

        if (
            self.dashboard_data.get("perspective")
            == "engineering"
        ):
            owner_text = (
                "Assigned To: "
                f"{record.get('assigned_to_name') or 'Unassigned'}"
            )
        else:
            owner_text = (
                "Requested By: "
                f"{record.get('requested_by') or ''}"
            )

        card["owner_label"].configure(
            text=owner_text
        )
        card["due_label"].configure(
            text=(
                "Due: "
                f"{self._format_date(record.get('due_date'))}"
            )
        )

        card["record"] = dict(record)

    # ========================================================
    # INCREMENTAL DATA APPLICATION
    # ========================================================

    def _apply_incremental_data(self, new_data):
        old_data = self.dashboard_data
        self.dashboard_data = new_data

        old_values = {
            item.get("label"): item.get("value")
            for item in old_data.get("cards", [])
        }

        for item in new_data.get("cards", []):
            label = item.get("label", "")
            value = item.get("value", 0)

            if (
                old_values.get(label) != value
                and label in self.summary_value_labels
            ):
                self.summary_value_labels[
                    label
                ].configure(
                    text=str(value)
                )

        if self.attention_description_label is not None:
            new_text = self._attention_text(
                new_data
            )

            if (
                self.attention_description_label.cget(
                    "text"
                )
                != new_text
            ):
                self.attention_description_label.configure(
                    text=new_text
                )

        self._sync_request_cards(
            new_data.get("records", [])
        )

    # ========================================================
    # ACTIONS
    # ========================================================

    def _open_request_id(self, request_id):
        if request_id and self.on_open_request:
            self.on_open_request(
                request_id
            )

    def _manual_refresh(self):
        try:
            self.reload_view()
        except Exception as error:
            NotificationService.error(
                "Unable to refresh the Dashboard.",
                title="Dashboard",
                error=error,
            )

    # ========================================================
    # REAL-TIME
    # ========================================================

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

        if (
            entity_type != "material_request"
            and not event_type.startswith(
                "material_request_"
            )
        ):
            return

        self._schedule_realtime_refresh(
            full_rebuild=False
        )

    def _schedule_realtime_refresh(
        self,
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
            if not self.winfo_exists():
                return
        except Exception:
            return

        try:
            if self._pending_full_rebuild:
                self._pending_full_rebuild = False
                self.reload_view()
                return

            new_data = DashboardService.get_dashboard(
                self.user
            )

            self._apply_incremental_data(
                new_data
            )

        except Exception:
            # Keep current visible state. Manual refresh or
            # reconnect reconciliation can retry safely.
            pass

    # ========================================================
    # FORMAT / COLORS
    # ========================================================

    @staticmethod
    def _attention_text(dashboard_data):
        count = int(
            dashboard_data.get(
                "attention_count",
                0,
            )
            or 0
        )

        perspective = dashboard_data.get(
            "perspective"
        )

        if perspective == "engineering":
            return (
                f"{count} supplier clarification(s) "
                "currently require your Engineering response."
            )

        if perspective == "purchasing":
            return (
                f"{count} supplier clarification(s) "
                "currently have an Engineering response ready "
                "for Purchasing action."
            )

        return (
            f"{count} active Material Request(s) "
            "currently require assignment."
        )

    @staticmethod
    def _format_project(record):
        code = record.get("project_code") or ""
        name = record.get("project_name") or ""

        return (
            f"{code} - {name}"
            if code
            else name
        )

    @staticmethod
    def _format_date(value):
        if not value:
            return "No due date"

        if isinstance(value, datetime):
            value = value.date()

        if isinstance(value, date):
            return value.strftime(
                "%d %b %Y"
            )

        return str(value)

    @staticmethod
    def _priority_color(priority):
        return {
            "High": "#E53935",
            "Medium": "#FB8C00",
            "Low": "#43A047",
        }.get(
            str(priority or ""),
            "#607D8B",
        )

    @staticmethod
    def _status_color(status):
        return {
            "New": "#1976D2",
            "Assigned": "#00ACC1",
            "In Progress": "#FB8C00",
            "Waiting Supplier Quote": "#8E24AA",
            "Completed": "#43A047",
            "Restored": "#1976D2",
        }.get(
            str(status or ""),
            "#607D8B",
        )