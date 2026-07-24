from __future__ import annotations

from typing import Any

import customtkinter as ctk
from tkinter import messagebox

from core.security.permissions import PermissionService
from core.theme import JCAPTheme
from modules.master_data.common.master_data_grid import MasterDataGrid
from modules.master_data.common.master_data_toolbar import MasterDataToolbar
from modules.master_data.projects.project_dialog import ProjectDialog
from modules.master_data.projects.project_service import ProjectService


class ProjectManagementView(ctk.CTkFrame):
    """
    Project Master Management workspace.

    Final implementation includes:
    - Complete view layout
    - Permission-aware toolbar
    - ProjectService-backed loading
    - Search and status filtering
    - Create Project workflow
    - Edit Project workflow
    - Archive Project workflow
    - Restore Project workflow
    - Selection preservation after data changes
    - Consistent validation and error handling
    """

    SEARCH_DELAY_MS = 300

    def __init__(
        self,
        parent,
        user: dict[str, Any],
        on_back=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.on_back = on_back

        self.projects: list[dict[str, Any]] = []
        self.selected_project: dict[str, Any] | None = None
        self._search_after_id: str | None = None
        self._is_loading = False

        self.can_view = PermissionService.can_view_projects(
            self.user
        )
        self.can_create = PermissionService.can_create_projects(
            self.user
        )
        self.can_edit = PermissionService.can_edit_projects(
            self.user
        )
        self.can_archive = PermissionService.can_archive_projects(
            self.user
        )
        self.can_restore = PermissionService.can_restore_projects(
            self.user
        )

        self._build_ui()
        self.load_projects()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_grid()

    def _build_header(self) -> None:
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

        title_block = ctk.CTkFrame(
            header,
            fg_color="transparent",
        )
        title_block.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=16,
        )

        ctk.CTkLabel(
            title_block,
            text="Project Management",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Create and maintain Project Master records "
                "linked to Project and Client Master records."
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        ctk.CTkButton(
            header,
            text="Back",
            width=100,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self._handle_back,
        ).grid(
            row=0,
            column=1,
            padx=(10, 20),
            pady=16,
        )

    def _build_toolbar(self) -> None:
        self.toolbar = MasterDataToolbar(
            self,
            search_placeholder=(
                "Search project code, project name, or client."
            ),
            on_search_change=self._handle_search_change,
            on_status_change=self._handle_status_change,
            on_new=self._handle_new,
            on_edit=self._handle_edit,
            on_archive=self._handle_archive,
            on_restore=self._handle_restore,
            on_refresh=self._handle_refresh,
            can_create=self.can_create,
            can_edit=self.can_edit,
            can_archive=self.can_archive,
            can_restore=self.can_restore,
            initial_status=MasterDataToolbar.FILTER_ACTIVE,
        )
        self.toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

    def _build_grid(self) -> None:
        columns = [
            {
                "key": "project_code",
                "title": "Project Code",
                "weight": 1,
            },
            {
                "key": "project_name",
                "title": "Project Name",
                "weight": 3,
            },
            {
                "key": "client_name",
                "title": "Client",
                "weight": 2,
            },
            {
                "key": "remarks",
                "title": "Remarks",
                "weight": 2,
            },
            {
                "key": "status_display",
                "title": "Status",
                "weight": 1,
                "formatter": self._format_status,
                "font": ("Segoe UI", 11, "bold"),
            },
        ]

        self.grid_view = MasterDataGrid(
            self,
            columns=columns,
            id_key="id",
            empty_message="No Project Master records found.",
            result_label_singular="project",
            result_label_plural="projects",
            on_select=self._handle_grid_selection,
            on_double_click=self._handle_grid_double_click,
        )
        self.grid_view.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

    # ============================================================
    # EVENT WIRING
    # ============================================================

    def _handle_back(self) -> None:
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass

            self._search_after_id = None

        if self.on_back:
            self.on_back()

    def _handle_grid_selection(
        self,
        project: dict[str, Any] | None,
    ) -> None:
        self.selected_project = project
        self.toolbar.set_selected_record(project)

    def _handle_grid_double_click(
        self,
        project: dict[str, Any],
    ) -> None:
        self.selected_project = project
        self.toolbar.set_selected_record(project)

        if self.can_edit:
            self._handle_edit()

    def _handle_search_change(
        self,
        _search_text: str,
    ) -> None:
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass

        self._search_after_id = self.after(
            self.SEARCH_DELAY_MS,
            self._run_debounced_search,
        )

    def _run_debounced_search(self) -> None:
        self._search_after_id = None
        self.load_projects()

    def _handle_status_change(
        self,
        _status: str,
    ) -> None:
        self.clear_selection()
        self.load_projects()

    def _handle_refresh(self) -> None:
        self.load_projects(
            preserve_selection=True,
        )

    # ============================================================
    # CREATE / EDIT
    # ============================================================

    def _handle_new(self) -> None:
        if not self.can_create:
            self._show_permission_denied(
                "create Project Master records"
            )
            return

        ProjectDialog(
            self,
            current_user=self.user,
            mode=ProjectDialog.MODE_CREATE,
            on_save=self._create_project,
        )

    def _handle_edit(self) -> None:
        if not self.can_edit:
            self._show_permission_denied(
                "edit Project Master records"
            )
            return

        project = self._get_selected_project()

        if not project:
            self._show_selection_warning("Edit")
            return

        if not bool(project.get("is_active")):
            messagebox.showwarning(
                "Editing Disabled",
                (
                    "Inactive Project Master records cannot be edited.\n\n"
                    "Restore the project before editing it."
                ),
                parent=self.winfo_toplevel(),
            )
            return

        ProjectDialog(
            self,
            current_user=self.user,
            mode=ProjectDialog.MODE_EDIT,
            project=project,
            on_save=lambda data: self._update_project(
                project.get("id"),
                data,
            ),
        )

    def _create_project(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        self._set_busy(True)

        try:
            created = ProjectService.create_project(
                data,
                current_user=self.user,
            )

            self.after_idle(
                lambda record=created: self._after_project_saved(
                    record,
                    action="created",
                )
            )

            return created
        finally:
            self._set_busy(False)

    def _update_project(
        self,
        project_id: Any,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        if not project_id:
            raise ValueError(
                "The selected Project Master record has no ID."
            )

        self._set_busy(True)

        try:
            updated = ProjectService.update_project(
                project_id,
                data,
                current_user=self.user,
            )

            self.after_idle(
                lambda record=updated: self._after_project_saved(
                    record,
                    action="updated",
                )
            )

            return updated
        finally:
            self._set_busy(False)

    def _after_project_saved(
        self,
        project: dict[str, Any],
        *,
        action: str,
    ) -> None:
        prepared_project = self._prepare_project_row(project)
        self.selected_project = prepared_project

        self.load_projects(
            preserve_selection=True,
            selected_project_id=project.get("id"),
        )

        messagebox.showinfo(
            "Project Saved",
            (
                f"Project Master record "
                f"{self._project_label(project)} was "
                f"{action} successfully."
            ),
            parent=self.winfo_toplevel(),
        )

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        cursor = "wait" if busy else ""

        try:
            self.winfo_toplevel().configure(
                cursor=cursor
            )
            self.update_idletasks()
        except ctk.TclError:
            pass

    # ============================================================
    # ARCHIVE / RESTORE
    # ============================================================

    def _handle_archive(self) -> None:
        if not self.can_archive:
            self._show_permission_denied(
                "archive Project Master records"
            )
            return

        project = self._get_selected_project()

        if not project:
            self._show_selection_warning("Archive")
            return

        if not bool(project.get("is_active")):
            messagebox.showwarning(
                "Already Inactive",
                (
                    f"Project Master record "
                    f"{self._project_label(project)} is already inactive."
                ),
                parent=self.winfo_toplevel(),
            )
            return

        confirmed = messagebox.askyesno(
            "Archive Project",
            (
                f"Archive Project Master record "
                f"{self._project_label(project)}?\n\n"
                "The project will become inactive but will remain "
                "available under the Inactive or All filter."
            ),
            parent=self.winfo_toplevel(),
        )

        if not confirmed:
            return

        self._set_busy(True)

        try:
            archived = ProjectService.deactivate_project(
                project.get("id"),
                current_user=self.user,
            )

            self._after_project_status_changed(
                archived,
                action="archived",
            )

        except PermissionError as exc:
            messagebox.showerror(
                "Permission Denied",
                str(exc),
                parent=self.winfo_toplevel(),
            )

        except ValueError as exc:
            messagebox.showwarning(
                "Unable to Archive Project",
                str(exc),
                parent=self.winfo_toplevel(),
            )

        except Exception as exc:
            messagebox.showerror(
                "Unable to Archive Project",
                (
                    "The Project Master record could not be archived."
                    f"\n\n{exc}"
                ),
                parent=self.winfo_toplevel(),
            )

        finally:
            self._set_busy(False)

    def _handle_restore(self) -> None:
        if not self.can_restore:
            self._show_permission_denied(
                "restore Project Master records"
            )
            return

        project = self._get_selected_project()

        if not project:
            self._show_selection_warning("Restore")
            return

        if bool(project.get("is_active")):
            messagebox.showwarning(
                "Already Active",
                (
                    f"Project Master record "
                    f"{self._project_label(project)} is already active."
                ),
                parent=self.winfo_toplevel(),
            )
            return

        confirmed = messagebox.askyesno(
            "Restore Project",
            (
                f"Restore Project Master record "
                f"{self._project_label(project)}?\n\n"
                "The project's linked Project Master record must "
                "also be active."
            ),
            parent=self.winfo_toplevel(),
        )

        if not confirmed:
            return

        self._set_busy(True)

        try:
            restored = ProjectService.restore_project(
                project.get("id"),
                current_user=self.user,
            )

            self._after_project_status_changed(
                restored,
                action="restored",
            )

        except PermissionError as exc:
            messagebox.showerror(
                "Permission Denied",
                str(exc),
                parent=self.winfo_toplevel(),
            )

        except ValueError as exc:
            messagebox.showwarning(
                "Unable to Restore Project",
                str(exc),
                parent=self.winfo_toplevel(),
            )

        except Exception as exc:
            messagebox.showerror(
                "Unable to Restore Project",
                (
                    "The Project Master record could not be restored."
                    f"\n\n{exc}"
                ),
                parent=self.winfo_toplevel(),
            )

        finally:
            self._set_busy(False)

    def _after_project_status_changed(
        self,
        project: dict[str, Any],
        *,
        action: str,
    ) -> None:
        project_id = project.get("id")

        self.load_projects(
            preserve_selection=True,
            selected_project_id=project_id,
        )

        # When the current filter excludes the changed record,
        # load_projects() clears the selection automatically.
        messagebox.showinfo(
            "Project Updated",
            (
                f"Project Master record "
                f"{self._project_label(project)} was "
                f"{action} successfully."
            ),
            parent=self.winfo_toplevel(),
        )

    # ============================================================
    # DATA LOADING
    # ============================================================

    def load_projects(
        self,
        *,
        preserve_selection: bool = True,
        selected_project_id: Any | None = None,
    ) -> None:
        if self._is_loading:
            return

        if not self.can_view:
            self.projects = []
            self.clear_selection()
            self.grid_view.set_rows([])
            messagebox.showerror(
                "Permission Denied",
                (
                    "You do not have permission to view "
                    "Project Master records."
                ),
                parent=self,
            )
            return

        self._is_loading = True

        try:
            if selected_project_id is None and preserve_selection:
                selected_project_id = self._get_selected_project_id()

            search_text = self._get_toolbar_search_text()
            status_filter = self._get_toolbar_status_filter()

            self.projects = ProjectService.search(
                search_text=search_text,
                status_filter=status_filter,
                current_user=self.user,
            )

            prepared_rows = [
                self._prepare_project_row(project)
                for project in self.projects
            ]

            self.grid_view.set_rows(prepared_rows)

            if selected_project_id:
                self._restore_selection(selected_project_id)
            else:
                self.clear_selection()

        except PermissionError as exc:
            self.projects = []
            self.clear_selection()
            self.grid_view.set_rows([])

            messagebox.showerror(
                "Permission Denied",
                str(exc),
                parent=self,
            )

        except Exception as exc:
            messagebox.showerror(
                "Unable to Load Projects",
                (
                    "The Project Master records could not be loaded.\n\n"
                    f"{exc}"
                ),
                parent=self,
            )

        finally:
            self._is_loading = False

    def clear_selection(self) -> None:
        self.grid_view.clear_selection()
        self.selected_project = None
        self.toolbar.set_selected_record(None)

    def _restore_selection(
        self,
        project_id: Any,
    ) -> None:
        matching_project = next(
            (
                project
                for project in self.projects
                if str(project.get("id")) == str(project_id)
            ),
            None,
        )

        if not matching_project:
            self.clear_selection()
            return

        select_method = getattr(
            self.grid_view,
            "select_by_id",
            None,
        )

        if callable(select_method):
            select_method(project_id)

        self.selected_project = matching_project
        self.toolbar.set_selected_record(
            matching_project
        )

    def _get_selected_project_id(self) -> Any | None:
        if not self.selected_project:
            return None

        return self.selected_project.get("id")

    # ============================================================
    # SELECTION / MESSAGE HELPERS
    # ============================================================

    def _get_selected_project(
        self,
    ) -> dict[str, Any] | None:
        if self.selected_project:
            return self.selected_project

        getter = getattr(
            self.grid_view,
            "get_selected_row",
            None,
        )

        if callable(getter):
            selected = getter()

            if selected:
                self.selected_project = selected
                return selected

        return None

    def _show_permission_denied(
        self,
        action_text: str,
    ) -> None:
        messagebox.showerror(
            "Permission Denied",
            f"You do not have permission to {action_text}.",
            parent=self.winfo_toplevel(),
        )

    def _show_selection_warning(
        self,
        action_text: str,
    ) -> None:
        messagebox.showwarning(
            "Select a Project",
            (
                "Select a Project Master record before "
                f"clicking {action_text}."
            ),
            parent=self.winfo_toplevel(),
        )

    @staticmethod
    def _project_label(
        project: dict[str, Any],
    ) -> str:
        project_code = str(
            project.get("project_code") or ""
        ).strip()
        project_name = str(
            project.get("project_name") or ""
        ).strip()

        label = " - ".join(
            value
            for value in (project_code, project_name)
            if value
        )

        return label or "the selected project"

    # ============================================================
    # TOOLBAR VALUE HELPERS
    # ============================================================

    def _get_toolbar_search_text(self) -> str:
        getter_names = (
            "get_search_text",
            "get_search_value",
        )

        for getter_name in getter_names:
            getter = getattr(
                self.toolbar,
                getter_name,
                None,
            )

            if callable(getter):
                return str(getter() or "").strip()

        variable_names = (
            "search_var",
            "search_text_var",
        )

        for variable_name in variable_names:
            variable = getattr(
                self.toolbar,
                variable_name,
                None,
            )

            if variable is not None and hasattr(
                variable,
                "get",
            ):
                return str(
                    variable.get() or ""
                ).strip()

        return ""

    def _get_toolbar_status_filter(self) -> str:
        getter_names = (
            "get_status_filter",
            "get_status_value",
        )

        for getter_name in getter_names:
            getter = getattr(
                self.toolbar,
                getter_name,
                None,
            )

            if callable(getter):
                return self._normalize_status_filter(
                    getter()
                )

        variable_names = (
            "status_var",
            "status_filter_var",
        )

        for variable_name in variable_names:
            variable = getattr(
                self.toolbar,
                variable_name,
                None,
            )

            if variable is not None and hasattr(
                variable,
                "get",
            ):
                return self._normalize_status_filter(
                    variable.get()
                )

        return "Active"

    @staticmethod
    def _normalize_status_filter(
        value: Any,
    ) -> str:
        normalized = str(
            value or "Active"
        ).strip().lower()

        if normalized == "all":
            return "All"

        if normalized == "inactive":
            return "Inactive"

        return "Active"

    # ============================================================
    # ROW PREPARATION
    # ============================================================

    @staticmethod
    def _prepare_project_row(
        project: dict[str, Any],
    ) -> dict[str, Any]:
        row = dict(project)

        row["project_code"] = str(
            row.get("project_code") or ""
        ).strip()

        row["project_name"] = str(
            row.get("project_name") or ""
        ).strip()

        row["client_name"] = str(
            row.get("client_name") or ""
        ).strip()

        row["remarks"] = str(
            row.get("remarks") or ""
        ).strip()

        row["status_display"] = (
            "Active"
            if bool(row.get("is_active", True))
            else "Inactive"
        )

        return row

    @staticmethod
    def _format_status(
        value: Any,
        _row: dict[str, Any] | None = None,
    ) -> str:
        return str(value or "")