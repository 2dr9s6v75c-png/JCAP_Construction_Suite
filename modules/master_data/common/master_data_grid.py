from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import customtkinter as ctk

from core.theme import JCAPTheme


class MasterDataGrid(ctk.CTkFrame):
    """
    Reusable scrollable data grid for Master Data modules.

    Column definition format:

        {
            "key": "client_code",
            "title": "Client Code",
            "weight": 1,
            "anchor": "w",
            "formatter": optional_callable,
        }

    Required public operations:

        set_rows(rows)
        get_selected_row()
        clear_selection()
        refresh_rows()
    """

    DEFAULT_ROW_COLOR = "#FFFFFF"
    ALTERNATE_ROW_COLOR = "#F8FAFC"
    SELECTED_ROW_COLOR = "#DCEBFA"
    HOVER_ROW_COLOR = "#EEF5FC"

    def __init__(
        self,
        parent,
        *,
        columns: list[dict[str, Any]],
        id_key: str = "id",
        empty_message: str = "No records found.",
        result_label_singular: str = "record",
        result_label_plural: str = "records",
        on_select: Callable[[dict[str, Any] | None], None] | None = None,
        on_double_click: Callable[[dict[str, Any]], None] | None = None,
        allow_selection: bool = True,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
            **kwargs,
        )

        if not columns:
            raise ValueError(
                "MasterDataGrid requires at least one column."
            )

        self.columns = columns
        self.id_key = id_key
        self.empty_message = empty_message
        self.result_label_singular = result_label_singular
        self.result_label_plural = result_label_plural
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.allow_selection = allow_selection

        self.rows: list[dict[str, Any]] = []
        self.selected_row_id: Any = None
        self._row_widgets: dict[Any, list[ctk.CTkBaseClass]] = {}
        self._row_frames: dict[Any, ctk.CTkFrame] = {}

        self._build_ui()

    # ============================================================
    # UI BUILD
    # ============================================================

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.summary_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.summary_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(16, 8),
        )

        self.result_label = ctk.CTkLabel(
            self.summary_frame,
            text=f"0 {self.result_label_plural}",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )
        self.result_label.pack(side="left")

        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.DARK_BLUE,
            corner_radius=8,
        )
        self.header_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 4),
        )

        self._configure_columns(
            self.header_frame
        )

        for column_index, column in enumerate(self.columns):
            ctk.CTkLabel(
                self.header_frame,
                text=str(column.get("title", "")),
                font=("Segoe UI", 11, "bold"),
                text_color="white",
                anchor=column.get("anchor", "w"),
            ).grid(
                row=0,
                column=column_index,
                sticky="ew",
                padx=8,
                pady=11,
            )

        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.table_scroll.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 12),
        )

        self.table_scroll.grid_columnconfigure(
            0,
            weight=1,
        )

    def _configure_columns(
        self,
        widget,
    ) -> None:
        for column_index, column in enumerate(self.columns):
            widget.grid_columnconfigure(
                column_index,
                weight=int(column.get("weight", 1)),
                uniform=f"master_data_column_{column_index}",
            )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def set_rows(
        self,
        rows: Iterable[dict[str, Any]] | None,
        *,
        preserve_selection: bool = True,
    ) -> None:
        previous_selection = (
            self.selected_row_id
            if preserve_selection
            else None
        )

        self.rows = [
            dict(row)
            for row in (rows or [])
        ]

        valid_ids = {
            row.get(self.id_key)
            for row in self.rows
        }

        if previous_selection not in valid_ids:
            previous_selection = None

        self.selected_row_id = previous_selection

        self.refresh_rows()

    def refresh_rows(self) -> None:
        self._clear_rendered_rows()
        self._update_result_count()

        if not self.rows:
            self._render_empty_state()
            self._notify_selection_changed()
            return

        for row_index, row_data in enumerate(self.rows):
            self._render_row(
                row_index,
                row_data,
            )

        self._notify_selection_changed()

    def get_selected_row(
        self,
    ) -> dict[str, Any] | None:
        if self.selected_row_id is None:
            return None

        for row in self.rows:
            if row.get(self.id_key) == self.selected_row_id:
                return row

        return None

    def clear_selection(self) -> None:
        if self.selected_row_id is None:
            return

        previous_id = self.selected_row_id
        self.selected_row_id = None

        self._apply_row_color(
            previous_id,
            self._base_row_color_for_id(previous_id),
        )
        self._notify_selection_changed()

    def select_row_by_id(
        self,
        row_id: Any,
    ) -> bool:
        if not self.allow_selection:
            return False

        valid_ids = {
            row.get(self.id_key)
            for row in self.rows
        }

        if row_id not in valid_ids:
            return False

        self._select_row(row_id)
        return True

    def set_empty_message(
        self,
        message: str,
    ) -> None:
        self.empty_message = str(message)
        if not self.rows:
            self.refresh_rows()

    # ============================================================
    # RENDERING
    # ============================================================

    def _clear_rendered_rows(self) -> None:
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self._row_widgets.clear()
        self._row_frames.clear()

    def _update_result_count(self) -> None:
        count = len(self.rows)

        noun = (
            self.result_label_singular
            if count == 1
            else self.result_label_plural
        )

        self.result_label.configure(
            text=f"{count} {noun}"
        )

    def _render_empty_state(self) -> None:
        ctk.CTkLabel(
            self.table_scroll,
            text=self.empty_message,
            font=("Segoe UI", 14),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=40,
        )

    def _render_row(
        self,
        row_index: int,
        row_data: dict[str, Any],
    ) -> None:
        row_id = row_data.get(self.id_key)

        if row_id is None:
            row_id = f"__row_{row_index}"

        row_color = (
            self.SELECTED_ROW_COLOR
            if row_id == self.selected_row_id
            else self._base_row_color(row_index)
        )

        row_frame = ctk.CTkFrame(
            self.table_scroll,
            fg_color=row_color,
            corner_radius=0,
        )
        row_frame.grid(
            row=row_index,
            column=0,
            sticky="ew",
            padx=0,
            pady=1,
        )

        self._configure_columns(row_frame)

        row_widgets: list[ctk.CTkBaseClass] = [row_frame]

        for column_index, column in enumerate(self.columns):
            value = row_data.get(column.get("key"))

            formatter = column.get("formatter")
            if callable(formatter):
                value = formatter(
                    value,
                    row_data,
                )

            if value is None:
                value = ""

            label = ctk.CTkLabel(
                row_frame,
                text=str(value),
                font=column.get(
                    "font",
                    ("Segoe UI", 11),
                ),
                text_color=column.get(
                    "text_color",
                    JCAPTheme.TEXT,
                ),
                anchor=column.get("anchor", "w"),
                fg_color=row_color,
            )
            label.grid(
                row=0,
                column=column_index,
                sticky="nsew",
                padx=1,
                pady=1,
                ipadx=8,
                ipady=10,
            )

            row_widgets.append(label)

        self._row_frames[row_id] = row_frame
        self._row_widgets[row_id] = row_widgets

        self._bind_row_events(
            row_id,
            row_data,
            row_widgets,
        )

    # ============================================================
    # EVENTS
    # ============================================================

    def _bind_row_events(
        self,
        row_id: Any,
        row_data: dict[str, Any],
        widgets: list[ctk.CTkBaseClass],
    ) -> None:
        for widget in widgets:
            widget.bind(
                "<Enter>",
                lambda _event, selected_id=row_id: (
                    self._handle_row_enter(selected_id)
                ),
                add="+",
            )

            widget.bind(
                "<Leave>",
                lambda _event, selected_id=row_id: (
                    self._handle_row_leave(selected_id)
                ),
                add="+",
            )

            widget.bind(
                "<Button-1>",
                lambda _event, selected_id=row_id: (
                    self._select_row(selected_id)
                ),
                add="+",
            )

            widget.bind(
                "<Double-Button-1>",
                lambda _event, selected_row=row_data: (
                    self._handle_double_click(selected_row)
                ),
                add="+",
            )

    def _handle_row_enter(
        self,
        row_id: Any,
    ) -> None:
        if row_id == self.selected_row_id:
            return

        self._apply_row_color(
            row_id,
            self.HOVER_ROW_COLOR,
        )

    def _handle_row_leave(
        self,
        row_id: Any,
    ) -> None:
        if row_id == self.selected_row_id:
            return

        self._apply_row_color(
            row_id,
            self._base_row_color_for_id(row_id),
        )

    def _select_row(
        self,
        row_id: Any,
    ) -> None:
        if not self.allow_selection:
            return

        previous_id = self.selected_row_id

        if previous_id == row_id:
            self._notify_selection_changed()
            return

        self.selected_row_id = row_id

        if previous_id is not None:
            self._apply_row_color(
                previous_id,
                self._base_row_color_for_id(previous_id),
            )

        self._apply_row_color(
            row_id,
            self.SELECTED_ROW_COLOR,
        )

        self._notify_selection_changed()

    def _handle_double_click(
        self,
        row_data: dict[str, Any],
    ) -> None:
        row_id = row_data.get(self.id_key)

        if row_id is not None:
            self._select_row(row_id)

        if self.on_double_click:
            self.on_double_click(row_data)

    # ============================================================
    # VISUAL HELPERS
    # ============================================================

    def _apply_row_color(
        self,
        row_id: Any,
        color: str,
    ) -> None:
        for widget in self._row_widgets.get(row_id, []):
            try:
                widget.configure(
                    fg_color=color
                )
            except (AttributeError, ValueError):
                pass

    def _base_row_color_for_id(
        self,
        row_id: Any,
    ) -> str:
        for row_index, row in enumerate(self.rows):
            effective_id = row.get(self.id_key)

            if effective_id is None:
                effective_id = f"__row_{row_index}"

            if effective_id == row_id:
                return self._base_row_color(row_index)

        return self.DEFAULT_ROW_COLOR

    @classmethod
    def _base_row_color(
        cls,
        row_index: int,
    ) -> str:
        return (
            cls.DEFAULT_ROW_COLOR
            if row_index % 2 == 0
            else cls.ALTERNATE_ROW_COLOR
        )

    def _notify_selection_changed(self) -> None:
        if self.on_select:
            self.on_select(
                self.get_selected_row()
            )