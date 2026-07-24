from __future__ import annotations

from typing import Any

import customtkinter as ctk

from modules.master_data.common.master_form_base import MasterFormBase
from modules.master_data.projects.project_service import ProjectService


class SiteDialog(MasterFormBase):
    """
    Create/Edit dialog for Site Master records.

    The dialog handles:
    - Site name entry
    - Active Project Master selection
    - Automatic Client display based on the selected project
    - Optional remarks
    - Lightweight UI validation and data binding

    SiteService remains responsible for authoritative validation,
    duplicate checking, permissions, transactions, code generation,
    project validation, and activity logging.
    """

    MODE_CREATE = "create"
    MODE_EDIT = "edit"

    PROJECT_PLACEHOLDER = "Select an active project"
    NO_PROJECTS_MESSAGE = "No active projects available"
    PROJECT_LOAD_ERROR = "Unable to load active projects"
    CLIENT_PLACEHOLDER = "Client will appear after project selection"

    def __init__(
        self,
        parent,
        *,
        current_user: dict[str, Any],
        mode: str = MODE_CREATE,
        site: dict[str, Any] | None = None,
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
                "SiteDialog mode must be 'create' or 'edit'."
            )

        if not current_user:
            raise ValueError(
                "SiteDialog requires an authenticated user."
            )

        self.current_user = current_user
        self.mode = normalized_mode
        self.site = dict(site or {})

        self.projects: list[dict[str, Any]] = []
        self.project_lookup: dict[str, dict[str, Any]] = {}

        self.site_name_var = ctk.StringVar()
        self.project_display_var = ctk.StringVar(
            value=self.PROJECT_PLACEHOLDER
        )
        self.client_display_var = ctk.StringVar(
            value=self.CLIENT_PLACEHOLDER
        )

        dialog_title = (
            "New Site"
            if self.mode == self.MODE_CREATE
            else "Edit Site"
        )

        dialog_subtitle = (
            "Create a new Site Master record."
            if self.mode == self.MODE_CREATE
            else "Update the selected Site Master record."
        )

        super().__init__(
            parent,
            title=dialog_title,
            subtitle=dialog_subtitle,
            save_text=(
                "Create Site"
                if self.mode == self.MODE_CREATE
                else "Save Changes"
            ),
            width=680,
            height=660,
            on_save=on_save,
            on_cancel=on_cancel,
        )

        self._load_active_projects()
        self._load_site_data()

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
            text="Site Name",
            required=True,
        )
        row += 1

        self.site_name_entry = self.add_entry(
            container,
            row=row,
            variable=self.site_name_var,
            placeholder_text="Enter the site name or location",
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Project",
            required=True,
        )
        row += 1

        self.project_option = ctk.CTkOptionMenu(
            container,
            variable=self.project_display_var,
            values=[self.PROJECT_PLACEHOLDER],
            height=40,
            dynamic_resizing=False,
            command=self._handle_project_change,
        )
        self.project_option.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 14),
        )
        row += 1

        self.add_field_label(
            container,
            row=row,
            text="Client",
        )
        row += 1

        self.client_entry = ctk.CTkEntry(
            container,
            textvariable=self.client_display_var,
            height=40,
            state="disabled",
        )
        self.client_entry.grid(
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
            height=160,
        )

    # ============================================================
    # PROJECT DATA
    # ============================================================

    def _load_active_projects(self) -> None:
        """
        Load active Project Master records for the dropdown.

        In Edit mode, the currently assigned project is preserved
        when present in the supplied Site record, even if it is not
        returned by the active-project query. SiteService remains the
        authority on whether the project can be used when saving.
        """
        try:
            projects = ProjectService.get_active(
                current_user=self.current_user,
            )

            self.projects = [
                project
                for project in projects
                if project.get("id")
                and str(
                    project.get("project_name") or ""
                ).strip()
            ]

            self.project_lookup = {}

            for project in self.projects:
                display_name = self._format_project_display(
                    project
                )
                self.project_lookup[display_name] = project

            values = list(self.project_lookup.keys())

            current_project_id = self.site.get("project_id")
            current_project_name = str(
                self.site.get("project_name") or ""
            ).strip()
            current_project_code = str(
                self.site.get("project_code") or ""
            ).strip()
            current_client_id = self.site.get("client_id")
            current_client_name = str(
                self.site.get("client_name") or ""
            ).strip()
            current_client_code = str(
                self.site.get("client_code") or ""
            ).strip()

            current_is_available = any(
                str(project.get("id")) ==
                str(current_project_id)
                for project in self.projects
            )

            if (
                self.mode == self.MODE_EDIT
                and current_project_id
                and current_project_name
                and not current_is_available
            ):
                current_project = {
                    "id": current_project_id,
                    "project_name": current_project_name,
                    "project_code": current_project_code,
                    "client_id": current_client_id,
                    "client_name": current_client_name,
                    "client_code": current_client_code,
                }

                current_display = self._format_project_display(
                    current_project
                )
                self.project_lookup[current_display] = (
                    current_project
                )
                values.insert(0, current_display)

            if not values:
                self.project_option.configure(
                    values=[self.NO_PROJECTS_MESSAGE],
                    state="disabled",
                )
                self.project_display_var.set(
                    self.NO_PROJECTS_MESSAGE
                )
                self.client_display_var.set(
                    self.CLIENT_PLACEHOLDER
                )
                self._set_save_enabled(False)
                return

            self.project_option.configure(
                values=values,
                state="normal",
            )

            self.project_display_var.set(values[0])
            self._update_client_display(values[0])
            self._set_save_enabled(True)

        except Exception:
            self.projects = []
            self.project_lookup = {}

            self.project_option.configure(
                values=[self.PROJECT_LOAD_ERROR],
                state="disabled",
            )
            self.project_display_var.set(
                self.PROJECT_LOAD_ERROR
            )
            self.client_display_var.set(
                self.CLIENT_PLACEHOLDER
            )
            self._set_save_enabled(False)
            raise

    @staticmethod
    def _format_project_display(
        project: dict[str, Any],
    ) -> str:
        project_code = str(
            project.get("project_code") or ""
        ).strip()
        project_name = str(
            project.get("project_name") or ""
        ).strip()

        if project_code:
            return f"{project_code} - {project_name}"

        return project_name

    @staticmethod
    def _format_client_display(
        project: dict[str, Any],
    ) -> str:
        client_code = str(
            project.get("client_code") or ""
        ).strip()
        client_name = str(
            project.get("client_name") or ""
        ).strip()

        if client_code and client_name:
            return f"{client_code} - {client_name}"

        if client_name:
            return client_name

        return "Client information unavailable"

    def _handle_project_change(
        self,
        selected_display: str,
    ) -> None:
        self._update_client_display(selected_display)

    def _update_client_display(
        self,
        selected_display: str,
    ) -> None:
        project = self.project_lookup.get(
            selected_display
        )

        if not project:
            self.client_display_var.set(
                self.CLIENT_PLACEHOLDER
            )
            return

        self.client_display_var.set(
            self._format_client_display(project)
        )

    def _set_save_enabled(
        self,
        enabled: bool,
    ) -> None:
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
    # SITE DATA
    # ============================================================

    def _load_site_data(self) -> None:
        self.site_name_var.set(
            str(
                self.site.get("site_name")
                or ""
            )
        )

        self.set_textbox_value(
            self.remarks_textbox,
            self.site.get("remarks"),
        )

        site_project_id = self.site.get("project_id")

        if site_project_id:
            for display_name, project in (
                self.project_lookup.items()
            ):
                if str(project.get("id")) == str(
                    site_project_id
                ):
                    self.project_display_var.set(
                        display_name
                    )
                    self._update_client_display(
                        display_name
                    )
                    break

        self.after(
            80,
            self.site_name_entry.focus_set,
        )

    # ============================================================
    # FORM DATA
    # ============================================================

    def collect_form_data(
        self,
    ) -> dict[str, Any]:
        selected_display = (
            self.project_display_var.get()
        )
        selected_project = self.project_lookup.get(
            selected_display
        )

        return {
            "site_name": self.site_name_var.get(),
            "project_id": (
                selected_project.get("id")
                if selected_project
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
        site_name = str(
            data.get("site_name") or ""
        ).strip()
        project_id = data.get("project_id")
        remarks = str(
            data.get("remarks") or ""
        ).strip()

        if not site_name:
            self.site_name_entry.focus_set()
            raise ValueError(
                "Site name is required."
            )

        if len(site_name) > 255:
            self.site_name_entry.focus_set()
            raise ValueError(
                "Site name must not exceed 255 characters."
            )

        if not project_id:
            self.project_option.focus_set()
            raise ValueError(
                "Project is required."
            )

        return {
            "site_name": site_name,
            "project_id": project_id,
            "remarks": remarks or None,
        }