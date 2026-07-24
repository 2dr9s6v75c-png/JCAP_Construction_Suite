from datetime import date, datetime
import os
from pathlib import Path
import subprocess
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.clarifications.clarification_service import (
    ClarificationService,
)
from core.documents.document_service import DocumentService
from core.lifecycle.document_lifecycle import DocumentLifecycle
from core.notifications.notification_service import NotificationService
from core.security.permissions import PermissionService

from modules.quotation.components.assignment_dialog import AssignmentDialog
from modules.quotation.components.collaboration_banner import (
    CollaborationBanner,
)
from modules.quotation.components.supplier_quotation_dialog import (
    SupplierQuotationDialog,
)
from modules.quotation.processes.supplier_quotation_process import (
    SupplierQuotationProcess,
)
from modules.quotation.sections.supplier_quotations_tab import (
    SupplierQuotationsTab,
)
from modules.quotation.processes.material_request_assignment_process import (
    MaterialRequestAssignmentProcess,
)
from modules.quotation.sections.activity_tab import ActivityTab
from modules.quotation.sections.attachments_tab import AttachmentsTab
from modules.quotation.sections.clarifications_tab import (
    ClarificationsTab,
)
from modules.quotation.sections.details_header import DetailsHeader
from modules.quotation.sections.information_tab import InformationTab
from modules.quotation.sections.summary_cards import SummaryCards
from modules.quotation.services.material_request_service import (
    archive_material_request,
    get_material_request,
    get_material_request_activity,
    restore_material_request,
)


