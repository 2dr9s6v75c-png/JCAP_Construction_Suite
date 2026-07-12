import customtkinter as ctk

from core.clarifications.clarification_service import (
    ClarificationService,
)
from core.notifications.notification_service import (
    NotificationService,
)
from core.organization.organization_service import (
    OrganizationService,
)
from core.security.permissions import PermissionService
from core.theme import JCAPTheme

from modules.quotation.services.material_request_service import (
    get_material_request,
)


class RecordSupplierClarificationView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        user,
        material_request_id,
        on_cancel=None,
        on_saved=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.material_request_id = material_request_id
        self.on_cancel = on_cancel
        self.on_saved = on_saved

        self.request = get_material_request(
            material_request_id
        )

        self.engineers = []
        self.engineer_lookup = {}

        self.load_project_engineers()
        self.build_ui()

    # ============================================================
    # DATA
    # ============================================================

    def load_project_engineers(self):
        users = OrganizationService.get_active_users()

        self.engineers = [
            user
            for user in users
            if str(
                user.get("role_name")
                or user.get("role")
                or ""
            ).strip().lower()
            == "project engineer"
        ]

        self.engineer_lookup = {
            self.format_engineer_name(user): user
            for user in self.engineers
        }

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_form()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )

        header.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(
            header,
            fg_color="transparent",
        )
        title_frame.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=18,
        )

        ctk.CTkLabel(
            title_frame,
            text="Record Supplier Clarification",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.TEXT,
        ).pack(anchor="w")

        mr_number = (
            self.request.get("mr_number", "")
            if self.request
            else ""
        )

        ctk.CTkLabel(
            title_frame,
            text=f"Material Request: {mr_number}",
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ctk.CTkButton(
            header,
            text="Cancel",
            width=100,
            height=36,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self.cancel,
        ).grid(
            row=0,
            column=1,
            padx=(5, 20),
            pady=18,
        )

        ctk.CTkButton(
            header,
            text="Save Clarification",
            width=160,
            height=36,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.save_clarification,
        ).grid(
            row=0,
            column=2,
            padx=(5, 20),
            pady=18,
        )

    def build_form(self):
        form = ctk.CTkScrollableFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        form.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        form.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            form,
            text="Supplier Clarification Details",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(20, 10),
        )

        self.supplier_name_entry = self.add_entry(
            form,
            "Supplier Name",
            row=1,
            column=0,
        )

        self.supplier_reference_entry = self.add_entry(
            form,
            "Supplier Reference / RFQ Reference",
            row=1,
            column=1,
        )

        self.subject_entry = self.add_entry(
            form,
            "Clarification Subject *",
            row=2,
            column=0,
            columnspan=2,
        )

        engineer_values = list(
            self.engineer_lookup.keys()
        )

        if not engineer_values:
            engineer_values = [
                "No active Project Engineers"
            ]

        self.engineer_option = self.add_option(
            form,
            "Assign to Project Engineer *",
            engineer_values,
            row=3,
            column=0,
            columnspan=2,
        )

        self.question_textbox = self.add_textbox(
            form,
            "Supplier Question / Clarification *",
            row=4,
            column=0,
            columnspan=2,
            height=180,
        )

        info = ctk.CTkFrame(
            form,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=10,
        )
        info.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(15, 25),
        )

        ctk.CTkLabel(
            info,
            text=(
                "The assigned Project Engineer will receive a "
                "notification requiring a technical response."
            ),
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_SECONDARY,
            wraplength=900,
            justify="left",
        ).pack(
            anchor="w",
            padx=15,
            pady=15,
        )

    # ============================================================
    # FORM HELPERS
    # ============================================================

    def add_entry(
        self,
        parent,
        label,
        *,
        row,
        column,
        columnspan=1,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=20,
            pady=8,
        )

        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        entry = ctk.CTkEntry(
            wrapper,
            height=38,
        )
        entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        return entry

    def add_option(
        self,
        parent,
        label,
        values,
        *,
        row,
        column,
        columnspan=1,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=20,
            pady=8,
        )

        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        option = ctk.CTkOptionMenu(
            wrapper,
            values=values,
            height=38,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            button_color=JCAPTheme.PRIMARY_BLUE,
            button_hover_color=JCAPTheme.PRIMARY_BLUE_HOVER,
        )
        option.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        option.set(values[0])

        return option

    def add_textbox(
        self,
        parent,
        label,
        *,
        row,
        column,
        columnspan=1,
        height=120,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=20,
            pady=8,
        )

        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        textbox = ctk.CTkTextbox(
            wrapper,
            height=height,
        )
        textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        return textbox

    # ============================================================
    # SAVE
    # ============================================================

    def validate_form(self):
        errors = []

        if not self.request:
            errors.append(
                "Material Request was not found."
            )

        if not PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        ):
            errors.append(
                "You do not have permission to record "
                "supplier clarifications."
            )

        if not self.subject_entry.get().strip():
            errors.append(
                "Clarification Subject is required."
            )

        supplier_question = self.question_textbox.get(
            "1.0",
            "end",
        ).strip()

        if not supplier_question:
            errors.append(
                "Supplier Question / Clarification is required."
            )

        selected_engineer = self.engineer_option.get()

        if selected_engineer not in self.engineer_lookup:
            errors.append(
                "A valid Project Engineer is required."
            )

        return errors

    def save_clarification(self):
        errors = self.validate_form()

        if errors:
            NotificationService.validation(
                errors
            )
            return

        selected_engineer = (
            self.engineer_lookup[
                self.engineer_option.get()
            ]
        )

        try:
            clarification_id = (
                ClarificationService
                .record_supplier_clarification(
                    material_request_id=(
                        self.material_request_id
                    ),
                    subject=(
                        self.subject_entry
                        .get()
                        .strip()
                    ),
                    supplier_question=(
                        self.question_textbox
                        .get(
                            "1.0",
                            "end",
                        )
                        .strip()
                    ),
                    project_engineer_user_id=(
                        selected_engineer["id"]
                    ),
                    current_user=self.user,
                    supplier_name=(
                        self.supplier_name_entry
                        .get()
                        .strip()
                        or None
                    ),
                    supplier_reference=(
                        self.supplier_reference_entry
                        .get()
                        .strip()
                        or None
                    ),
                )
            )

            NotificationService.success(
                (
                    "Supplier clarification was recorded "
                    "successfully.\n\n"
                    "The assigned Project Engineer has been "
                    "notified."
                ),
                title="Clarification Recorded",
            )

            if self.on_saved:
                self.on_saved(
                    clarification_id
                )

        except Exception as error:
            NotificationService.error(
                "Unable to record the supplier clarification.",
                title="Clarification Failed",
                error=error,
            )

    # ============================================================
    # NAVIGATION
    # ============================================================

    def cancel(self):
        if self.on_cancel:
            self.on_cancel()

    # ============================================================
    # DISPLAY HELPERS
    # ============================================================

    @staticmethod
    def format_engineer_name(user):
        full_name = str(
            user.get("full_name")
            or ""
        ).strip()

        employee_number = str(
            user.get("employee_number")
            or ""
        ).strip()

        if employee_number:
            return (
                f"{employee_number} - {full_name}"
            )

        return full_name