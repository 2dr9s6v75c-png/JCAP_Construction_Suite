"""
JCAP Construction Suite
Supplier Quotations Tab

Reusable Material Request Details section for displaying and selecting
Supplier Quotation records.

Dialog creation, file selection, and workflow execution remain owned by the
parent view. This component only renders records and forwards user actions
through callbacks.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

import customtkinter as ctk

from modules.quotation.components.supplier_quotation_file_panel import (
    SupplierQuotationFilePanel,
)


class SupplierQuotationsTab(ctk.CTkFrame):
    """Display Supplier Quotations associated with one Material Request."""

    STATUS_COLORS = {
        "Received": ("#E3F2FD", "#1565C0"),
        "Under Review": ("#FFF3E0", "#E65100"),
        "Clarification Required": ("#FFF8E1", "#F57F17"),
        "Accepted": ("#E8F5E9", "#2E7D32"),
        "Rejected": ("#FFEBEE", "#C62828"),
        "Archived": ("#ECEFF1", "#546E7A"),
    }

    def __init__(
        self,
        parent,
        quotations: list[dict[str, Any]] | None = None,
        *,
        can_add: bool = False,
        can_edit: bool = False,
        can_archive: bool = False,
        can_restore: bool = False,
        on_add: Callable[[], None] | None = None,
        on_open: Callable[[dict[str, Any]], None] | None = None,
        on_edit: Callable[[dict[str, Any]], None] | None = None,
        on_upload_files: Callable[[dict[str, Any]], None] | None = None,
        on_archive: Callable[[dict[str, Any]], None] | None = None,
        on_restore: Callable[[dict[str, Any]], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        current_user: dict[str, Any] | None = None,
        quotation_process=None,
        material_request_archived: bool = False,
        can_manage_files: bool | None = None,
    ) -> None:
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.quotations = list(quotations or [])
        self.filtered_quotations = list(self.quotations)

        self.search_var = ctk.StringVar()
        self.status_filter_var = ctk.StringVar(value="All")
        self.date_from_var = ctk.StringVar()
        self.date_to_var = ctk.StringVar()

        self.can_add = bool(can_add)
        self.can_edit = bool(can_edit)
        self.can_archive = bool(can_archive)
        self.can_restore = bool(can_restore)

        self.on_add = on_add
        self.on_open = on_open
        self.on_edit = on_edit
        self.on_upload_files = on_upload_files
        self.on_archive = on_archive
        self.on_restore = on_restore
        self.on_refresh = on_refresh

        self.current_user = current_user or {}
        self.quotation_process = quotation_process
        self.material_request_archived = bool(
            material_request_archived
        )
        self.can_manage_files = (
            self.can_edit
            if can_manage_files is None
            else bool(can_manage_files)
        )

        self.selected_quotation: dict[str, Any] | None = None
        self._row_frames: list[ctk.CTkFrame] = []

        self._selection_label = None
        self._open_button = None
        self._edit_button = None
        self._upload_button = None
        self._archive_button = None
        self._restore_button = None
        self._list_frame = None
        self._empty_state = None
        self._file_panel = None

        self._build_ui()
        self.set_quotations(self.quotations)

    # ========================================================
    # UI CONSTRUCTION
    # ========================================================

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_workspace()

    def _build_workspace(self) -> None:
        workspace = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        workspace.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(0, 14),
        )
        workspace.grid_columnconfigure(0, weight=42, uniform="quotation")
        workspace.grid_columnconfigure(1, weight=58, uniform="quotation")
        workspace.grid_rowconfigure(0, weight=1)

        list_side = ctk.CTkFrame(
            workspace,
            fg_color="transparent",
            corner_radius=0,
        )
        list_side.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(14, 5),
            pady=14,
        )
        list_side.grid_columnconfigure(0, weight=1)
        list_side.grid_rowconfigure(2, weight=1)

        self._build_filters(parent=list_side, row=0)
        self._build_column_header(parent=list_side, row=1)
        self._build_list(parent=list_side, row=2)
        self._build_action_bar(parent=list_side, row=3)

        divider = ctk.CTkFrame(
            workspace,
            width=1,
            fg_color="#E5E7EB",
            corner_radius=0,
        )
        divider.grid(
            row=0,
            column=0,
            sticky="nse",
            padx=(0, 0),
            pady=14,
        )

        self._file_panel = SupplierQuotationFilePanel(
            workspace,
            current_user=self.current_user,
            quotation_process=self.quotation_process,
            can_manage=self.can_manage_files,
            material_request_archived=(
                self.material_request_archived
            ),
            on_files_changed=self._handle_files_changed,
        )
        self._file_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 14),
            pady=14,
        )

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=14,
            pady=(8, 8),
        )
        toolbar.grid_columnconfigure(0, weight=1)

        title_group = ctk.CTkFrame(
            toolbar,
            fg_color="transparent",
        )
        title_group.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=10,
        )

        ctk.CTkLabel(
            title_group,
            text="Supplier Quotations",
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
            text_color="#111827",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_group,
            text=(
                "Quotation records and supporting files "
                "for this Material Request."
            ),
            font=ctk.CTkFont(size=12),
            text_color="#607D8B",
        ).pack(anchor="w", pady=(2, 0))

        button_group = ctk.CTkFrame(
            toolbar,
            fg_color="transparent",
        )
        button_group.grid(
            row=0,
            column=1,
            sticky="e",
            padx=18,
            pady=10,
        )

        ctk.CTkButton(
            button_group,
            text="Refresh",
            width=92,
            height=32,
            fg_color="#E3F2FD",
            hover_color="#BBDEFB",
            text_color="#0D47A1",
            command=self._handle_refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_group,
            text="+ Add Quotation",
            width=132,
            height=32,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            state=("normal" if self.can_add else "disabled"),
            command=self._handle_add,
        ).pack(side="left")

    def _build_filters(self, parent, row: int) -> None:
        filters = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )
        filters.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 5),
        )
        filters.grid_columnconfigure(0, weight=5)
        filters.grid_columnconfigure(1, weight=3)
        filters.grid_columnconfigure(2, weight=2)
        filters.grid_columnconfigure(3, weight=2)

        search_entry = ctk.CTkEntry(
            filters,
            textvariable=self.search_var,
            placeholder_text="Search supplier or reference...",
            height=32,
        )
        search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 5),
        )
        search_entry.bind(
            "<KeyRelease>",
            lambda _event: self.apply_filters(),
        )

        status_values = [
            "All",
            "Active",
            "Archived",
            *[
                status
                for status in self.STATUS_COLORS
                if status != "Archived"
            ],
        ]

        status_menu = ctk.CTkOptionMenu(
            filters,
            variable=self.status_filter_var,
            values=status_values,
            height=32,
            command=lambda _value: self.apply_filters(),
        )
        status_menu.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5,
        )

        date_from_entry = ctk.CTkEntry(
            filters,
            textvariable=self.date_from_var,
            placeholder_text="From date",
            height=34,
        )
        date_from_entry.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=5,
        )
        date_from_entry.bind(
            "<Return>",
            lambda _event: self.apply_filters(),
        )

        date_to_entry = ctk.CTkEntry(
            filters,
            textvariable=self.date_to_var,
            placeholder_text="To date",
            height=34,
        )
        date_to_entry.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(5, 0),
        )
        date_to_entry.bind(
            "<Return>",
            lambda _event: self.apply_filters(),
        )

    def _build_column_header(self, parent, row: int) -> None:
        header = ctk.CTkFrame(
            parent,
            fg_color="#EAF0F6",
            corner_radius=8,
        )
        header.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 6),
        )

        column_weights = (3, 2, 2, 2, 1)
        for index, weight in enumerate(column_weights):
            header.grid_columnconfigure(index, weight=weight)

        headings = (
            "Supplier",
            "Reference",
            "Quotation Date",
            "Status",
            "Files",
        )

        for index, heading in enumerate(headings):
            ctk.CTkLabel(
                header,
                text=heading,
                anchor=("center" if index == 4 else "w"),
                font=ctk.CTkFont(
                    size=12,
                    weight="bold",
                ),
                text_color="#455A64",
            ).grid(
                row=0,
                column=index,
                sticky="ew",
                padx=12,
                pady=9,
            )

    def _build_list(self, parent, row: int) -> None:
        container = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        container.grid(
            row=row,
            column=0,
            sticky="nsew",
            pady=(0, 8),
        )
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self._list_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent",
            corner_radius=0,
        )
        self._list_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=4,
            pady=4,
        )
        self._list_frame.grid_columnconfigure(0, weight=1)

        self._empty_state = ctk.CTkLabel(
            self._list_frame,
            text=(
                "No Supplier Quotations have been recorded "
                "for this Material Request."
            ),
            text_color="#78909C",
            font=ctk.CTkFont(size=13),
        )

    def _build_action_bar(self, parent, row: int) -> None:
        action_bar = ctk.CTkFrame(
            parent,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        action_bar.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 0),
        )
        action_bar.grid_columnconfigure(0, weight=1)

        self._selection_label = ctk.CTkLabel(
            action_bar,
            text="Select a quotation to enable actions.",
            wraplength=300,
            anchor="w",
            text_color="#607D8B",
            font=ctk.CTkFont(size=12),
        )
        self._selection_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(14, 8),
            pady=10,
        )

        buttons = ctk.CTkFrame(
            action_bar,
            fg_color="transparent",
        )
        buttons.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(8, 12),
            pady=8,
        )

        self._open_button = self._make_action_button(
            buttons,
            "Open",
            self._handle_open,
        )
        self._edit_button = self._make_action_button(
            buttons,
            "Edit",
            self._handle_edit,
        )
        self._upload_button = self._make_action_button(
            buttons,
            "Upload Files",
            self._handle_upload_files,
            width=108,
        )
        self._archive_button = self._make_action_button(
            buttons,
            "Archive",
            self._handle_archive,
        )
        self._restore_button = self._make_action_button(
            buttons,
            "Restore",
            self._handle_restore,
        )

        self._update_action_states()

    def _make_action_button(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        *,
        width: int = 82,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=32,
            fg_color="#1976D2",
            hover_color="#0D47A1",
            command=command,
        )
        button.pack(side="left", padx=4)
        return button

    # ========================================================
    # DATA RENDERING
    # ========================================================

    def set_quotations(
        self,
        quotations: list[dict[str, Any]] | None,
    ) -> None:
        self.quotations = list(quotations or [])
        self.selected_quotation = None

        if self._file_panel is not None:
            self._file_panel.set_quotation(
                None,
                refresh=False,
            )

        self.apply_filters()

    def _render_rows(self) -> None:
        for row in self._row_frames:
            row.destroy()
        self._row_frames.clear()

        if self._empty_state is not None:
            self._empty_state.grid_forget()

        if not self.filtered_quotations:
            self._empty_state.configure(
                text=(
                    "No Supplier Quotations match the "
                    "current search and filters."
                    if self.quotations
                    else (
                        "No Supplier Quotations have been recorded "
                        "for this Material Request."
                    )
                )
            )
            self._empty_state.grid(
                row=0,
                column=0,
                sticky="n",
                padx=20,
                pady=50,
            )
            return

        for index, quotation in enumerate(
            self.filtered_quotations
        ):
            row = self._create_row(
                quotation,
                index,
            )
            row.grid(
                row=index,
                column=0,
                sticky="ew",
                padx=2,
                pady=3,
            )
            self._row_frames.append(row)

    def _create_row(
        self,
        quotation: dict[str, Any],
        index: int,
    ) -> ctk.CTkFrame:
        background = (
            "#F8FAFC"
            if index % 2 == 0
            else "#FFFFFF"
        )

        row = ctk.CTkFrame(
            self._list_frame,
            fg_color=background,
            corner_radius=8,
            border_width=1,
            border_color="#E5E7EB",
            cursor="hand2",
        )

        column_weights = (3, 2, 2, 2, 1)
        for column, weight in enumerate(column_weights):
            row.grid_columnconfigure(column, weight=weight)

        supplier_name = str(
            quotation.get("supplier_name") or ""
        )
        reference = str(
            quotation.get("quotation_reference") or "—"
        )
        quotation_date = self._format_date(
            quotation.get("quotation_date")
        )
        file_count = int(
            quotation.get("file_count") or 0
        )
        is_archived = bool(
            quotation.get("is_archived")
        )
        status = (
            "Archived"
            if is_archived
            else str(quotation.get("status") or "")
        )

        supplier_label = ctk.CTkLabel(
            row,
            text=supplier_name,
            anchor="w",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
            text_color="#111827",
        )
        supplier_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=12,
            pady=11,
        )

        reference_label = ctk.CTkLabel(
            row,
            text=reference,
            anchor="w",
            text_color="#455A64",
            font=ctk.CTkFont(size=12),
        )
        reference_label.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=12,
            pady=11,
        )

        date_label = ctk.CTkLabel(
            row,
            text=quotation_date,
            anchor="w",
            text_color="#455A64",
            font=ctk.CTkFont(size=12),
        )
        date_label.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=12,
            pady=11,
        )

        status_background, status_text = (
            self.STATUS_COLORS.get(
                status,
                ("#ECEFF1", "#455A64"),
            )
        )

        status_badge = ctk.CTkLabel(
            row,
            text=status or "—",
            fg_color=status_background,
            text_color=status_text,
            corner_radius=10,
            height=24,
            font=ctk.CTkFont(
                size=11,
                weight="bold",
            ),
        )
        status_badge.grid(
            row=0,
            column=3,
            sticky="w",
            padx=12,
            pady=8,
        )

        files_label = ctk.CTkLabel(
            row,
            text=str(file_count),
            anchor="center",
            text_color="#455A64",
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        )
        files_label.grid(
            row=0,
            column=4,
            sticky="ew",
            padx=12,
            pady=11,
        )

        clickable_widgets = (
            row,
            supplier_label,
            reference_label,
            date_label,
            status_badge,
            files_label,
        )

        for widget in clickable_widgets:
            widget.bind(
                "<Button-1>",
                lambda _event, record=quotation: (
                    self.select_quotation(record)
                ),
            )
            widget.bind(
                "<Double-Button-1>",
                lambda _event, record=quotation: (
                    self._handle_double_click(record)
                ),
            )

        return row

    # ========================================================
    # SEARCH AND FILTERING
    # ========================================================

    def apply_filters(self) -> None:
        search_text = self.search_var.get().strip().lower()
        status_filter = self.status_filter_var.get().strip()
        date_from = self._parse_filter_date(
            self.date_from_var.get()
        )
        date_to = self._parse_filter_date(
            self.date_to_var.get()
        )

        filtered = []

        for quotation in self.quotations:
            is_archived = bool(
                quotation.get("is_archived")
            )
            status = (
                "Archived"
                if is_archived
                else str(quotation.get("status") or "")
            )

            if status_filter == "Active" and is_archived:
                continue

            if status_filter == "Archived" and not is_archived:
                continue

            if (
                status_filter
                not in {"All", "Active", "Archived"}
                and status != status_filter
            ):
                continue

            searchable_values = (
                quotation.get("supplier_name"),
                quotation.get("quotation_reference"),
                quotation.get("status"),
                quotation.get("remarks"),
            )
            searchable_text = " ".join(
                str(value or "").lower()
                for value in searchable_values
            )

            if search_text and search_text not in searchable_text:
                continue

            quotation_date = self._coerce_date(
                quotation.get("quotation_date")
            )

            if date_from:
                if not quotation_date or quotation_date < date_from:
                    continue

            if date_to:
                if not quotation_date or quotation_date > date_to:
                    continue

            filtered.append(quotation)

        self.filtered_quotations = filtered
        self.selected_quotation = None

        if self._file_panel is not None:
            self._file_panel.set_quotation(
                None,
                refresh=False,
            )

        self._render_rows()
        self._update_action_states()

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.status_filter_var.set("All")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.apply_filters()

    @staticmethod
    def _parse_filter_date(value: Any) -> date | None:
        text = str(value or "").strip()

        if not text:
            return None

        try:
            return datetime.strptime(
                text,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            return None

    @staticmethod
    def _coerce_date(value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value or "").strip()

        if not text:
            return None

        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            return None

    # ========================================================
    # SELECTION AND ACTIONS
    # ========================================================

    def select_quotation(
        self,
        quotation: dict[str, Any],
    ) -> None:
        self.selected_quotation = quotation
        self._highlight_selected_row()
        self._update_action_states()

        if self._file_panel is not None:
            self._file_panel.set_quotation(
                quotation,
                refresh=True,
            )

    def _highlight_selected_row(self) -> None:
        selected_id = (
            self.selected_quotation.get("id")
            if self.selected_quotation
            else None
        )

        for index, row in enumerate(self._row_frames):
            quotation = self.filtered_quotations[index]
            is_selected = quotation.get("id") == selected_id

            row.configure(
                border_color=(
                    "#1976D2"
                    if is_selected
                    else "#E5E7EB"
                ),
                border_width=(2 if is_selected else 1),
                fg_color=(
                    "#E3F2FD"
                    if is_selected
                    else (
                        "#F8FAFC"
                        if index % 2 == 0
                        else "#FFFFFF"
                    )
                ),
            )

    def _update_action_states(self) -> None:
        selected = self.selected_quotation
        has_selection = selected is not None
        is_archived = bool(
            selected and selected.get("is_archived")
        )

        self._set_button_state(
            self._open_button,
            has_selection and self.on_open is not None,
        )
        self._set_button_state(
            self._edit_button,
            (
                has_selection
                and not is_archived
                and self.can_edit
                and self.on_edit is not None
            ),
        )
        self._set_button_state(
            self._upload_button,
            (
                has_selection
                and not is_archived
                and self.can_edit
                and self.on_upload_files is not None
            ),
        )
        self._set_button_state(
            self._archive_button,
            (
                has_selection
                and not is_archived
                and self.can_archive
                and self.on_archive is not None
            ),
        )
        self._set_button_state(
            self._restore_button,
            (
                has_selection
                and is_archived
                and self.can_restore
                and self.on_restore is not None
            ),
        )

        if self._selection_label is None:
            return

        if selected is None:
            text = "Select a quotation to enable actions."
        else:
            supplier_name = str(
                selected.get("supplier_name") or ""
            )
            status = (
                "Archived"
                if is_archived
                else str(selected.get("status") or "")
            )
            text = f"Selected: {supplier_name} • {status}"

        self._selection_label.configure(text=text)

    @staticmethod
    def _set_button_state(
        button: ctk.CTkButton | None,
        enabled: bool,
    ) -> None:
        if button is not None:
            button.configure(
                state=("normal" if enabled else "disabled")
            )

    def _handle_add(self) -> None:
        if self.can_add and self.on_add:
            self.on_add()

    def _handle_refresh(self) -> None:
        if self.on_refresh:
            self.on_refresh()

    def _handle_open(self) -> None:
        if self.selected_quotation and self.on_open:
            self.on_open(self.selected_quotation)

    def _handle_edit(self) -> None:
        if (
            self.selected_quotation
            and self.can_edit
            and not self.selected_quotation.get("is_archived")
            and self.on_edit
        ):
            self.on_edit(self.selected_quotation)

    def _handle_upload_files(self) -> None:
        if (
            self.selected_quotation
            and self.can_edit
            and not self.selected_quotation.get("is_archived")
            and self.on_upload_files
        ):
            self.on_upload_files(self.selected_quotation)

    def _handle_archive(self) -> None:
        if (
            self.selected_quotation
            and self.can_archive
            and not self.selected_quotation.get("is_archived")
            and self.on_archive
        ):
            self.on_archive(self.selected_quotation)

    def _handle_restore(self) -> None:
        if (
            self.selected_quotation
            and self.can_restore
            and self.selected_quotation.get("is_archived")
            and self.on_restore
        ):
            self.on_restore(self.selected_quotation)

    def _handle_double_click(
        self,
        quotation: dict[str, Any],
    ) -> None:
        self.select_quotation(quotation)

        if self.on_open:
            self.on_open(quotation)

    def _handle_files_changed(
        self,
        quotation: dict[str, Any],
        files: list[dict[str, Any]],
    ) -> None:
        quotation_id = quotation.get("id")
        file_count = len(files or [])

        for record in self.quotations:
            if record.get("id") == quotation_id:
                record["file_count"] = file_count
                break

        for record in self.filtered_quotations:
            if record.get("id") == quotation_id:
                record["file_count"] = file_count
                break

        self._render_rows()
        self._highlight_selected_row()

    def set_permissions(
        self,
        *,
        can_manage: bool,
        material_request_archived: bool,
    ) -> None:
        enabled = bool(can_manage)
        self.can_add = enabled
        self.can_edit = enabled
        self.can_archive = enabled
        self.can_restore = enabled
        self.can_manage_files = enabled
        self.material_request_archived = bool(
            material_request_archived
        )

        self._update_action_states()

        if self._file_panel is not None:
            self._file_panel.can_manage = enabled
            self._file_panel.material_request_archived = bool(
                material_request_archived
            )

    def refresh_selected_files(self) -> None:
        if self._file_panel is not None:
            self._file_panel.refresh_files(
                notify_on_error=True,
            )

    # ========================================================
    # FORMATTING
    # ========================================================

    @staticmethod
    def _format_date(value: Any) -> str:
        if isinstance(value, datetime):
            value = value.date()

        if isinstance(value, date):
            return value.strftime("%d %b %Y")

        text = str(value or "").strip()
        return text or "—"