class MaterialRequestDetailsView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        user,
        material_request_id,
        on_back=None,
        on_edit=None,
        on_record_clarification=None,
        on_open_clarification=None,
    ):
        super().__init__(
            parent,
            fg_color="#F5F7FA",
            corner_radius=0,
        )

        self.user = user
        self.material_request_id = material_request_id

        self.on_back = on_back
        self.on_edit = on_edit
        self.on_record_clarification = (
            on_record_clarification
        )
        self.on_open_clarification = (
            on_open_clarification
        )

        self.request = get_material_request(
            material_request_id
        )

        self.activities = get_material_request_activity(
            material_request_id
        )

        self.clarifications = (
            ClarificationService
            .get_material_request_clarifications(
                material_request_id
            )
        )

        self.assignment_process = (
            MaterialRequestAssignmentProcess()
        )

        self.supplier_quotation_process = (
            SupplierQuotationProcess()
        )

        self.supplier_quotations = []
        self.supplier_quotations_section = None

        self.header = None
        self.summary = None
        self.collaboration_banner = None
        self.tabview = None

        self.load_supplier_quotations(
            notify_on_error=False
        )

        self.build_ui()

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            3,
            weight=1,
        )

        self.build_header()
        self.build_summary()
        self.build_collaboration_banner()
        self.build_tabs()

    def build_header(self):
        title = (
            self.request.get(
                "mr_number",
                "",
            )
            if self.request
            else "Material Request"
        )

        self.header = DetailsHeader(
            self,
            title=title,
            subtitle="Material Request",
            on_open_folder=self.open_folder,
            on_assign=self.open_assignment_dialog,
            on_archive=self.archive_request,
            on_restore=self.restore_request,
            on_edit=self.edit_request,
            on_back=self.on_back,
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )

        is_archived = self.is_archived()

        self.header.set_record_state(
            (
                "archived"
                if is_archived
                else "active"
            )
        )

        is_assigned = bool(
            self.request
            and self.request.get("current_assignment_id")
        )

        self.header.set_assignment_state(
            assigned=is_assigned
        )

        self.header.set_assignment_enabled(
            enabled=(
                not is_archived
                and PermissionService
                .can_assign_material_request(
                    self.user
                )
            )
        )

        self.header.set_archive_enabled(
            (
                not is_archived
                and PermissionService
                .can_archive_material_request(
                    self.user
                )
            )
        )

        self.header.set_edit_enabled(
            (
                not is_archived
                and PermissionService
                .can_edit_material_request(
                    self.user
                )
            )
        )

    def build_summary(self):
        items = []

        if self.request:
            items = [
                {
                    "label": "Project",
                    "value": self.format_project(),
                },
                {
                    "label": "Status",
                    "value": self.request.get(
                        "status",
                        "",
                    ),
                },
                {
                    "label": "Priority",
                    "value": self.request.get(
                        "priority",
                        "",
                    ),
                },
                {
                    "label": "Attachments",
                    "value": len(
                        self.request.get(
                            "attachments",
                            [],
                        )
                    ),
                },
            ]

        self.summary = SummaryCards(
            self,
            items=items,
        )

        self.summary.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

    def build_collaboration_banner(self):
        self.collaboration_banner = CollaborationBanner(
            self,
            material_request_id=self.material_request_id,
            current_user=self.user,
            on_status_change=self.handle_lock_status_change,
        )

        self.collaboration_banner.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 10),
        )

    def build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )

        self.tabview.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        information_parent = self.tabview.add(
            "Information"
        )

        attachments_parent = self.tabview.add(
            "Attachments"
        )

        supplier_quotations_parent = self.tabview.add(
            "Supplier Quotations"
        )

        clarifications_parent = self.tabview.add(
            "Supplier Clarifications"
        )

        activity_parent = self.tabview.add(
            "Activity Timeline"
        )

        self.build_information_tab(
            information_parent
        )

        self.build_attachments_tab(
            attachments_parent
        )

        self.build_supplier_quotation_tab(
            supplier_quotations_parent
        )

        self.build_clarifications_tab(
            clarifications_parent
        )

        self.build_activity_tab(
            activity_parent
        )

    # ============================================================
    # TAB SECTIONS
    # ============================================================

    def build_information_tab(self, parent):
        fields = []

        if self.request:
            assigned_to_name = (
                self.request.get(
                    "assigned_to_name"
                )
                or self.request.get(
                    "assigned_to_full_name"
                )
                or "Unassigned"
            )

            fields = [
                {
                    "label": "MR Number",
                    "value": self.request.get(
                        "mr_number",
                        "",
                    ),
                },
                {
                    "label": "Project",
                    "value": self.format_project(),
                },
                {
                    "label": "Client",
                    "value": self.request.get(
                        "client_name",
                        "",
                    ),
                },
                {
                    "label": "Location",
                    "value": self.request.get(
                        "location",
                        "",
                    ),
                },
                {
                    "label": "Requested By",
                    "value": self.request.get(
                        "requested_by",
                        "",
                    ),
                },
                {
                    "label": "Assigned To",
                    "value": assigned_to_name,
                },
                {
                    "label": "Description",
                    "value": self.request.get(
                        "material_request_description",
                        "",
                    ),
                },
                {
                    "label": "Due Date",
                    "value": self.format_date(
                        self.request.get(
                            "due_date"
                        )
                    ),
                },
                {
                    "label": "Created",
                    "value": self.format_datetime(
                        self.request.get(
                            "created_at"
                        )
                    ),
                },
                {
                    "label": "Remarks",
                    "value": self.request.get(
                        "remarks",
                        "",
                    ),
                },
            ]

        section = InformationTab(
            parent,
            fields=fields,
        )

        section.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=0,
            pady=0,
        )

        parent.grid_columnconfigure(
            0,
            weight=1,
        )

        parent.grid_rowconfigure(
            0,
            weight=1,
        )

    def build_attachments_tab(self, parent):
        attachments = (
            self.request.get(
                "attachments",
                [],
            )
            if self.request
            else []
        )

        section = AttachmentsTab(
            parent,
            attachments=attachments,
            on_open=self.open_attachment,
            on_show_folder=self.show_attachment_folder,
        )

        section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        parent.grid_columnconfigure(
            0,
            weight=1,
        )

        parent.grid_rowconfigure(
            0,
            weight=1,
        )

    def build_supplier_quotation_tab(self, parent):
        self.supplier_quotations_section = (
            SupplierQuotationsTab(
                parent,
                quotations=self.supplier_quotations,
                can_add=(
                    not self.is_archived()
                    and PermissionService
                    .can_manage_supplier_quotations(
                        self.user
                    )
                ),
                can_edit=(
                    not self.is_archived()
                    and PermissionService
                    .can_manage_supplier_quotations(
                        self.user
                    )
                ),
                can_archive=(
                    not self.is_archived()
                    and PermissionService
                    .can_manage_supplier_quotations(
                        self.user
                    )
                ),
                can_restore=(
                    not self.is_archived()
                    and PermissionService
                    .can_manage_supplier_quotations(
                        self.user
                    )
                ),
                on_add=self.open_new_supplier_quotation_dialog,
                on_open=self.open_supplier_quotation_files,
                on_edit=self.open_edit_supplier_quotation_dialog,
                on_upload_files=(
                    self.upload_supplier_quotation_files
                ),
                on_archive=self.archive_supplier_quotation,
                on_restore=self.restore_supplier_quotation,
                on_refresh=self.refresh_supplier_quotations,
            )
        )

        self.supplier_quotations_section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        parent.grid_columnconfigure(
            0,
            weight=1,
        )

        parent.grid_rowconfigure(
            0,
            weight=1,
        )

    def build_clarifications_tab(self, parent):
        can_record = (
            not self.is_archived()
            and PermissionService.has_permission(
                self.user,
                (
                    "material_requests."
                    "clarifications.record_supplier"
                ),
            )
        )

        section = ClarificationsTab(
            parent,
            clarifications=self.clarifications,
            can_record=can_record,
            on_record=self.record_supplier_clarification,
            on_open=self.open_clarification,
        )

        section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        parent.grid_columnconfigure(
            0,
            weight=1,
        )

        parent.grid_rowconfigure(
            0,
            weight=1,
        )

    def build_activity_tab(self, parent):
        section = ActivityTab(
            parent,
            activities=self.activities,
        )

        section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        parent.grid_columnconfigure(
            0,
            weight=1,
        )

        parent.grid_rowconfigure(
            0,
            weight=1,
        )

    # ============================================================
    # SUPPLIER QUOTATION ACTIONS
    # ============================================================

    def open_new_supplier_quotation_dialog(self):
        if self.is_archived():
            NotificationService.error(
                (
                    "Supplier Quotations cannot be added "
                    "to an archived Material Request."
                ),
                title="Supplier Quotations",
            )
            return

        if not PermissionService.can_manage_supplier_quotations(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to create "
                    "Supplier Quotations."
                ),
                title="Permission Denied",
            )
            return

        SupplierQuotationDialog(
            self,
            mode=SupplierQuotationDialog.MODE_CREATE,
            on_save=self.create_supplier_quotation,
        )

    def create_supplier_quotation(self, form_data):
        result = self.supplier_quotation_process.create(
            material_request_id=self.material_request_id,
            supplier_name=form_data["supplier_name"],
            current_user=self.user,
            quotation_reference=form_data.get(
                "quotation_reference"
            ),
            quotation_date=form_data.get(
                "quotation_date"
            ),
            remarks=form_data.get("remarks"),
            status=form_data["status"],
        )

        self.refresh_supplier_quotations()

        created_quotation = (
            result.get("supplier_quotation", {})
            if isinstance(result, dict)
            else {}
        )

        supplier_name = (
            created_quotation.get("supplier_name")
            or form_data["supplier_name"]
        )

        NotificationService.success(
            (
                f"Supplier Quotation from {supplier_name} "
                "was created successfully."
            ),
            title="Supplier Quotation Created",
        )

        return result

    def open_edit_supplier_quotation_dialog(
        self,
        quotation,
    ):
        if self.is_archived():
            NotificationService.error(
                (
                    "Supplier Quotations cannot be edited "
                    "while the Material Request is archived."
                ),
                title="Supplier Quotations",
            )
            return

        if not PermissionService.can_manage_supplier_quotations(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to edit "
                    "Supplier Quotations."
                ),
                title="Permission Denied",
            )
            return

        if not quotation or not quotation.get("id"):
            NotificationService.error(
                "Select a valid Supplier Quotation.",
                title="Supplier Quotations",
            )
            return

        if quotation.get("is_archived"):
            NotificationService.error(
                (
                    "Archived Supplier Quotations must be "
                    "restored before they can be edited."
                ),
                title="Supplier Quotations",
            )
            return

        quotation_id = quotation["id"]

        latest_quotation = (
            self.supplier_quotation_process.get_by_id(
                quotation_id
            )
        )

        SupplierQuotationDialog(
            self,
            mode=SupplierQuotationDialog.MODE_EDIT,
            quotation=latest_quotation,
            on_save=lambda form_data: (
                self.update_supplier_quotation(
                    quotation_id,
                    form_data,
                )
            ),
        )

    def update_supplier_quotation(
        self,
        supplier_quotation_id,
        form_data,
    ):
        updated = self.supplier_quotation_process.update(
            supplier_quotation_id=(
                supplier_quotation_id
            ),
            supplier_name=form_data["supplier_name"],
            current_user=self.user,
            quotation_reference=form_data.get(
                "quotation_reference"
            ),
            quotation_date=form_data.get(
                "quotation_date"
            ),
            remarks=form_data.get("remarks"),
            status=form_data["status"],
        )

        self.refresh_supplier_quotations()

        supplier_name = (
            updated.get("supplier_name")
            if isinstance(updated, dict)
            else None
        ) or form_data["supplier_name"]

        NotificationService.success(
            (
                f"Supplier Quotation from {supplier_name} "
                "was updated successfully."
            ),
            title="Supplier Quotation Updated",
        )

        return updated

    def open_supplier_quotation_files(
        self,
        quotation,
    ):
        if not quotation or not quotation.get("id"):
            NotificationService.error(
                "Select a valid Supplier Quotation.",
                title="Supplier Quotations",
            )
            return

        try:
            files = (
                self.supplier_quotation_process
                .list_files(quotation["id"])
                or []
            )

            valid_paths = []

            for file_record in files:
                folder_path = str(
                    file_record.get("folder_path") or ""
                ).strip()

                stored_filename = str(
                    file_record.get("stored_filename") or ""
                ).strip()

                if not folder_path or not stored_filename:
                    continue

                full_path = (
                    Path(folder_path) / stored_filename
                )

                if full_path.is_file():
                    valid_paths.append(full_path)

            if not valid_paths:
                NotificationService.warning(
                    (
                        "No available files were found for "
                        "the selected Supplier Quotation."
                    ),
                    title="No Quotation Files",
                )
                return

            if len(valid_paths) == 1:
                os.startfile(str(valid_paths[0]))
                return

            first_file = valid_paths[0]

            subprocess.Popen(
                [
                    "explorer",
                    f"/select,{first_file}",
                ]
            )

            NotificationService.info(
                (
                    f"{len(valid_paths)} files are attached. "
                    "The quotation folder has been opened."
                ),
                title="Supplier Quotation Files",
            )

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to open the Supplier "
                    "Quotation files."
                ),
                title="Open Quotation Failed",
                error=error,
            )

    def upload_supplier_quotation_files(
        self,
        quotation,
    ):
        if self.is_archived():
            NotificationService.error(
                (
                    "Files cannot be uploaded while the "
                    "Material Request is archived."
                ),
                title="Supplier Quotations",
            )
            return

        if not PermissionService.can_manage_supplier_quotations(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to upload "
                    "Supplier Quotation files."
                ),
                title="Permission Denied",
            )
            return

        if not quotation or not quotation.get("id"):
            NotificationService.error(
                "Select a valid Supplier Quotation.",
                title="Supplier Quotations",
            )
            return

        if quotation.get("is_archived"):
            NotificationService.error(
                (
                    "Archived Supplier Quotations must be "
                    "restored before files can be uploaded."
                ),
                title="Supplier Quotations",
            )
            return

        selected_files = filedialog.askopenfilenames(
            parent=self,
            title="Select Supplier Quotation Files",
            filetypes=(
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
                    ),
                ),
                ("PDF files", "*.pdf"),
                (
                    "Spreadsheet files",
                    "*.xlsx *.xls *.csv",
                ),
                (
                    "Image files",
                    "*.png *.jpg *.jpeg *.webp",
                ),
                (
                    "Word documents",
                    "*.docx *.doc",
                ),
                ("All files", "*.*"),
            ),
        )

        if not selected_files:
            return

        try:
            uploaded_files = (
                self.supplier_quotation_process
                .upload_files(
                    supplier_quotation_id=quotation["id"],
                    files=selected_files,
                    current_user=self.user,
                )
            )

            self.refresh_supplier_quotations()

            file_count = len(uploaded_files or [])
            supplier_name = str(
                quotation.get("supplier_name") or "supplier"
            )

            NotificationService.success(
                (
                    f"{file_count} file(s) uploaded for "
                    f"{supplier_name}."
                ),
                title="Supplier Quotation Files Uploaded",
            )

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to upload the selected Supplier "
                    "Quotation files."
                ),
                title="Upload Failed",
                error=error,
            )

    def archive_supplier_quotation(
        self,
        quotation,
    ):
        if self.is_archived():
            NotificationService.error(
                (
                    "Supplier Quotations cannot be changed "
                    "while the Material Request is archived."
                ),
                title="Supplier Quotations",
            )
            return

        if not PermissionService.can_manage_supplier_quotations(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to archive "
                    "Supplier Quotations."
                ),
                title="Permission Denied",
            )
            return

        if not quotation or not quotation.get("id"):
            NotificationService.error(
                "Select a valid Supplier Quotation.",
                title="Supplier Quotations",
            )
            return

        if quotation.get("is_archived"):
            NotificationService.warning(
                (
                    "The selected Supplier Quotation is "
                    "already archived."
                ),
                title="Supplier Quotations",
            )
            return

        supplier_name = str(
            quotation.get("supplier_name")
            or "the selected supplier"
        )

        confirmed = messagebox.askyesno(
            title="Archive Supplier Quotation",
            message=(
                f"Archive the Supplier Quotation from "
                f"{supplier_name}?\n\n"
                "The record and attached files will be "
                "preserved and can be restored later."
            ),
            parent=self,
        )

        if not confirmed:
            return

        try:
            self.supplier_quotation_process.archive(
                supplier_quotation_id=quotation["id"],
                current_user=self.user,
            )

            self.refresh_supplier_quotations()

            NotificationService.success(
                (
                    f"Supplier Quotation from {supplier_name} "
                    "was archived successfully."
                ),
                title="Supplier Quotation Archived",
            )

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to archive the selected Supplier "
                    "Quotation."
                ),
                title="Archive Failed",
                error=error,
            )

    def restore_supplier_quotation(
        self,
        quotation,
    ):
        if self.is_archived():
            NotificationService.error(
                (
                    "Supplier Quotations cannot be changed "
                    "while the Material Request is archived."
                ),
                title="Supplier Quotations",
            )
            return

        if not PermissionService.can_manage_supplier_quotations(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to restore "
                    "Supplier Quotations."
                ),
                title="Permission Denied",
            )
            return

        if not quotation or not quotation.get("id"):
            NotificationService.error(
                "Select a valid Supplier Quotation.",
                title="Supplier Quotations",
            )
            return

        if not quotation.get("is_archived"):
            NotificationService.warning(
                (
                    "The selected Supplier Quotation is "
                    "already active."
                ),
                title="Supplier Quotations",
            )
            return

        supplier_name = str(
            quotation.get("supplier_name")
            or "the selected supplier"
        )

        try:
            self.supplier_quotation_process.restore(
                supplier_quotation_id=quotation["id"],
                current_user=self.user,
            )

            self.refresh_supplier_quotations()

            NotificationService.success(
                (
                    f"Supplier Quotation from {supplier_name} "
                    "was restored successfully."
                ),
                title="Supplier Quotation Restored",
            )

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to restore the selected Supplier "
                    "Quotation."
                ),
                title="Restore Failed",
                error=error,
            )

    # ============================================================
    # SUPPLIER QUOTATION DATA
    # ============================================================

    def load_supplier_quotations(
        self,
        notify_on_error=True,
    ):
        try:
            self.supplier_quotations = (
                self.supplier_quotation_process
                .list_by_material_request(
                    self.material_request_id,
                    status_filter="All",
                )
                or []
            )

            return True

        except Exception as error:
            self.supplier_quotations = []

            if notify_on_error:
                NotificationService.error(
                    (
                        "Unable to load Supplier "
                        "Quotations."
                    ),
                    title="Supplier Quotations",
                    error=error,
                )

            return False

    def refresh_supplier_quotations(self):
        loaded = self.load_supplier_quotations(
            notify_on_error=True
        )

        if (
            loaded
            and self.supplier_quotations_section
        ):
            self.supplier_quotations_section.set_quotations(
                self.supplier_quotations
            )

    # ============================================================
    # CLARIFICATION ACTIONS
    # ============================================================

    def record_supplier_clarification(self):
        if not self.request:
            return

        if self.is_archived():
            NotificationService.warning(
                (
                    "Supplier clarifications cannot be "
                    "recorded for an archived "
                    "Material Request."
                ),
                title="Clarification Unavailable",
            )
            return

        if not PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        ):
            NotificationService.error(
                (
                    "You do not have permission to record "
                    "supplier clarifications."
                ),
                title="Permission Denied",
            )
            return

        if self.on_record_clarification:
            self.on_record_clarification(
                self.material_request_id
            )

    def open_clarification(
        self,
        clarification,
    ):
        clarification_id = clarification.get(
            "id"
        )

        if not clarification_id:
            NotificationService.warning(
                (
                    "The selected clarification "
                    "is unavailable."
                ),
                title="Clarification Unavailable",
            )
            return

        if not PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.view"
            ),
        ):
            NotificationService.error(
                (
                    "You do not have permission to view "
                    "supplier clarifications."
                ),
                title="Permission Denied",
            )
            return

        if self.on_open_clarification:
            self.on_open_clarification(
                clarification_id
            )

    # ============================================================
    # ASSIGNMENT ACTIONS
    # ============================================================

    def open_assignment_dialog(self):
        if not self.request:
            return

        if self.is_archived():
            NotificationService.warning(
                (
                    "Archived Material Requests cannot be "
                    "assigned or reassigned."
                ),
                title="Assignment Unavailable",
            )
            return

        if not PermissionService.can_assign_material_request(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to assign "
                    "Material Requests."
                ),
                title="Permission Denied",
            )
            return

        is_assigned = bool(
            self.request.get("current_assignment_id")
        )

        AssignmentDialog(
            self,
            mode=(
                AssignmentDialog.MODE_REASSIGN
                if is_assigned
                else AssignmentDialog.MODE_ASSIGN
            ),
            current_assignee_id=(
                self.request.get("assigned_to_id")
                or self.request.get("assigned_to")
            ),
            on_submit=self.submit_assignment,
        )

    def submit_assignment(self, payload):
        if not self.request:
            raise ValueError(
                "Material Request is unavailable."
            )

        assigned_to = payload.get("assigned_to")
        assigned_to_name = payload.get(
            "assigned_to_name",
            "",
        )
        remarks = payload.get("remarks")

        current_assignment_id = (
            self.request.get(
                "current_assignment_id"
            )
            or self.request.get(
                "assignment_id"
            )
        )

        if current_assignment_id:
            self.assignment_process.reassign(
                assignment_id=current_assignment_id,
                assigned_to=assigned_to,
                current_user=self.user,
                remarks=(
                    "Reassigned through Material Request "
                    "Details View."
                ),
                replacement_remarks=remarks,
            )

            action_text = "reassigned"

        else:
            self.assignment_process.assign(
                material_request_id=(
                    self.request.get("id")
                    or self.material_request_id
                ),
                assigned_to=assigned_to,
                current_user=self.user,
                remarks=remarks,
            )

            action_text = "assigned"

        self.reload_view_data()

        NotificationService.success(
            (
                f"Material Request "
                f"{self.request.get('mr_number', '')} was "
                f"{action_text} to {assigned_to_name}."
            ),
            title="Assignment Complete",
        )

    def reload_view_data(self):
        self.request = get_material_request(
            self.material_request_id
        )

        self.activities = get_material_request_activity(
            self.material_request_id
        )

        self.clarifications = (
            ClarificationService
            .get_material_request_clarifications(
                self.material_request_id
            )
        )

        self.load_supplier_quotations(
            notify_on_error=True
        )

        for widget in self.winfo_children():
            widget.destroy()

        self.header = None
        self.summary = None
        self.collaboration_banner = None
        self.tabview = None
        self.supplier_quotations_section = None

        self.build_ui()

    # ============================================================
    # DOCUMENT ACTIONS
    # ============================================================

    def edit_request(self):
        if not self.request:
            return

        if self.is_archived():
            NotificationService.warning(
                (
                    "Archived Material Requests "
                    "cannot be edited.\n\n"
                    "Restore the record before editing it."
                ),
                title="Editing Disabled",
            )
            return

        if not PermissionService.can_edit_material_request(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to edit "
                    "Material Requests."
                ),
                title="Permission Denied",
            )
            return

        if self.on_edit:
            self.on_edit(
                self.material_request_id
            )

    def archive_request(self):
        if not self.request:
            return

        if not PermissionService.can_archive_material_request(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to archive "
                    "Material Requests."
                ),
                title="Permission Denied",
            )
            return

        if self.is_archived():
            NotificationService.info(
                (
                    "This Material Request is "
                    "already archived."
                ),
                title="Already Archived",
            )
            return

        confirmed = NotificationService.confirm(
            (
                "Archive this Material Request?\n\n"
                f"{self.request.get('mr_number', '')}\n\n"
                "The request will disappear from "
                "active records.\n"
                "It can be restored later by an "
                "authorized user."
            ),
            title="Archive Material Request",
        )

        if not confirmed:
            return

        try:
            mr_number = archive_material_request(
                self.material_request_id,
                self.user,
            )

            NotificationService.success(
                (
                    f"Material Request {mr_number} "
                    "was archived successfully."
                ),
                title="Archive Complete",
            )

            self.navigate_back()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to archive the "
                    "Material Request."
                ),
                title="Archive Failed",
                error=error,
            )

    def restore_request(self):
        if not self.request:
            return

        if not PermissionService.can_restore_material_request(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to restore "
                    "Material Requests."
                ),
                title="Permission Denied",
            )
            return

        if not self.is_archived():
            NotificationService.info(
                (
                    "Only archived Material Requests "
                    "can be restored."
                ),
                title="Restore Unavailable",
            )
            return

        confirmed = NotificationService.confirm(
            (
                "Restore this Material Request?\n\n"
                f"{self.request.get('mr_number', '')}\n\n"
                "The record will return to the active "
                "Material Request list."
            ),
            title="Restore Material Request",
        )

        if not confirmed:
            return

        try:
            mr_number = restore_material_request(
                self.material_request_id,
                self.user,
            )

            NotificationService.success(
                (
                    f"Material Request {mr_number} "
                    "was restored successfully."
                ),
                title="Restore Complete",
            )

            self.navigate_back()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to restore the "
                    "Material Request."
                ),
                title="Restore Failed",
                error=error,
            )

    # ============================================================
    # COLLABORATION AND LOCK STATE
    # ============================================================

    def handle_lock_status_change(
        self,
        status,
    ):
        if not self.header:
            return

        if self.is_archived():
            self.header.set_edit_enabled(
                False
            )
            return

        has_edit_permission = (
            PermissionService.can_edit_material_request(
                self.user
            )
        )

        record_available = (
            status != "locked_by_other"
        )

        self.header.set_edit_enabled(
            enabled=(
                has_edit_permission
                and record_available
            )
        )

    # ============================================================
    # FILE AND FOLDER ACTIONS
    # ============================================================

    def open_folder(self):
        try:
            DocumentService.open_material_request_folder(
                self.material_request_id
            )

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to open the Material "
                    "Request folder."
                ),
                title="Open Folder Failed",
                error=error,
            )

    def open_attachment(
        self,
        attachment,
    ):
        stored_filename = attachment.get(
            "stored_filename"
        )

        if not stored_filename:
            NotificationService.warning(
                (
                    "The selected attachment does not "
                    "have a valid stored filename."
                ),
                title="Attachment Unavailable",
            )
            return

        try:
            DocumentService.open_material_request_attachment(
                self.material_request_id,
                stored_filename,
            )

        except Exception as error:
            NotificationService.error(
                "Unable to open the attachment.",
                title="Open Attachment Failed",
                error=error,
            )

    def show_attachment_folder(
        self,
        attachment,
    ):
        self.open_folder()

    # ============================================================
    # NAVIGATION
    # ============================================================

    def navigate_back(self):
        if self.on_back:
            self.on_back()

    # ============================================================
    # STATUS AND FORMATTING HELPERS
    # ============================================================

    def is_archived(self):
        if not self.request:
            return False

        return DocumentLifecycle.is_archived(
            self.request.get(
                "status"
            )
        )

    def format_project(self):
        if not self.request:
            return ""

        code = (
            self.request.get(
                "project_code"
            )
            or ""
        )

        name = (
            self.request.get(
                "project_name"
            )
            or ""
        )

        return (
            f"{code} - {name}"
            if code
            else name
        )

    @staticmethod
    def format_date(value):
        if isinstance(
            value,
            date,
        ):
            return value.strftime(
                "%d %b %Y"
            )

        return str(
            value or ""
        )

    @staticmethod
    def format_datetime(value):
        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(
            value or ""
        )