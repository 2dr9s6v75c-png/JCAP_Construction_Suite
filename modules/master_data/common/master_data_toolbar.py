from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from core.theme import JCAPTheme


class MasterDataToolbar(ctk.CTkFrame):
    """
    Reusable toolbar for Master Data modules.

    Provides:
    - Live search
    - Active / Inactive / All status filter
    - New
    - Edit
    - Archive
    - Restore
    - Refresh

    Button availability is controlled by:
    - Permission flags passed by the module
    - Whether a row is selected
    - Whether the selected row is active
    """

    FILTER_ALL = "All"
    FILTER_ACTIVE = "Active"
    FILTER_INACTIVE = "Inactive"

    def __init__(
        self,
        parent,
        *,
        search_placeholder: str = "Search records...",
        on_search_change: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
        on_new: Callable[[], None] | None = None,
        on_edit: Callable[[], None] | None = None,
        on_archive: Callable[[], None] | None = None,
        on_restore: Callable[[], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        can_create: bool = False,
        can_edit: bool = False,
        can_archive: bool = False,
        can_restore: bool = False,
        initial_status: str = FILTER_ACTIVE,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
            **kwargs,
        )

        self.on_search_change = on_search_change
        self.on_status_change = on_status_change
        self.on_new = on_new
        self.on_edit = on_edit
        self.on_archive = on_archive
        self.on_restore = on_restore
        self.on_refresh = on_refresh

        self.permission_create = bool(can_create)
        self.permission_edit = bool(can_edit)
        self.permission_archive = bool(can_archive)
        self.permission_restore = bool(can_restore)

        self.selected_record: dict[str, Any] | None = None

        self.search_var = ctk.StringVar()
        self.status_var = ctk.StringVar(
            value=self._normalize_status(initial_status)
        )

        self._build_ui(search_placeholder)
        self._update_action_states()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(
        self,
        search_placeholder: str,
    ) -> None:
        self.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text=search_placeholder,
            height=38,
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(16, 8),
            pady=14,
        )

        self.search_var.trace_add(
            "write",
            self._handle_search_change,
        )

        self.status_menu = ctk.CTkOptionMenu(
            self,
            variable=self.status_var,
            values=[
                self.FILTER_ALL,
                self.FILTER_ACTIVE,
                self.FILTER_INACTIVE,
            ],
            width=130,
            command=self._handle_status_change,
        )
        self.status_menu.grid(
            row=0,
            column=1,
            padx=8,
            pady=14,
        )

        self.new_button = ctk.CTkButton(
            self,
            text="New",
            width=85,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self._handle_new,
        )
        self.new_button.grid(
            row=0,
            column=2,
            padx=4,
            pady=14,
        )

        self.edit_button = ctk.CTkButton(
            self,
            text="Edit",
            width=85,
            fg_color=JCAPTheme.EDIT,
            hover_color=JCAPTheme.EDIT_HOVER,
            command=self._handle_edit,
        )
        self.edit_button.grid(
            row=0,
            column=3,
            padx=4,
            pady=14,
        )

        self.archive_button = ctk.CTkButton(
            self,
            text="Archive",
            width=90,
            fg_color=JCAPTheme.ARCHIVE,
            hover_color=JCAPTheme.ARCHIVE_HOVER,
            command=self._handle_archive,
        )
        self.archive_button.grid(
            row=0,
            column=4,
            padx=4,
            pady=14,
        )

        self.restore_button = ctk.CTkButton(
            self,
            text="Restore",
            width=90,
            fg_color=JCAPTheme.GREEN,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self._handle_restore,
        )
        self.restore_button.grid(
            row=0,
            column=5,
            padx=4,
            pady=14,
        )

        self.refresh_button = ctk.CTkButton(
            self,
            text="Refresh",
            width=95,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.PRIMARY_BLUE_HOVER,
            command=self._handle_refresh,
        )
        self.refresh_button.grid(
            row=0,
            column=6,
            padx=(4, 16),
            pady=14,
        )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def set_selected_record(
        self,
        record: dict[str, Any] | None,
    ) -> None:
        self.selected_record = record
        self._update_action_states()

    def clear_selection(self) -> None:
        self.set_selected_record(None)

    def set_permissions(
        self,
        *,
        can_create: bool | None = None,
        can_edit: bool | None = None,
        can_archive: bool | None = None,
        can_restore: bool | None = None,
    ) -> None:
        if can_create is not None:
            self.permission_create = bool(can_create)

        if can_edit is not None:
            self.permission_edit = bool(can_edit)

        if can_archive is not None:
            self.permission_archive = bool(can_archive)

        if can_restore is not None:
            self.permission_restore = bool(can_restore)

        self._update_action_states()

    def get_search_text(self) -> str:
        return self.search_var.get().strip()

    def set_search_text(
        self,
        value: str,
    ) -> None:
        self.search_var.set(str(value or ""))

    def clear_search(self) -> None:
        self.search_var.set("")

    def get_status_filter(self) -> str:
        return self._normalize_status(
            self.status_var.get()
        )

    def set_status_filter(
        self,
        status: str,
        *,
        notify: bool = True,
    ) -> None:
        normalized = self._normalize_status(status)
        self.status_var.set(normalized)

        if notify and self.on_status_change:
            self.on_status_change(normalized)

    def focus_search(self) -> None:
        self.search_entry.focus_set()

    # ============================================================
    # STATE MANAGEMENT
    # ============================================================

    def _update_action_states(self) -> None:
        has_selection = self.selected_record is not None

        selected_is_active = bool(
            self.selected_record.get("is_active", True)
        ) if has_selection else False

        self._set_button_state(
            self.new_button,
            self.permission_create,
        )

        self._set_button_state(
            self.edit_button,
            self.permission_edit and has_selection,
        )

        self._set_button_state(
            self.archive_button,
            (
                self.permission_archive
                and has_selection
                and selected_is_active
            ),
        )

        self._set_button_state(
            self.restore_button,
            (
                self.permission_restore
                and has_selection
                and not selected_is_active
            ),
        )

        self._set_button_state(
            self.refresh_button,
            True,
        )

    @staticmethod
    def _set_button_state(
        button: ctk.CTkButton,
        enabled: bool,
    ) -> None:
        button.configure(
            state="normal" if enabled else "disabled"
        )

    # ============================================================
    # EVENT HANDLERS
    # ============================================================

    def _handle_search_change(
        self,
        *_args,
    ) -> None:
        if self.on_search_change:
            self.on_search_change(
                self.get_search_text()
            )

    def _handle_status_change(
        self,
        value: str,
    ) -> None:
        normalized = self._normalize_status(value)

        if normalized != value:
            self.status_var.set(normalized)

        self.clear_selection()

        if self.on_status_change:
            self.on_status_change(normalized)

    def _handle_new(self) -> None:
        if self.permission_create and self.on_new:
            self.on_new()

    def _handle_edit(self) -> None:
        if (
            self.permission_edit
            and self.selected_record
            and self.on_edit
        ):
            self.on_edit()

    def _handle_archive(self) -> None:
        if not self.selected_record:
            return

        if (
            self.permission_archive
            and bool(
                self.selected_record.get(
                    "is_active",
                    True,
                )
            )
            and self.on_archive
        ):
            self.on_archive()

    def _handle_restore(self) -> None:
        if not self.selected_record:
            return

        if (
            self.permission_restore
            and not bool(
                self.selected_record.get(
                    "is_active",
                    True,
                )
            )
            and self.on_restore
        ):
            self.on_restore()

    def _handle_refresh(self) -> None:
        if self.on_refresh:
            self.on_refresh()

    # ============================================================
    # HELPERS
    # ============================================================

    @classmethod
    def _normalize_status(
        cls,
        value: str,
    ) -> str:
        normalized = str(
            value or cls.FILTER_ACTIVE
        ).strip().lower()

        if normalized in {
            "all",
            "all records",
            "all accounts",
        }:
            return cls.FILTER_ALL

        if normalized in {
            "inactive",
            "disabled",
            "archived",
        }:
            return cls.FILTER_INACTIVE

        return cls.FILTER_ACTIVE