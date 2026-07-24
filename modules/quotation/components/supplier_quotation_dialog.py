from __future__ import annotations

from datetime import date, datetime
from typing import Any

import customtkinter as ctk

from modules.master_data.common.master_form_base import MasterFormBase
from modules.quotation.services.supplier_quotation_service import (
    DEFAULT_SUPPLIER_QUOTATION_STATUS,
    MAX_QUOTATION_REFERENCE_LENGTH,
    MAX_QUOTATION_REMARKS_LENGTH,
    MAX_SUPPLIER_NAME_LENGTH,
    SUPPLIER_QUOTATION_STATUSES,
)


class SupplierQuotationDialog(MasterFormBase):
    """
    Create/Edit dialog for Supplier Quotation records.

    The dialog owns form presentation and lightweight UI validation.
    SupplierQuotationProcess and SupplierQuotationService remain responsible
    for transactions, permissions, business validation, activity logging,
    and database operations.
    """

    MODE_CREATE = "create"
    MODE_EDIT = "edit"

    def __init__(
        self,
        parent,
        *,
        mode: str = MODE_CREATE,
        quotation: dict[str, Any] | None = None,
        on_save=None,
        on_cancel=None,
    ):
        normalized_mode = str(
            mode or self.MODE_CREATE
        ).strip().lower()

        if normalized_mode not in {
            self.MODE_CREATE,
            self.MODE_EDIT,
        }:
            raise ValueError(
                "SupplierQuotationDialog mode must be "
                "'create' or 'edit'."
            )

        self.mode = normalized_mode
        self.quotation = dict(quotation or {})

        self.supplier_name_var = ctk.StringVar()
        self.quotation_reference_var = ctk.StringVar()
        self.quotation_date_var = ctk.StringVar()
        self.status_var = ctk.StringVar(
            value=DEFAULT_SUPPLIER_QUOTATION_STATUS
        )

        dialog_title = (
            "New Supplier Quotation"
            if self.mode == self.MODE_CREATE
            else "Edit Supplier Quotation"
        )

        dialog_subtitle = (
            "Record a quotation received for this "
            "Material Request."
            if self.mode == self.MODE_CREATE
            else "Update the selected Supplier Quotation."
        )

        super().__init__(
            parent,
            title=dialog_title,
            subtitle=dialog_subtitle,
            save_text=(
                "Create Quotation"
                if self.mode == self.MODE_CREATE
                else "Save Changes"
            ),
            width=690,
            height=720,
            on_save=on_save,
            on_cancel=on_cancel,
        )

        self._load_quotation_data()

    # ============================================================
    # FORM BUILD
    # ============================================================

    def build_form_fields(
        self,
        container: ctk.CTkFrame,
    ) -> None:
        container.grid_columnconfigure(
            0,
            weight=1,
        )
        container.grid_columnconfigure(
            1,
            weight=1,
        )

        row = 0

        self.add_field_label(
            container,
            row=row,
            text="Supplier Name",
            required=True,
            columnspan=2,
        )
        row += 1

        self.supplier_name_entry = self.add_entry(
            container,
            row=row,
            variable=self.supplier_name_var,
            placeholder_text="Enter supplier business name",
            columnspan=2,
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Quotation Reference No.",
            column=0,
            padx=(0, 6),
        )
        self.add_field_label(
            container,
            row=row,
            text="Quotation Date",
            column=1,
            padx=(6, 0),
        )
        row += 1

        self.quotation_reference_entry = self.add_entry(
            container,
            row=row,
            variable=self.quotation_reference_var,
            placeholder_text="Optional reference number",
            column=0,
            padx=(0, 6),
        )

        self.quotation_date_entry = self.add_entry(
            container,
            row=row,
            variable=self.quotation_date_var,
            placeholder_text="YYYY-MM-DD",
            column=1,
            padx=(6, 0),
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Status",
            required=True,
            columnspan=2,
        )
        row += 1

        self.status_menu = ctk.CTkOptionMenu(
            container,
            variable=self.status_var,
            values=list(SUPPLIER_QUOTATION_STATUSES),
            height=38,
            fg_color="#FFFFFF",
            button_color="#1976D2",
            button_hover_color="#0D47A1",
            text_color="#111827",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#111827",
            dropdown_hover_color="#E3F2FD",
        )
        self.status_menu.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=0,
            pady=(0, 14),
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Remarks",
            columnspan=2,
        )
        row += 1

        self.remarks_textbox = self.add_textbox(
            container,
            row=row,
            height=150,
            columnspan=2,
        )

    # ============================================================
    # DATA
    # ============================================================

    def _load_quotation_data(self) -> None:
        self.supplier_name_var.set(
            str(
                self.quotation.get(
                    "supplier_name"
                )
                or ""
            )
        )

        self.quotation_reference_var.set(
            str(
                self.quotation.get(
                    "quotation_reference"
                )
                or ""
            )
        )

        self.quotation_date_var.set(
            self._format_date_for_entry(
                self.quotation.get(
                    "quotation_date"
                )
            )
        )

        status = str(
            self.quotation.get("status")
            or DEFAULT_SUPPLIER_QUOTATION_STATUS
        ).strip()

        if status not in SUPPLIER_QUOTATION_STATUSES:
            status = DEFAULT_SUPPLIER_QUOTATION_STATUS

        self.status_var.set(status)

        self.set_textbox_value(
            self.remarks_textbox,
            self.quotation.get("remarks"),
        )

        self.after(
            80,
            self.supplier_name_entry.focus_set,
        )

    def collect_form_data(
        self,
    ) -> dict[str, Any]:
        return {
            "supplier_name": (
                self.supplier_name_var.get()
            ),
            "quotation_reference": (
                self.quotation_reference_var.get()
            ),
            "quotation_date": (
                self.quotation_date_var.get()
            ),
            "status": self.status_var.get(),
            "remarks": self.get_textbox_value(
                self.remarks_textbox
            ),
        }

    def validate_form_data(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        cleaned = {
            key: str(value or "").strip()
            for key, value in data.items()
        }

        supplier_name = cleaned["supplier_name"]

        if not supplier_name:
            self.supplier_name_entry.focus_set()
            raise ValueError(
                "Supplier name is required."
            )

        if len(supplier_name) > MAX_SUPPLIER_NAME_LENGTH:
            self.supplier_name_entry.focus_set()
            raise ValueError(
                "Supplier name must not exceed "
                f"{MAX_SUPPLIER_NAME_LENGTH} characters."
            )

        quotation_reference = cleaned[
            "quotation_reference"
        ]

        if (
            quotation_reference
            and len(quotation_reference)
            > MAX_QUOTATION_REFERENCE_LENGTH
        ):
            self.quotation_reference_entry.focus_set()
            raise ValueError(
                "Quotation reference must not exceed "
                f"{MAX_QUOTATION_REFERENCE_LENGTH} characters."
            )

        quotation_date = cleaned["quotation_date"]

        if quotation_date:
            try:
                parsed_date = datetime.strptime(
                    quotation_date,
                    "%Y-%m-%d",
                ).date()

            except ValueError as error:
                self.quotation_date_entry.focus_set()
                raise ValueError(
                    "Quotation date must use YYYY-MM-DD."
                ) from error

            cleaned["quotation_date"] = parsed_date

        else:
            cleaned["quotation_date"] = None

        status = cleaned["status"]

        if status not in SUPPLIER_QUOTATION_STATUSES:
            self.status_menu.focus_set()
            raise ValueError(
                "Select a valid Supplier Quotation status."
            )

        remarks = cleaned["remarks"]

        if len(remarks) > MAX_QUOTATION_REMARKS_LENGTH:
            self.remarks_textbox.focus_set()
            raise ValueError(
                "Remarks must not exceed "
                f"{MAX_QUOTATION_REMARKS_LENGTH} characters."
            )

        cleaned["quotation_reference"] = (
            quotation_reference or None
        )
        cleaned["remarks"] = remarks or None

        return cleaned

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _format_date_for_entry(
        value: Any,
    ) -> str:
        if isinstance(value, datetime):
            value = value.date()

        if isinstance(value, date):
            return value.isoformat()

        text = str(value or "").strip()

        if not text:
            return ""

        try:
            return datetime.fromisoformat(
                text
            ).date().isoformat()

        except ValueError:
            return text