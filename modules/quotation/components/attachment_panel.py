from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from modules.quotation.processes.material_request_attachment_process import (
    MaterialRequestAttachmentProcess,
)


class AttachmentPanel(ctk.CTkFrame):
    """Phase 1 Material Request attachment management panel."""

    SUPPORTED_FILE_TYPES = (
        (
            "Supported files",
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
        material_request_id,
        current_user,
        is_archived=False,
        attachment_process=None,
        on_data_changed=None,
    ):
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=14,
        )

        self.material_request_id = material_request_id
        self.current_user = current_user
        self.is_archived = bool(is_archived)
        self.attachment_process = (
            attachment_process or MaterialRequestAttachmentProcess()
        )
        self.on_data_changed = on_data_changed

        self.attachments: list[dict[str, Any]] = []
        self.filtered_attachments: list[dict[str, Any]] = []
        self.attachment_by_row_id: dict[str, dict[str, Any]] = {}

        self.search_var = ctk.StringVar(value="")

        self.header_label = None
        self.search_entry = None
        self.upload_button = None
        self.open_button = None
        self.open_folder_button = None
        self.delete_button = None
        self.refresh_button = None
        self.tree = None
        self.empty_label = None

        self._build_ui()
        self.refresh_attachments(notify_on_error=False)

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_table()

    def _build_header(self):
        self.header_label = ctk.CTkLabel(
            self,
            text="Attachments (0 files • 0 KB)",
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
            anchor="w",
        )
        self.header_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(15, 8),
        )

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 10),
        )
        toolbar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="Search by filename or file type...",
            height=34,
            font=("Segoe UI", 12),
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(12, 8),
            pady=12,
        )
        self.search_var.trace_add("write", self._on_search_changed)

        self.upload_button = ctk.CTkButton(
            toolbar,
            text="Upload",
            width=85,
            height=34,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.upload_files,
        )
        self.upload_button.grid(
            row=0,
            column=1,
            padx=4,
            pady=12,
        )

        self.open_button = ctk.CTkButton(
            toolbar,
            text="Open",
            width=75,
            height=34,
            fg_color="#1565C0",
            hover_color="#0D47A1",
            command=self.open_selected,
        )
        self.open_button.grid(
            row=0,
            column=2,
            padx=4,
            pady=12,
        )

        self.open_folder_button = ctk.CTkButton(
            toolbar,
            text="Open Folder",
            width=105,
            height=34,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.open_selected_folder,
        )
        self.open_folder_button.grid(
            row=0,
            column=3,
            padx=4,
            pady=12,
        )

        self.delete_button = ctk.CTkButton(
            toolbar,
            text="Delete",
            width=75,
            height=34,
            fg_color="#C62828",
            hover_color="#8E0000",
            command=self.delete_selected,
        )
        self.delete_button.grid(
            row=0,
            column=4,
            padx=4,
            pady=12,
        )

        self.refresh_button = ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=80,
            height=34,
            fg_color="#455A64",
            hover_color="#263238",
            command=self.refresh_attachments,
        )
        self.refresh_button.grid(
            row=0,
            column=5,
            padx=(4, 12),
            pady=12,
        )

    def _build_table(self):
        table_frame = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=0,
        )
        table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=15,
            pady=(0, 15),
        )
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Attachment.Treeview",
            font=("Segoe UI", 11),
            rowheight=34,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#111827",
            borderwidth=0,
        )
        style.configure(
            "Attachment.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Attachment.Treeview",
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
            style="Attachment.Treeview",
        )

        self.tree.heading("filename", text="File Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("uploaded_by", text="Uploaded By")
        self.tree.heading("uploaded_at", text="Uploaded Date")

        self.tree.column("filename", width=360, minwidth=180, anchor="w")
        self.tree.column("type", width=90, minwidth=70, anchor="center")
        self.tree.column("size", width=100, minwidth=80, anchor="e")
        self.tree.column("uploaded_by", width=170, minwidth=120, anchor="w")
        self.tree.column("uploaded_at", width=180, minwidth=150, anchor="w")

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
            text="No attachments found.",
            font=("Segoe UI", 14),
            text_color="#607D8B",
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Delete>", self._on_delete_key)
        self.tree.bind("<Return>", self._on_enter_key)

        self._update_button_states()

    # ============================================================
    # DATA
    # ============================================================

    def refresh_attachments(self, notify_on_error=True):
        try:
            self.attachments = (
                self.attachment_process.list_by_material_request(
                    self.material_request_id
                )
                or []
            )
            self._apply_filter()
            self._notify_data_changed()
            return True

        except Exception as error:
            self.attachments = []
            self.filtered_attachments = []
            self._render_rows()

            if notify_on_error:
                NotificationService.error(
                    "Unable to load Material Request attachments.",
                    title="Attachments",
                    error=error,
                )

            return False

    def _apply_filter(self):
        search_text = self.search_var.get().strip().lower()

        if not search_text:
            self.filtered_attachments = list(self.attachments)
        else:
            self.filtered_attachments = [
                attachment
                for attachment in self.attachments
                if search_text
                in self._searchable_attachment_text(attachment)
            ]

        self._render_rows()

    def _render_rows(self):
        selected_id = self._get_selected_attachment_id()

        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        self.attachment_by_row_id.clear()

        for index, attachment in enumerate(self.filtered_attachments):
            attachment_id = str(
                attachment.get("id") or f"attachment-{index}"
            )
            row_id = attachment_id

            while self.tree.exists(row_id):
                row_id = f"{attachment_id}-{index}"

            original_filename = (
                attachment.get("original_filename")
                or attachment.get("stored_filename")
                or ""
            )

            values = (
                original_filename,
                self.format_extension(
                    attachment.get("file_extension")
                    or Path(original_filename).suffix
                ),
                self.format_file_size(
                    attachment.get("file_size")
                ),
                self._get_uploaded_by_name(attachment),
                self.format_datetime(
                    attachment.get("uploaded_at")
                ),
            )

            self.tree.insert(
                "",
                "end",
                iid=row_id,
                values=values,
            )
            self.attachment_by_row_id[row_id] = attachment

            if selected_id and str(attachment.get("id")) == selected_id:
                self.tree.selection_set(row_id)
                self.tree.focus(row_id)

        has_rows = bool(self.filtered_attachments)

        if has_rows:
            self.empty_label.grid_forget()
            self.tree.grid()
        else:
            self.tree.grid_remove()
            self.empty_label.grid(
                row=0,
                column=0,
                sticky="nsew",
                pady=50,
            )

        self._update_header()
        self._update_button_states()

    # ============================================================
    # ACTIONS
    # ============================================================

    def upload_files(self):
        if self.is_archived:
            NotificationService.warning(
                (
                    "Attachments cannot be uploaded while the "
                    "Material Request is archived."
                ),
                title="Attachments",
            )
            return

        selected_files = filedialog.askopenfilenames(
            parent=self,
            title="Select Material Request Attachments",
            filetypes=self.SUPPORTED_FILE_TYPES,
        )

        if not selected_files:
            return

        try:
            uploaded = self.attachment_process.upload_files(
                material_request_id=self.material_request_id,
                files=selected_files,
                current_user=self.current_user,
            )

            self.refresh_attachments(notify_on_error=False)

            NotificationService.success(
                f"{len(uploaded or [])} attachment(s) uploaded successfully.",
                title="Attachments Uploaded",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to upload the selected attachments.",
                title="Upload Failed",
                error=error,
            )

    def open_selected(self):
        attachment = self._get_selected_attachment()

        if not attachment:
            NotificationService.warning(
                "Select an attachment to open.",
                title="Attachments",
            )
            return

        try:
            self.attachment_process.open_attachment(
                attachment["id"]
            )
        except Exception as error:
            NotificationService.error(
                "Unable to open the selected attachment.",
                title="Open Attachment Failed",
                error=error,
            )

    def open_selected_folder(self):
        attachment = self._get_selected_attachment()

        if not attachment:
            NotificationService.warning(
                "Select an attachment first.",
                title="Attachments",
            )
            return

        try:
            self.attachment_process.open_attachment_folder(
                attachment["id"]
            )
        except Exception as error:
            NotificationService.error(
                "Unable to open the attachment folder.",
                title="Open Folder Failed",
                error=error,
            )

    def delete_selected(self):
        if self.is_archived:
            NotificationService.warning(
                (
                    "Attachments cannot be deleted while the "
                    "Material Request is archived."
                ),
                title="Attachments",
            )
            return

        attachment = self._get_selected_attachment()

        if not attachment:
            NotificationService.warning(
                "Select an attachment to delete.",
                title="Attachments",
            )
            return

        filename = (
            attachment.get("original_filename")
            or attachment.get("stored_filename")
            or "the selected attachment"
        )

        confirmed = messagebox.askyesno(
            title="Delete Attachment",
            message=(
                f"Delete {filename}?\n\n"
                "The file and its attachment record will be "
                "permanently removed."
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            self.attachment_process.delete_attachment(
                attachment_id=attachment["id"],
                current_user=self.current_user,
            )

            self.refresh_attachments(notify_on_error=False)

            NotificationService.success(
                f"{filename} was deleted successfully.",
                title="Attachment Deleted",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to delete the selected attachment.",
                title="Delete Failed",
                error=error,
            )

    # ============================================================
    # EVENTS
    # ============================================================

    def _on_search_changed(self, *_):
        self._apply_filter()

    def _on_selection_changed(self, _event=None):
        self._update_button_states()

    def _on_double_click(self, _event=None):
        if self._get_selected_attachment():
            self.open_selected()

    def _on_delete_key(self, _event=None):
        if self.delete_button.cget("state") == "normal":
            self.delete_selected()

    def _on_enter_key(self, _event=None):
        if self.open_button.cget("state") == "normal":
            self.open_selected()

    # ============================================================
    # STATE
    # ============================================================

    def _update_button_states(self):
        has_selection = self._get_selected_attachment() is not None

        self.open_button.configure(
            state="normal" if has_selection else "disabled"
        )
        self.open_folder_button.configure(
            state="normal" if has_selection else "disabled"
        )
        self.delete_button.configure(
            state=(
                "normal"
                if has_selection and not self.is_archived
                else "disabled"
            )
        )
        self.upload_button.configure(
            state="disabled" if self.is_archived else "normal"
        )

    def _update_header(self):
        count = len(self.attachments)
        total_size = sum(
            int(attachment.get("file_size") or 0)
            for attachment in self.attachments
        )

        self.header_label.configure(
            text=(
                f"Attachments "
                f"({count} file{'s' if count != 1 else ''} • "
                f"{self.format_file_size(total_size)})"
            )
        )

    def _get_selected_attachment(self):
        selection = self.tree.selection()

        if not selection:
            return None

        return self.attachment_by_row_id.get(selection[0])

    def _get_selected_attachment_id(self):
        attachment = self._get_selected_attachment()

        if not attachment:
            return None

        attachment_id = attachment.get("id")
        return str(attachment_id) if attachment_id else None

    def set_archived(self, is_archived):
        self.is_archived = bool(is_archived)
        self._update_button_states()

    def _notify_data_changed(self):
        if self.on_data_changed:
            self.on_data_changed(self.attachments)

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _searchable_attachment_text(attachment):
        values = (
            attachment.get("original_filename"),
            attachment.get("stored_filename"),
            attachment.get("file_extension"),
            attachment.get("uploaded_by_name"),
            attachment.get("uploaded_by_full_name"),
        )
        return " ".join(
            str(value or "").lower()
            for value in values
        )

    @staticmethod
    def _get_uploaded_by_name(attachment):
        return str(
            attachment.get("uploaded_by_name")
            or attachment.get("uploaded_by_full_name")
            or attachment.get("uploader_name")
            or attachment.get("uploaded_by")
            or ""
        )

    @staticmethod
    def format_extension(extension):
        value = str(extension or "").strip().lstrip(".")
        return (value or "FILE").upper()

    @staticmethod
    def format_file_size(size):
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

        return f"{size_value / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def format_datetime(value):
        if not value:
            return ""

        if isinstance(value, datetime):
            return value.strftime("%d %b %Y %I:%M %p")

        try:
            parsed = datetime.fromisoformat(str(value))
            return parsed.strftime("%d %b %Y %I:%M %p")
        except (TypeError, ValueError):
            return str(value)