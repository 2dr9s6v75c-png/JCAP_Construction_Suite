from __future__ import annotations

from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from core.security.permissions import PermissionService
from core.theme import JCAPTheme
from modules.master_data.clients.client_dialog import ClientDialog
from modules.master_data.clients.client_service import ClientService
from modules.master_data.common.master_data_grid import MasterDataGrid
from modules.master_data.common.master_data_toolbar import MasterDataToolbar


class ClientManagementView(ctk.CTkFrame):
    SEARCH_DELAY_MS = 250

    def __init__(self, parent, user: dict[str, Any], on_back=None):
        super().__init__(parent, fg_color=JCAPTheme.BACKGROUND, corner_radius=0)
        self.user = user
        self.on_back = on_back
        self.clients: list[dict[str, Any]] = []
        self.selected_client: dict[str, Any] | None = None
        self._search_after_id: str | None = None
        self._is_loading = False

        self.can_view = PermissionService.can_view_clients(self.user)
        self.can_create = PermissionService.can_create_clients(self.user)
        self.can_edit = PermissionService.can_edit_clients(self.user)
        self.can_archive = PermissionService.can_archive_clients(self.user)
        self.can_restore = PermissionService.can_restore_clients(self.user)

        self._build_ui()
        self.load_clients()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_toolbar()
        self._build_grid()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=JCAPTheme.CARD, corner_radius=14)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w", padx=20, pady=16)

        ctk.CTkLabel(
            title_block,
            text="Client Management",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Create and maintain Client Master records used throughout "
                "the JCAP Construction Suite."
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkButton(
            header,
            text="Back",
            width=100,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self._handle_back,
        ).grid(row=0, column=1, padx=(10, 20), pady=16)

    def _build_toolbar(self) -> None:
        self.toolbar = MasterDataToolbar(
            self,
            search_placeholder=(
                "Search client code, name, contact person, phone, email..."
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
        self.toolbar.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

    def _build_grid(self) -> None:
        columns = [
            {"key": "client_code", "title": "Client Code", "weight": 1},
            {"key": "client_name", "title": "Client Name", "weight": 2},
            {"key": "contact_person", "title": "Contact Person", "weight": 2},
            {"key": "phone", "title": "Phone", "weight": 1},
            {"key": "email", "title": "Email", "weight": 2},
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
            empty_message="No Client Master records found.",
            result_label_singular="client",
            result_label_plural="clients",
            on_select=self._handle_grid_selection,
            on_double_click=self._handle_grid_double_click,
        )
        self.grid_view.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

    def _handle_back(self) -> None:
        self._cancel_pending_search()
        if self.on_back:
            self.on_back()

    def _handle_grid_selection(self, client: dict[str, Any] | None) -> None:
        self.selected_client = client
        self.toolbar.set_selected_record(client)

    def _handle_grid_double_click(self, client: dict[str, Any]) -> None:
        self.selected_client = client
        self.toolbar.set_selected_record(client)
        if self.can_edit:
            self._handle_edit()

    def _handle_search_change(self, _search_text: str) -> None:
        self._cancel_pending_search()
        self._search_after_id = self.after(
            self.SEARCH_DELAY_MS,
            self._run_delayed_search,
        )

    def _run_delayed_search(self) -> None:
        self._search_after_id = None
        self.load_clients()

    def _handle_status_change(self, _status: str) -> None:
        self._cancel_pending_search()
        self._clear_selection()
        self.load_clients(preserve_selection=False)

    def _handle_refresh(self) -> None:
        self._cancel_pending_search()
        self.load_clients()

    def _handle_new(self) -> None:
        if not self.can_create:
            self._show_permission_denied("create Client Master records")
            return

        ClientDialog(
            self,
            mode=ClientDialog.MODE_CREATE,
            on_save=self._create_client,
        )

    def _handle_edit(self) -> None:
        if not self.can_edit:
            self._show_permission_denied("edit Client Master records")
            return

        client = self.selected_client or self.grid_view.get_selected_row()
        if not client:
            messagebox.showwarning(
                "Select a Client",
                "Select a Client Master record before clicking Edit.",
                parent=self.winfo_toplevel(),
            )
            return

        if not bool(client.get("is_active")):
            messagebox.showwarning(
                "Editing Disabled",
                "Inactive Client Master records cannot be edited.\n\nRestore the client before editing it.",
                parent=self.winfo_toplevel(),
            )
            return

        ClientDialog(
            self,
            mode=ClientDialog.MODE_EDIT,
            client=client,
            on_save=lambda data: self._update_client(client.get("id"), data),
        )

    def _create_client(self, data: dict[str, Any]) -> dict[str, Any]:
        self._set_busy(True)
        try:
            created = ClientService.create_client(data, current_user=self.user)
            self.after_idle(
                lambda record=created: self._after_client_saved(record, action="created")
            )
            return created
        finally:
            self._set_busy(False)

    def _update_client(self, client_id: Any, data: dict[str, Any]) -> dict[str, Any]:
        if not client_id:
            raise ValueError("The selected Client Master record has no ID.")

        self._set_busy(True)
        try:
            updated = ClientService.update_client(
                client_id,
                data,
                current_user=self.user,
            )
            self.after_idle(
                lambda record=updated: self._after_client_saved(record, action="updated")
            )
            return updated
        finally:
            self._set_busy(False)

    def _after_client_saved(self, client: dict[str, Any], *, action: str) -> None:
        self.selected_client = self._prepare_client_row(client)
        self.load_clients(preserve_selection=True)
        messagebox.showinfo(
            "Client Saved",
            f"Client Master record {self._get_client_label(client)} was {action} successfully.",
            parent=self.winfo_toplevel(),
        )

    def _handle_archive(self) -> None:
        if not self.can_archive:
            self._show_permission_denied("archive Client Master records")
            return

        client = self.selected_client or self.grid_view.get_selected_row()
        if not client:
            messagebox.showwarning(
                "Select a Client",
                "Select an active Client Master record before clicking Archive.",
                parent=self.winfo_toplevel(),
            )
            return

        if not bool(client.get("is_active")):
            messagebox.showwarning(
                "Already Inactive",
                "The selected Client Master record is already inactive.",
                parent=self.winfo_toplevel(),
            )
            return

        client_id = client.get("id")
        if not client_id:
            messagebox.showerror(
                "Archive Failed",
                "The selected Client Master record has no valid ID.",
                parent=self.winfo_toplevel(),
            )
            return

        confirmed = messagebox.askyesno(
            "Archive Client",
            (
                f'Archive client "{self._get_client_label(client)}"?\n\n'
                "The client will be removed from the Active list but can be restored later."
            ),
            icon="warning",
            parent=self.winfo_toplevel(),
        )
        if not confirmed:
            return

        self._set_busy(True)
        try:
            archived = ClientService.deactivate_client(
                client_id,
                current_user=self.user,
            )
        except PermissionError as exc:
            messagebox.showerror("Permission Denied", str(exc), parent=self.winfo_toplevel())
            return
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Archive Failed", str(exc), parent=self.winfo_toplevel())
            return
        except Exception as exc:
            messagebox.showerror(
                "Archive Failed",
                f"The Client Master record could not be archived.\n\nDetails: {exc}",
                parent=self.winfo_toplevel(),
            )
            return
        finally:
            self._set_busy(False)

        self._clear_selection()
        self.load_clients(preserve_selection=False)
        messagebox.showinfo(
            "Client Archived",
            f'Client "{self._get_client_label(archived)}" was archived successfully.',
            parent=self.winfo_toplevel(),
        )

    def _handle_restore(self) -> None:
        if not self.can_restore:
            self._show_permission_denied("restore Client Master records")
            return

        client = self.selected_client or self.grid_view.get_selected_row()
        if not client:
            messagebox.showwarning(
                "Select a Client",
                "Select an inactive Client Master record before clicking Restore.",
                parent=self.winfo_toplevel(),
            )
            return

        if bool(client.get("is_active")):
            messagebox.showwarning(
                "Already Active",
                "The selected Client Master record is already active.",
                parent=self.winfo_toplevel(),
            )
            return

        client_id = client.get("id")
        if not client_id:
            messagebox.showerror(
                "Restore Failed",
                "The selected Client Master record has no valid ID.",
                parent=self.winfo_toplevel(),
            )
            return

        confirmed = messagebox.askyesno(
            "Restore Client",
            (
                f'Restore client "{self._get_client_label(client)}"?\n\n'
                "The client will become available in the Active list again."
            ),
            parent=self.winfo_toplevel(),
        )
        if not confirmed:
            return

        self._set_busy(True)
        try:
            restored = ClientService.restore_client(
                client_id,
                current_user=self.user,
            )
        except PermissionError as exc:
            messagebox.showerror("Permission Denied", str(exc), parent=self.winfo_toplevel())
            return
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Restore Failed", str(exc), parent=self.winfo_toplevel())
            return
        except Exception as exc:
            messagebox.showerror(
                "Restore Failed",
                f"The Client Master record could not be restored.\n\nDetails: {exc}",
                parent=self.winfo_toplevel(),
            )
            return
        finally:
            self._set_busy(False)

        self._clear_selection()
        self.load_clients(preserve_selection=False)
        messagebox.showinfo(
            "Client Restored",
            f'Client "{self._get_client_label(restored)}" was restored successfully.',
            parent=self.winfo_toplevel(),
        )

    def load_clients(self, *, preserve_selection: bool = True) -> None:
        if self._is_loading:
            return

        if not self.can_view:
            self.clients = []
            self._clear_selection()
            self.grid_view.set_empty_message(
                "You do not have permission to view Client Master records."
            )
            self.grid_view.set_rows([], preserve_selection=False)
            return

        self._is_loading = True
        try:
            search_text = self.toolbar.get_search_text()
            status_filter = self.toolbar.get_status_filter()

            if search_text:
                clients = ClientService.search(
                    search_text=search_text,
                    status_filter=status_filter,
                    current_user=self.user,
                )
            else:
                clients = ClientService.get_all(
                    status_filter=status_filter,
                    current_user=self.user,
                )

            self.clients = [self._prepare_client_row(client) for client in clients]
            self.grid_view.set_empty_message(
                self._build_empty_message(
                    search_text=search_text,
                    status_filter=status_filter,
                )
            )
            self.grid_view.set_rows(
                self.clients,
                preserve_selection=preserve_selection,
            )

            self.selected_client = self.grid_view.get_selected_row()
            self.toolbar.set_selected_record(self.selected_client)

        except PermissionError as exc:
            self._handle_load_error(title="Permission Denied", message=str(exc))
        except (ValueError, RuntimeError) as exc:
            self._handle_load_error(title="Unable to Load Clients", message=str(exc))
        except Exception as exc:
            self._handle_load_error(
                title="Unable to Load Clients",
                message=(
                    "The Client Master records could not be loaded.\n\n"
                    f"Details: {exc}"
                ),
            )
        finally:
            self._is_loading = False

    def _handle_load_error(self, *, title: str, message: str) -> None:
        self.clients = []
        self._clear_selection()
        self.grid_view.set_empty_message(
            "Client Master records could not be loaded."
        )
        self.grid_view.set_rows([], preserve_selection=False)
        messagebox.showerror(title, message, parent=self.winfo_toplevel())

    @staticmethod
    def _prepare_client_row(client: dict[str, Any]) -> dict[str, Any]:
        row = dict(client)
        for key in (
            "client_code",
            "client_name",
            "contact_person",
            "phone",
            "email",
        ):
            if row.get(key) is None:
                row[key] = ""
        row["status_display"] = (
            "Active" if bool(row.get("is_active")) else "Inactive"
        )
        return row

    @staticmethod
    def _build_empty_message(*, search_text: str, status_filter: str) -> str:
        if search_text:
            return f'No {status_filter.lower()} clients match "{search_text}".'
        if status_filter == MasterDataToolbar.FILTER_INACTIVE:
            return "No inactive Client Master records found."
        if status_filter == MasterDataToolbar.FILTER_ALL:
            return "No Client Master records found."
        return "No active Client Master records found."

    def _clear_selection(self) -> None:
        self.selected_client = None
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

    def _set_busy(self, busy: bool) -> None:
        cursor = "wait" if busy else ""
        try:
            self.winfo_toplevel().configure(cursor=cursor)
            self.update_idletasks()
        except ctk.TclError:
            pass

    def _show_permission_denied(self, action_text: str) -> None:
        messagebox.showerror(
            "Permission Denied",
            f"You do not have permission to {action_text}.",
            parent=self.winfo_toplevel(),
        )

    @staticmethod
    def _get_client_label(client: dict[str, Any]) -> str:
        client_code = str(client.get("client_code") or "").strip()
        client_name = str(client.get("client_name") or "").strip()
        return " - ".join(
            value for value in (client_code, client_name) if value
        ) or "Selected Client"

    @staticmethod
    def _format_status(_value: Any, row: dict[str, Any]) -> str:
        return "Active" if bool(row.get("is_active")) else "Inactive"