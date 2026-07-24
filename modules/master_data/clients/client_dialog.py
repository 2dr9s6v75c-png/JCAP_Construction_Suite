from __future__ import annotations

from typing import Any

import customtkinter as ctk

from modules.master_data.common.master_form_base import MasterFormBase


class ClientDialog(MasterFormBase):
    """
    Create/Edit dialog for Client Master records.

    The dialog handles form presentation and lightweight UI validation.
    ClientService remains responsible for authoritative validation,
    duplicate checking, transactions, permissions, and activity logging.
    """

    MODE_CREATE = "create"
    MODE_EDIT = "edit"

    def __init__(
        self,
        parent,
        *,
        mode: str = MODE_CREATE,
        client: dict[str, Any] | None = None,
        on_save=None,
        on_cancel=None,
    ):
        normalized_mode = str(mode or self.MODE_CREATE).strip().lower()

        if normalized_mode not in {
            self.MODE_CREATE,
            self.MODE_EDIT,
        }:
            raise ValueError(
                "ClientDialog mode must be 'create' or 'edit'."
            )

        self.mode = normalized_mode
        self.client = dict(client or {})

        self.client_name_var = ctk.StringVar()
        self.contact_person_var = ctk.StringVar()
        self.phone_var = ctk.StringVar()
        self.email_var = ctk.StringVar()

        dialog_title = (
            "New Client"
            if self.mode == self.MODE_CREATE
            else "Edit Client"
        )

        dialog_subtitle = (
            "Create a new Client Master record."
            if self.mode == self.MODE_CREATE
            else "Update the selected Client Master record."
        )

        super().__init__(
            parent,
            title=dialog_title,
            subtitle=dialog_subtitle,
            save_text=(
                "Create Client"
                if self.mode == self.MODE_CREATE
                else "Save Changes"
            ),
            width=650,
            height=720,
            on_save=on_save,
            on_cancel=on_cancel,
        )

        self._load_client_data()

    # ============================================================
    # FORM BUILD
    # ============================================================

    def build_form_fields(
        self,
        container: ctk.CTkFrame,
    ) -> None:
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        row = 0

        self.add_field_label(
            container,
            row=row,
            text="Client Name",
            required=True,
            columnspan=2,
        )
        row += 1

        self.client_name_entry = self.add_entry(
            container,
            row=row,
            variable=self.client_name_var,
            placeholder_text="Enter the registered or business name",
            columnspan=2,
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Contact Person",
            column=0,
            padx=(0, 6),
        )
        self.add_field_label(
            container,
            row=row,
            text="Phone Number",
            column=1,
            padx=(6, 0),
        )
        row += 1

        self.contact_person_entry = self.add_entry(
            container,
            row=row,
            variable=self.contact_person_var,
            placeholder_text="Primary contact person",
            column=0,
            padx=(0, 6),
        )
        self.phone_entry = self.add_entry(
            container,
            row=row,
            variable=self.phone_var,
            placeholder_text="Telephone or mobile number",
            column=1,
            padx=(6, 0),
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Email Address",
            columnspan=2,
        )
        row += 1

        self.email_entry = self.add_entry(
            container,
            row=row,
            variable=self.email_var,
            placeholder_text="name@example.com",
            columnspan=2,
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Address",
            columnspan=2,
        )
        row += 1

        self.address_textbox = self.add_textbox(
            container,
            row=row,
            height=105,
            columnspan=2,
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
            height=105,
            columnspan=2,
        )

    # ============================================================
    # DATA
    # ============================================================

    def _load_client_data(self) -> None:
        self.client_name_var.set(
            str(self.client.get("client_name") or "")
        )
        self.contact_person_var.set(
            str(self.client.get("contact_person") or "")
        )
        self.phone_var.set(
            str(self.client.get("phone") or "")
        )
        self.email_var.set(
            str(self.client.get("email") or "")
        )

        self.set_textbox_value(
            self.address_textbox,
            self.client.get("address"),
        )
        self.set_textbox_value(
            self.remarks_textbox,
            self.client.get("remarks"),
        )

        self.after(
            80,
            self.client_name_entry.focus_set,
        )

    def collect_form_data(
        self,
    ) -> dict[str, Any]:
        return {
            "client_name": self.client_name_var.get(),
            "contact_person": self.contact_person_var.get(),
            "phone": self.phone_var.get(),
            "email": self.email_var.get(),
            "address": self.get_textbox_value(
                self.address_textbox
            ),
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

        if not cleaned["client_name"]:
            self.client_name_entry.focus_set()
            raise ValueError("Client name is required.")

        if len(cleaned["client_name"]) > 255:
            self.client_name_entry.focus_set()
            raise ValueError(
                "Client name must not exceed 255 characters."
            )

        if (
            cleaned["contact_person"]
            and len(cleaned["contact_person"]) > 255
        ):
            self.contact_person_entry.focus_set()
            raise ValueError(
                "Contact person must not exceed 255 characters."
            )

        if cleaned["phone"] and len(cleaned["phone"]) > 50:
            self.phone_entry.focus_set()
            raise ValueError(
                "Phone number must not exceed 50 characters."
            )

        if cleaned["email"]:
            if len(cleaned["email"]) > 255:
                self.email_entry.focus_set()
                raise ValueError(
                    "Email address must not exceed 255 characters."
                )

            if (
                "@" not in cleaned["email"]
                or "." not in cleaned["email"].split("@")[-1]
            ):
                self.email_entry.focus_set()
                raise ValueError(
                    "Please enter a valid email address."
                )

        return cleaned

    # ============================================================
    # CONVENIENCE
    # ============================================================

    @property
    def client_id(self) -> Any:
        return self.client.get("id")

    @property
    def is_edit_mode(self) -> bool:
        return self.mode == self.MODE_EDIT