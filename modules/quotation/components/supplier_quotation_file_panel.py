"""
JCAP Construction Suite
Supplier Quotation File Panel

Purchasing-officer file management environment for one selected
Supplier Quotation.

The SupplierQuotationProcess owns transaction orchestration, storage,
rollback compensation, and metadata operations. This component owns only
presentation, selection, file dialogs, operating-system open actions, and
user notifications.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from modules.quotation.processes.supplier_quotation_process import (
    SupplierQuotationProcess,
)


class SupplierQuotationFilePanel(ctk.CTkFrame):
    """Manage files belonging to the selected Supplier Quotation."""

    SUPPORTED_FILE_TYPES = (
        (
            "Supported quotation files",
            (
                "*.pdf",
                "*.xlsx",
                "*.xls",
                "*.csv",
                "*.docx",
                "*.doc",
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.webp",
                "*.bmp",
                "*.dwg",
                "*.dxf",
                "*.zip",
            ),
        ),
        ("PDF files", "*.pdf"),
        ("Spreadsheet files", "*.xlsx *.xls *.csv"),
        ("Word documents", "*.docx *.doc"),
        ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
        ("Drawing files", "*.dwg *.dxf"),
        ("Archive files", "*.zip"),
        ("All files", "*.*"),
    )

    def __init__(
        self,
        parent,
        *,
        current_user: dict[str, Any],
        quotation_process: SupplierQuotationProcess | None = None,
        can_manage: bool = False,
        material_request_archived: bool = False,
        on_files_changed: Callable[
            [dict[str, Any], list[dict[str, Any]]],
            None,
        ]
        | None = None,
    ) -> None:
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.current_user = current_user
        self.quotation_process = (
            quotation_process or SupplierQuotationProcess()
        )
        self.can_manage = bool(can_manage)
        self.material_request_archived = bool(
            material_request_archived
        )
        self.on_files_changed = on_files_changed

        self.selected_quotation: dict[str, Any] | None = None
        self.files: list[dict[str, Any]] = []
        self.filtered_files: list[dict[str, Any]] = []
        self.file_by_row_id: dict[str, dict[str, Any]] = {}

        self.search_var = ctk.StringVar(value="")

        self.title_label = None
        self.context_label = None
        self.summary_label = None
        self.search_entry = None
        self.upload_button = None
        self.open_button = None
        self.open_folder_button = None
        self.delete_button = None
        self.refresh_button = None
        self.tree = None
        self.empty_label = None

        self._build_ui()
        self._render_rows()

    # ========================================================
    # PUBLIC API
    # ========================================================

    def set_quotation(
        self,
        quotation: dict[str, Any] | None,
        *,
        refresh: bool = True,
    ) -> None:
        """Set the quotation whose managed files are displayed."""
        self.selected_quotation = quotation
        self.files = []
        self.filtered_files = []
        self.search_var.set("")

        self._update_heading()

        if quotation and refresh:
            self.refresh_files(notify_on_error=True)
        else:
            self._render_rows()

    def refresh_files(
        self,
        notify_on_error: bool = True,
    ) -> bool:
        """Reload files for the currently selected quotation."""
        if not self.selected_quotation:
            self.files = []
            self.filtered_files = []
            self._render_rows()
            return True

        quotation_id = self.selected_quotation.get("id")

        if not quotation_id:
            self.files = []
            self.filtered_files = []
            self._render_rows()

            if notify_on_error:
                NotificationService.warning(
                    "The selected Supplier Quotation is unavailable.",
                    title="Supplier Quotation Files",
                )
            return False

        try:
            self.files = (
                self.quotation_process.list_files(quotation_id)
                or []
            )
            self._apply_filter()
            self._notify_files_changed()
            return True

        except Exception as error:
            self.files = []
            self.filtered_files = []
            self._render_rows()

            if notify_on_error:
                NotificationService.error(
                    "Unable to load Supplier Quotation files.",
                    title="Supplier Quotation Files",
                    error=error,
                )
            return False

    def set_manage_permission(
        self,
        can_manage: bool,
    ) -> None:
        self.can_manage = bool(can_manage)
        self._update_button_states()

    def set_material_request_archived(
        self,
        is_archived: bool,
    ) -> None:
        self.material_request_archived = bool(is_archived)
        self._update_button_states()

    # ========================================================
    # UI CONSTRUCTION
    # ========================================================

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_heading()
        self._build_toolbar()
        self._build_table()

    def _build_heading(self) -> None:
        heading = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        heading.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=0,
            pady=(0, 6),
        )
        heading.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            heading,
            text="Quotation Files",
            anchor="w",
            font=ctk.CTkFont(
                size=16,
                weight="bold",
            ),
            text_color="#111827",
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.context_label = ctk.CTkLabel(
            heading,
            text="Select a Supplier Quotation to view its files.",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
        )
        self.context_label.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(2, 0),
        )

        self.summary_label = ctk.CTkLabel(
            heading,
            text="0 files • 0 B",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#607D8B",
        )
        self.summary_label.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(2, 0),
        )

    def _build_toolbar(self) -> None:
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=0,
            pady=(0, 7),
        )
        toolbar.grid_columnconfigure(0, weight=3)
        toolbar.grid_columnconfigure(1, weight=2)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="Search quotation files...",
            height=32,
            font=ctk.CTkFont(size=12),
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(10, 6),
            pady=8,
        )
        self.search_var.trace_add(
            "write",
            self._on_search_changed,
        )

        button_row = ctk.CTkFrame(
            toolbar,
            fg_color="transparent",
        )
        button_row.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(0, 6),
            pady=6,
        )

        self.upload_button = self._make_button(
            button_row,
            text="Upload",
            command=self.upload_files,
            column=0,
            width=80,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
        )
        self.open_button = self._make_button(
            button_row,
            text="Open",
            command=self.open_selected,
            column=1,
            width=80,
            fg_color="#1565C0",
            hover_color="#0D47A1",
        )
        self.open_folder_button = self._make_button(
            button_row,
            text="Open Folder",
            command=self.open_selected_folder,
            column=2,
            width=110,
            fg_color="#607D8B",
            hover_color="#455A64",
        )
        self.delete_button = self._make_button(
            button_row,
            text="Delete",
            command=self.delete_selected,
            column=3,
            width=80,
            fg_color="#C62828",
            hover_color="#8E0000",
        )
        self.refresh_button = self._make_button(
            button_row,
            text="Refresh",
            command=self.refresh_files,
            column=4,
            width=80,
            fg_color="#455A64",
            hover_color="#263238",
            right_padding=4,
        )

    def _make_button(
        self,
        parent,
        *,
        text: str,
        command,
        column: int,
        width: int,
        fg_color: str,
        hover_color: str,
        right_padding: int = 4,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=34,
            fg_color=fg_color,
            hover_color=hover_color,
            command=command,
        )
        button.grid(
            row=0,
            column=column,
            padx=(4, right_padding),
            pady=12,
        )
        return button

    def _build_table(self) -> None:
        table_frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=0,
        )
        table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=0,
            pady=(0, 0),
        )
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "SupplierQuotationFile.Treeview",
            font=("Segoe UI", 11),
            rowheight=34,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#111827",
            borderwidth=0,
        )
        style.configure(
            "SupplierQuotationFile.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "SupplierQuotationFile.Treeview",
            background=[("selected", "#D9EAF7")],
            foreground=[("selected", "#111827")],
        )

        columns = (
            "filename",
            "type",
            "size",
            "uploaded_by",
            "uploaded_at",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="SupplierQuotationFile.Treeview",
            height=8,
        )

        self.tree.heading("filename", text="File Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("uploaded_by", text="Uploaded By")
        self.tree.heading("uploaded_at", text="Uploaded Date")

        self.tree.column(
            "filename",
            width=360,
            minwidth=220,
            anchor="w",
        )
        self.tree.column(
            "type",
            width=75,
            minwidth=60,
            anchor="center",
        )
        self.tree.column(
            "size",
            width=90,
            minwidth=70,
            anchor="e",
        )
        self.tree.column(
            "uploaded_by",
            width=170,
            minwidth=120,
            anchor="w",
        )
        self.tree.column(
            "uploaded_at",
            width=170,
            minwidth=145,
            anchor="w",
        )

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        vertical_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        horizontal_scrollbar.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        self.empty_label = ctk.CTkLabel(
            table_frame,
            text="Select a Supplier Quotation to view its files.",
            font=ctk.CTkFont(size=13),
            text_color="#78909C",
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._on_selection_changed,
        )
        self.tree.bind(
            "<Double-1>",
            self._on_double_click,
        )
        self.tree.bind(
            "<Return>",
            self._on_enter_key,
        )
        self.tree.bind(
            "<Delete>",
            self._on_delete_key,
        )

        self._update_button_states()

    # ========================================================
    # DATA RENDERING
    # ========================================================

    def _apply_filter(self) -> None:
        search_text = self.search_var.get().strip().lower()

        if not search_text:
            self.filtered_files = list(self.files)
        else:
            self.filtered_files = [
                file_record
                for file_record in self.files
                if search_text
                in self._searchable_file_text(file_record)
            ]

        self._render_rows()

    def _render_rows(self) -> None:
        selected_file_id = self._get_selected_file_id()

        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        self.file_by_row_id.clear()

        for index, file_record in enumerate(self.filtered_files):
            file_id = str(
                file_record.get("id") or f"quotation-file-{index}"
            )
            row_id = file_id

            while self.tree.exists(row_id):
                row_id = f"{file_id}-{index}"

            original_filename = str(
                file_record.get("original_filename")
                or file_record.get("stored_filename")
                or ""
            )

            values = (
                original_filename,
                self.format_extension(
                    file_record.get("file_extension")
                    or Path(original_filename).suffix
                ),
                self.format_file_size(
                    file_record.get("file_size")
                ),
                self._get_uploaded_by_name(file_record),
                self.format_datetime(
                    file_record.get("uploaded_at")
                ),
            )

            self.tree.insert(
                "",
                "end",
                iid=row_id,
                values=values,
            )
            self.file_by_row_id[row_id] = file_record

            if (
                selected_file_id
                and str(file_record.get("id")) == selected_file_id
            ):
                self.tree.selection_set(row_id)
                self.tree.focus(row_id)

        has_rows = bool(self.filtered_files)

        if has_rows:
            self.empty_label.grid_forget()
            self.tree.grid()
        else:
            self.tree.grid_remove()
            self.empty_label.configure(
                text=self._get_empty_state_text()
            )
            self.empty_label.grid(
                row=0,
                column=0,
                sticky="nsew",
                pady=45,
            )

        self._update_heading()
        self._update_button_states()

    # ========================================================
    # FILE ACTIONS
    # ========================================================

    def upload_files(self) -> None:
        if not self._can_modify_selected_quotation():
            NotificationService.warning(
                (
                    "Files cannot be uploaded to the selected "
                    "Supplier Quotation."
                ),
                title="Supplier Quotation Files",
            )
            return

        selected_files = filedialog.askopenfilenames(
            parent=self,
            title="Select Supplier Quotation Files",
            filetypes=self.SUPPORTED_FILE_TYPES,
        )

        if not selected_files:
            return

        try:
            uploaded_files = self.quotation_process.upload_files(
                supplier_quotation_id=(
                    self.selected_quotation["id"]
                ),
                files=selected_files,
                current_user=self.current_user,
            )

            self.refresh_files(notify_on_error=False)

            NotificationService.success(
                (
                    f"{len(uploaded_files or [])} file(s) "
                    "uploaded successfully."
                ),
                title="Supplier Quotation Files Uploaded",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to upload the selected quotation files.",
                title="Upload Failed",
                error=error,
            )

    def open_selected(self) -> None:
        file_record = self._get_selected_file()

        if not file_record:
            NotificationService.warning(
                "Select a quotation file to open.",
                title="Supplier Quotation Files",
            )
            return

        try:
            file_path = self._resolve_file_path(file_record)

            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Supplier Quotation file was not found: {file_path}"
                )

            self._open_path(file_path)

        except Exception as error:
            NotificationService.error(
                "Unable to open the selected quotation file.",
                title="Open File Failed",
                error=error,
            )

    def open_selected_folder(self) -> None:
        file_record = self._get_selected_file()

        if not file_record:
            NotificationService.warning(
                "Select a quotation file first.",
                title="Supplier Quotation Files",
            )
            return

        try:
            file_path = self._resolve_file_path(file_record)
            folder_path = file_path.parent

            if not folder_path.is_dir():
                raise FileNotFoundError(
                    "The Supplier Quotation folder was not found."
                )

            self._open_folder(
                folder_path,
                file_path if file_path.exists() else None,
            )

        except Exception as error:
            NotificationService.error(
                "Unable to open the Supplier Quotation folder.",
                title="Open Folder Failed",
                error=error,
            )

    def delete_selected(self) -> None:
        if not self._can_modify_selected_quotation():
            NotificationService.warning(
                (
                    "Files cannot be deleted from the selected "
                    "Supplier Quotation."
                ),
                title="Supplier Quotation Files",
            )
            return

        file_record = self._get_selected_file()

        if not file_record:
            NotificationService.warning(
                "Select a quotation file to delete.",
                title="Supplier Quotation Files",
            )
            return

        filename = str(
            file_record.get("original_filename")
            or file_record.get("stored_filename")
            or "the selected file"
        )

        confirmed = messagebox.askyesno(
            title="Delete Supplier Quotation File",
            message=(
                f"Delete {filename}?\n\n"
                "The physical file and its database record will "
                "be permanently removed."
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            self.quotation_process.delete_file(
                supplier_quotation_file_id=file_record["id"],
                current_user=self.current_user,
            )

            self.refresh_files(notify_on_error=False)

            NotificationService.success(
                f"{filename} was deleted successfully.",
                title="Supplier Quotation File Deleted",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to delete the selected quotation file.",
                title="Delete Failed",
                error=error,
            )

    # ========================================================
    # EVENTS
    # ========================================================

    def _on_search_changed(self, *_args) -> None:
        self._apply_filter()

    def _on_selection_changed(self, _event=None) -> None:
        self._update_button_states()

    def _on_double_click(self, _event=None) -> None:
        if self._get_selected_file():
            self.open_selected()

    def _on_enter_key(self, _event=None) -> None:
        if self.open_button.cget("state") == "normal":
            self.open_selected()

    def _on_delete_key(self, _event=None) -> None:
        if self.delete_button.cget("state") == "normal":
            self.delete_selected()

    # ========================================================
    # STATE
    # ========================================================

    def _can_modify_selected_quotation(self) -> bool:
        return bool(
            self.selected_quotation
            and self.selected_quotation.get("id")
            and not self.material_request_archived
            and not self.selected_quotation.get("is_archived")
            and self.can_manage
        )

    def _update_button_states(self) -> None:
        has_quotation = bool(
            self.selected_quotation
            and self.selected_quotation.get("id")
        )
        has_file = self._get_selected_file() is not None
        can_modify = self._can_modify_selected_quotation()

        self.search_entry.configure(
            state=("normal" if has_quotation else "disabled")
        )
        self.upload_button.configure(
            state=("normal" if can_modify else "disabled")
        )
        self.refresh_button.configure(
            state=("normal" if has_quotation else "disabled")
        )
        self.open_button.configure(
            state=("normal" if has_file else "disabled")
        )
        self.open_folder_button.configure(
            state=("normal" if has_file else "disabled")
        )
        self.delete_button.configure(
            state=(
                "normal"
                if has_file and can_modify
                else "disabled"
            )
        )

    def _update_heading(self) -> None:
        if not self.selected_quotation:
            if self.title_label is not None:
                self.title_label.configure(
                    text="Quotation Files"
                )

            if self.context_label is not None:
                self.context_label.configure(
                    text=(
                        "Select a Supplier Quotation "
                        "to view its files."
                    )
                )

            if self.summary_label is not None:
                self.summary_label.configure(
                    text="0 files • 0 B"
                )
            return

        quotation = self.selected_quotation

        supplier_name = str(
            quotation.get("supplier_name")
            or "Selected Supplier"
        )
        reference = str(
            quotation.get("quotation_reference")
            or "—"
        )
        status = (
            "Archived"
            if quotation.get("is_archived")
            else str(quotation.get("status") or "—")
        )

        file_count = len(self.files)
        total_size = sum(
            int(file_record.get("file_size") or 0)
            for file_record in self.files
        )

        if self.title_label is not None:
            self.title_label.configure(
                text=f"{supplier_name} — Quotation Files"
            )

        if self.context_label is not None:
            self.context_label.configure(
                text=(
                    f"Reference: {reference}    •    "
                    f"Status: {status}"
                )
            )

        if self.summary_label is not None:
            self.summary_label.configure(
                text=(
                    f"{file_count} "
                    f"file{'s' if file_count != 1 else ''} • "
                    f"{self.format_file_size(total_size)}"
                )
            )

    def _get_selected_file(self) -> dict[str, Any] | None:
        selection = self.tree.selection()

        if not selection:
            return None

        return self.file_by_row_id.get(selection[0])

    def _get_selected_file_id(self) -> str | None:
        file_record = self._get_selected_file()

        if not file_record:
            return None

        file_id = file_record.get("id")
        return str(file_id) if file_id else None

    def _notify_files_changed(self) -> None:
        if self.on_files_changed and self.selected_quotation:
            self.on_files_changed(
                self.selected_quotation,
                list(self.files),
            )

    # ========================================================
    # HELPERS
    # ========================================================

    def _get_empty_state_text(self) -> str:
        if not self.selected_quotation:
            return "Select a Supplier Quotation to view its files."

        if self.search_var.get().strip() and self.files:
            return "No quotation files match the current search."

        return "No files have been uploaded for this Supplier Quotation."

    @staticmethod
    def _searchable_file_text(
        file_record: dict[str, Any],
    ) -> str:
        values = (
            file_record.get("original_filename"),
            file_record.get("stored_filename"),
            file_record.get("file_extension"),
            file_record.get("uploaded_by_name"),
            file_record.get("uploaded_by_full_name"),
            file_record.get("uploader_name"),
        )
        return " ".join(
            str(value or "").lower()
            for value in values
        )

    @staticmethod
    def _get_uploaded_by_name(
        file_record: dict[str, Any],
    ) -> str:
        return str(
            file_record.get("uploaded_by_name")
            or file_record.get("uploaded_by_full_name")
            or file_record.get("uploader_name")
            or file_record.get("uploaded_by")
            or ""
        )

    @staticmethod
    def _resolve_file_path(
        file_record: dict[str, Any],
    ) -> Path:
        folder_path = str(
            file_record.get("folder_path") or ""
        ).strip()
        stored_filename = str(
            file_record.get("stored_filename") or ""
        ).strip()

        if not folder_path or not stored_filename:
            raise ValueError(
                "Supplier Quotation file storage metadata is incomplete."
            )

        return Path(folder_path) / stored_filename

    @staticmethod
    def format_extension(extension: Any) -> str:
        value = str(extension or "").strip().lstrip(".")
        return (value or "FILE").upper()

    @staticmethod
    def format_file_size(size: Any) -> str:
        try:
            size_value = int(size or 0)
        except (TypeError, ValueError):
            size_value = 0

        if size_value < 1024:
            return f"{size_value} B"
        if size_value < 1024 * 1024:
            return f"{size_value / 1024:.1f} KB"
        if size_value < 1024 * 1024 * 1024:
            return f"{size_value / (1024 * 1024):.1f} MB"

        return (
            f"{size_value / (1024 * 1024 * 1024):.1f} GB"
        )

    @staticmethod
    def format_datetime(value: Any) -> str:
        if not value:
            return ""

        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %I:%M %p")

        try:
            parsed = datetime.fromisoformat(str(value))
            return parsed.strftime("%d %b %Y %I:%M %p")
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _open_path(path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return

        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return

        subprocess.Popen(["xdg-open", str(path)])

    @staticmethod
    def _open_folder(
        folder_path: Path,
        file_path: Path | None = None,
    ) -> None:
        if sys.platform.startswith("win"):
            if file_path is not None and file_path.exists():
                subprocess.Popen(
                    ["explorer", "/select,", str(file_path)]
                )
            else:
                os.startfile(  # type: ignore[attr-defined]
                    str(folder_path)
                )
            return

        SupplierQuotationFilePanel._open_path(folder_path)