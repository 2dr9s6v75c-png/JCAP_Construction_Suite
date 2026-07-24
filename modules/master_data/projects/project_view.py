from __future__ import annotations

from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from core.security.permissions import PermissionService
from core.theme import JCAPTheme
from modules.master_data.common.master_data_grid import MasterDataGrid
from modules.master_data.common.master_data_toolbar import MasterDataToolbar
from modules.master_data.projects.project_dialog import ProjectDialog
from modules.master_data.projects.project_service import ProjectService


class ProjectManagementView(ctk.CTkFrame):
    """
    Complete Project Master Management workspace.

    Features:
    - Service-backed loading
    - Live search and status filtering
    - Create and Edit workflows
    - Archive and Restore workflows
    - Permission-aware controls
    - Selection preservation
    - Busy-state handling
    - User-friendly notifications and error handling
    """

    SEARCH_DELAY_MS = 250

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
        self._is_busy = False

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
                "linked to Client Master records."
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
                "Search project code, project name, or client..."
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
        self._cancel_pending_search()

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

        if self.can_edit and bool(project.get("is_active")):
            self._handle_edit()

    def _handle_search_change(
        self,
        _search_text: str,
    ) -> None:
        self._cancel_pending_search()

        self._search_after_id = self.after(
            self.SEARCH_DELAY_MS,
            self._run_delayed_search,
        )

    def _run_delayed_search(self) -> None:
        self._search_after_id = None
        self.load_projects()

    def _handle_status_change(
        self,
        _status: str,
    ) -> None:
        self._cancel_pending_search()
        self._clear_selection()
        self.load_projects(
            preserve_selection=False,
        )

    def _handle_refresh(self) -> None:
        self._cancel_pending_search()
        self.load_projects()

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
        self.selected_project = self._prepare_project_row(
            project
        )

        self.load_projects(
            preserve_selection=True,
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
            messagebox.showinfo(
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
                "available in historical records."
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
        except PermissionError as exc:
            self._show_error(
                "Permission Denied",
                str(exc),
            )
            return
        except (ValueError, RuntimeError) as exc:
            self._show_error(
                "Unable to Archive Project",
                str(exc),
            )
            return
        except Exception as exc:
            self._show_error(
                "Unable to Archive Project",
                (
                    "The Project Master record could not be archived."
                    f"\n\nDetails: {exc}"
                ),
            )
            return
        finally:
            self._set_busy(False)

        self._after_project_status_changed(
            archived,
            action="archived",
        )

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
            messagebox.showinfo(
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
                "The associated Client Master record must be active."
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
        except PermissionError as exc:
            self._show_error(
                "Permission Denied",
                str(exc),
            )
            return
        except (ValueError, RuntimeError) as exc:
            self._show_error(
                "Unable to Restore Project",
                str(exc),
            )
            return
        except Exception as exc:
            self._show_error(
                "Unable to Restore Project",
                (
                    "The Project Master record could not be restored."
                    f"\n\nDetails: {exc}"
                ),
            )
            return
        finally:
            self._set_busy(False)

        self._after_project_status_changed(
            restored,
            action="restored",
        )

    def _after_project_status_changed(
        self,
        project: dict[str, Any],
        *,
        action: str,
    ) -> None:
        self.selected_project = self._prepare_project_row(
            project
        )

        self.load_projects(
            preserve_selection=True,
        )

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
    ) -> None:
        if self._is_loading:
            return

        if not self.can_view:
            self.projects = []
            self._clear_selection()
            self.grid_view.set_empty_message(
                "You do not have permission to view Project Master records."
            )
            self.grid_view.set_rows(
                [],
                preserve_selection=False,
            )
            return

        self._is_loading = True

        try:
            search_text = self.toolbar.get_search_text()
            status_filter = self.toolbar.get_status_filter()

            if search_text:
                projects = ProjectService.search(
                    search_text=search_text,
                    status_filter=status_filter,
                    current_user=self.user,
                )
            else:
                projects = ProjectService.get_all(
                    status_filter=status_filter,
                    current_user=self.user,
                )

            self.projects = [
                self._prepare_project_row(project)
                for project in projects
            ]

            self.grid_view.set_empty_message(
                self._build_empty_message(
                    search_text=search_text,
                    status_filter=status_filter,
                )
            )

            self.grid_view.set_rows(
                self.projects,
                preserve_selection=preserve_selection,
            )

            self.selected_project = (
                self.grid_view.get_selected_row()
            )
            self.toolbar.set_selected_record(
                self.selected_project
            )

        except PermissionError as exc:
            self._handle_load_error(
                title="Permission Denied",
                message=str(exc),
            )
        except (ValueError, RuntimeError) as exc:
            self._handle_load_error(
                title="Unable to Load Projects",
                message=str(exc),
            )
        except Exception as exc:
            self._handle_load_error(
                title="Unable to Load Projects",
                message=(
                    "The Project Master records could not be loaded.\n\n"
                    f"Details: {exc}"
                ),
            )
        finally:
            self._is_loading = False

    def _handle_load_error(
        self,
        *,
        title: str,
        message: str,
    ) -> None:
        self.projects = []
        self._clear_selection()

        self.grid_view.set_empty_message(
            "Project Master records could not be loaded."
        )
        self.grid_view.set_rows(
            [],
            preserve_selection=False,
        )

        self._show_error(
            title,
            message,
        )

    @staticmethod
    def _prepare_project_row(
        project: dict[str, Any],
    ) -> dict[str, Any]:
        row = dict(project)

        for key in (
            "project_code",
            "project_name",
            "client_name",
            "remarks",
        ):
            if row.get(key) is None:
                row[key] = ""

        row["status_display"] = (
            "Active"
            if bool(row.get("is_active"))
            else "Inactive"
        )

        return row

    @staticmethod
    def _build_empty_message(
        *,
        search_text: str,
        status_filter: str,
    ) -> str:
        if search_text:
            return (
                f'No {status_filter.lower()} projects match '
                f'"{search_text}".'
            )

        if status_filter == MasterDataToolbar.FILTER_INACTIVE:
            return "No inactive Project Master records found."

        if status_filter == MasterDataToolbar.FILTER_ALL:
            return "No Project Master records found."

        return "No active Project Master records found."

    # ============================================================
    # STATE / MESSAGE HELPERS
    # ============================================================

    def _get_selected_project(
        self,
    ) -> dict[str, Any] | None:
        return (
            self.selected_project
            or self.grid_view.get_selected_row()
        )

    def _clear_selection(self) -> None:
        self.selected_project = None
        self.grid_view.clear_selection()
        self.toolbar.clear_selection()

    def _cancel_pending_search(self) -> None:
        if self._search_after_id is None:
            return

        try:
            self.after_cancel(self._search_after_id)
        except (ValueError, ctk.TclError):
            pass
        finally:
            self._search_after_id = None

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        self._is_busy = busy
        cursor = "wait" if busy else ""

        try:
            self.winfo_toplevel().configure(
                cursor=cursor
            )
            self.update_idletasks()
        except ctk.TclError:
            pass

    def _show_permission_denied(
        self,
        action_text: str,
    ) -> None:
        self._show_error(
            "Permission Denied",
            f"You do not have permission to {action_text}.",
        )

    def _show_selection_warning(
        self,
        action_name: str,
    ) -> None:
        messagebox.showwarning(
            "Select a Project",
            (
                "Select a Project Master record before "
                f"clicking {action_name}."
            ),
            parent=self.winfo_toplevel(),
        )

    def _show_error(
        self,
        title: str,
        message: str,
    ) -> None:
        messagebox.showerror(
            title,
            message,
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
            for value in (
                project_code,
                project_name,
            )
            if value
        )

        return label or "the selected project"

    # ============================================================
    # FORMATTERS
    # ============================================================

    @staticmethod
    def _format_status(
        _value: Any,
        row: dict[str, Any],
    ) -> str:
        return (
            "Active"
            if bool(row.get("is_active"))
            else "Inactive"
        )