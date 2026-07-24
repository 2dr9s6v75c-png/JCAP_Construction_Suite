from __future__ import annotations

from typing import Any

import customtkinter as ctk

from modules.master_data.clients.client_service import ClientService
from modules.master_data.common.master_form_base import MasterFormBase


class ProjectDialog(MasterFormBase):
    """
    Create/Edit dialog for Project Master records.

    The dialog handles:
    - Project name entry
    - Active Client Master selection
    - Optional remarks
    - Lightweight UI validation and data binding

    ProjectService remains responsible for authoritative validation,
    duplicate checking, permissions, transactions, code generation,
    and activity logging.
    """

    MODE_CREATE = "create"
    MODE_EDIT = "edit"

    CLIENT_PLACEHOLDER = "Select an active client"
    NO_CLIENTS_MESSAGE = "No active clients available"
    CLIENT_LOAD_ERROR = "Unable to load active clients"

    def __init__(
        self,
        parent,
        *,
        current_user: dict[str, Any],
        mode: str = MODE_CREATE,
        project: dict[str, Any] | None = None,
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
                "ProjectDialog mode must be 'create' or 'edit'."
            )

        if not current_user:
            raise ValueError(
                "ProjectDialog requires an authenticated user."
            )

        self.current_user = current_user
        self.mode = normalized_mode
        self.project = dict(project or {})

        self.clients: list[dict[str, Any]] = []
        self.client_lookup: dict[str, dict[str, Any]] = {}

        self.project_name_var = ctk.StringVar()
        self.client_display_var = ctk.StringVar(
            value=self.CLIENT_PLACEHOLDER
        )

        dialog_title = (
            "New Project"
            if self.mode == self.MODE_CREATE
            else "Edit Project"
        )

        dialog_subtitle = (
            "Create a new Project Master record."
            if self.mode == self.MODE_CREATE
            else "Update the selected Project Master record."
        )

        super().__init__(
            parent,
            title=dialog_title,
            subtitle=dialog_subtitle,
            save_text=(
                "Create Project"
                if self.mode == self.MODE_CREATE
                else "Save Changes"
            ),
            width=650,
            height=570,
            on_save=on_save,
            on_cancel=on_cancel,
        )

        self._load_active_clients()
        self._load_project_data()

    # ============================================================
    # FORM BUILD
    # ============================================================

    def build_form_fields(
        self,
        container: ctk.CTkFrame,
    ) -> None:
        container.grid_columnconfigure(0, weight=1)

        row = 0

        self.add_field_label(
            container,
            row=row,
            text="Project Name",
            required=True,
        )
        row += 1

        self.project_name_entry = self.add_entry(
            container,
            row=row,
            variable=self.project_name_var,
            placeholder_text="Enter the project name",
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Client",
            required=True,
        )
        row += 1

        self.client_option = ctk.CTkOptionMenu(
            container,
            variable=self.client_display_var,
            values=[self.CLIENT_PLACEHOLDER],
            height=40,
            dynamic_resizing=False,
        )
        self.client_option.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 14),
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Remarks",
        )
        row += 1

        self.remarks_textbox = self.add_textbox(
            container,
            row=row,
            height=150,
        )

    # ============================================================
    # CLIENT DATA
    # ============================================================

    def _load_active_clients(self) -> None:
        """
        Load active Client Master records for the dropdown.

        In Edit mode, the currently assigned client is also preserved
        in the dropdown when present in the supplied project data.
        The service remains the authority on whether that client is
        valid and active when the record is saved.
        """
        try:
            clients = ClientService.get_active(
                current_user=self.current_user,
            )

            self.clients = [
                client
                for client in clients
                if client.get("id")
                and str(
                    client.get("client_name") or ""
                ).strip()
            ]

            self.client_lookup = {}

            for client in self.clients:
                display_name = self._format_client_display(
                    client
                )

                # Client code makes display values naturally unique.
                self.client_lookup[display_name] = client

            values = list(self.client_lookup.keys())

            current_client_id = self.project.get("client_id")
            current_client_name = str(
                self.project.get("client_name") or ""
            ).strip()
            current_client_code = str(
                self.project.get("client_code") or ""
            ).strip()

            current_is_available = any(
                str(client.get("id")) ==
                str(current_client_id)
                for client in self.clients
            )

            if (
                self.mode == self.MODE_EDIT
                and current_client_id
                and current_client_name
                and not current_is_available
            ):
                current_client = {
                    "id": current_client_id,
                    "client_name": current_client_name,
                    "client_code": current_client_code,
                }
                current_display = self._format_client_display(
                    current_client
                )
                self.client_lookup[current_display] = (
                    current_client
                )
                values.insert(0, current_display)

            if not values:
                self.client_option.configure(
                    values=[self.NO_CLIENTS_MESSAGE],
                    state="disabled",
                )
                self.client_display_var.set(
                    self.NO_CLIENTS_MESSAGE
                )
                self._set_save_enabled(False)
                return

            self.client_option.configure(
                values=values,
                state="normal",
            )

            self.client_display_var.set(values[0])
            self._set_save_enabled(True)

        except Exception:
            self.clients = []
            self.client_lookup = {}

            self.client_option.configure(
                values=[self.CLIENT_LOAD_ERROR],
                state="disabled",
            )
            self.client_display_var.set(
                self.CLIENT_LOAD_ERROR
            )
            self._set_save_enabled(False)
            raise

    @staticmethod
    def _format_client_display(
        client: dict[str, Any],
    ) -> str:
        client_code = str(
            client.get("client_code") or ""
        ).strip()
        client_name = str(
            client.get("client_name") or ""
        ).strip()

        if client_code:
            return f"{client_code} - {client_name}"

        return client_name

    def _set_save_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        MasterFormBase exposes the save button as save_button.
        The guard keeps this dialog compatible if that implementation
        detail changes later.
        """
        save_button = getattr(
            self,
            "save_button",
            None,
        )

        if save_button is not None:
            save_button.configure(
                state=(
                    "normal"
                    if enabled
                    else "disabled"
                )
            )

    # ============================================================
    # PROJECT DATA
    # ============================================================

    def _load_project_data(self) -> None:
        self.project_name_var.set(
            str(
                self.project.get("project_name")
                or ""
            )
        )

        self.set_textbox_value(
            self.remarks_textbox,
            self.project.get("remarks"),
        )

        project_client_id = self.project.get("client_id")

        if project_client_id:
            for display_name, client in (
                self.client_lookup.items()
            ):
                if str(client.get("id")) == str(
                    project_client_id
                ):
                    self.client_display_var.set(
                        display_name
                    )
                    break

        self.after(
            80,
            self.project_name_entry.focus_set,
        )

    def collect_form_data(
        self,
    ) -> dict[str, Any]:
        selected_display = (
            self.client_display_var.get()
        )
        selected_client = self.client_lookup.get(
            selected_display
        )

        return {
            "project_name": self.project_name_var.get(),
            "client_id": (
                selected_client.get("id")
                if selected_client
                else None
            ),
            "remarks": self.get_textbox_value(
                self.remarks_textbox
            ),
        }

    def validate_form_data(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        project_name = str(
            data.get("project_name") or ""
        ).strip()
        client_id = data.get("client_id")
        remarks = str(
            data.get("remarks") or ""
        ).strip()

        if not project_name:
            self.project_name_entry.focus_set()
            raise ValueError(
                "Project name is required."
            )

        if len(project_name) > 255:
            self.project_name_entry.focus_set()
            raise ValueError(
                "Project name must not exceed 255 characters."
            )

        if not client_id:
            self.client_option.focus_set()
            raise ValueError(
                "Client is required."
            )

        return {
            "project_name": project_name,
            "client_id": client_id,
            "remarks": remarks or None,
        }

    # ============================================================
    # CONVENIENCE
    # ============================================================

    @property
    def project_id(self) -> Any:
        return self.project.get("id")

    @property
    def is_edit_mode(self) -> bool:
        return self.mode == self.MODE_EDIT