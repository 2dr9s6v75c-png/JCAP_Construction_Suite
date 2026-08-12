"""
JCAP Construction Suite
Reusable popup calendar / date-entry component.

Uses only Python tkinter/customtkinter; no tkcalendar dependency is required.
Dates are stored/displayed as YYYY-MM-DD.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
import tkinter as tk

import customtkinter as ctk


class DatePicker(ctk.CTkFrame):
    """Entry field with a reusable popup month calendar."""

    def __init__(
        self,
        parent,
        *,
        variable=None,
        placeholder_text="YYYY-MM-DD",
        height=36,
        command=None,
        allow_clear=True,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
            **kwargs,
        )

        self.variable = variable or ctk.StringVar()
        self.command = command
        self.allow_clear = bool(allow_clear)
        self._popup = None

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.variable,
            placeholder_text=placeholder_text,
            height=height,
        )
        self.entry.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.button = ctk.CTkButton(
            self,
            text="📅",
            width=42,
            height=height,
            fg_color="#1976D2",
            hover_color="#0D47A1",
            command=self.open_calendar,
        )
        self.button.grid(
            row=0,
            column=1,
            padx=(6, 0),
        )

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(
            self._format_value(value)
        )

    def delete(self, first=0, last="end"):
        self.entry.delete(first, last)

    def insert(self, index, value):
        self.entry.insert(index, value)

    def focus_set(self):
        self.entry.focus_set()

    def bind(self, sequence=None, command=None, add=True):
        """
        Bind application callbacks to the internal CTkEntry.

        CustomTkinter reserves its own internal bindings, so application
        callbacks must be added with add=True (or "+") rather than replacing
        those callbacks.
        """
        if sequence is None:
            return None

        if command is None:
            return self.entry.bind(sequence)

        return self.entry.bind(
            sequence,
            command,
            add=True,
        )

    def configure(self, **kwargs):
        state = kwargs.pop("state", None)
        if state is not None and hasattr(self, "entry"):
            self.entry.configure(state=state)
            self.button.configure(
                state=(
                    "disabled"
                    if state == "disabled"
                    else "normal"
                )
            )
        return super().configure(**kwargs)

    config = configure

    def open_calendar(self):
        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    self._popup.focus_force()
                    return
            except Exception:
                pass

        selected = self._parse_value(
            self.variable.get()
        ) or date.today()

        self._popup = _CalendarPopup(
            self,
            selected_date=selected,
            on_select=self._select_date,
            on_clear=(
                self._clear_date
                if self.allow_clear
                else None
            ),
        )

    def _select_date(self, selected_date):
        self.variable.set(
            selected_date.isoformat()
        )
        self._close_popup()

        if self.command:
            self.command(
                selected_date.isoformat()
            )

    def _clear_date(self):
        self.variable.set("")
        self._close_popup()

        if self.command:
            self.command("")

    def _close_popup(self):
        popup = self._popup
        self._popup = None

        if popup is not None:
            try:
                popup.destroy()
            except Exception:
                pass

    @staticmethod
    def _parse_value(value):
        text = str(value or "").strip()
        if not text:
            return None

        try:
            return datetime.strptime(
                text,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            return None

    @staticmethod
    def _format_value(value):
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return value.isoformat()
        return str(value or "").strip()


class _CalendarPopup(ctk.CTkToplevel):
    WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

    def __init__(
        self,
        owner,
        *,
        selected_date,
        on_select,
        on_clear=None,
    ):
        super().__init__(owner)

        self.owner = owner
        self.selected_date = selected_date
        self.on_select = on_select
        self.on_clear = on_clear
        self.display_year = selected_date.year
        self.display_month = selected_date.month

        self.title("Select Date")
        self.resizable(False, False)
        self.transient(owner.winfo_toplevel())

        self.protocol(
            "WM_DELETE_WINDOW",
            self.destroy,
        )

        self._build_ui()
        self._position_near_owner()

        self.after(10, self.lift)
        self.after(20, self.focus_force)

    def _build_ui(self):
        shell = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
        )
        shell.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        nav = ctk.CTkFrame(
            shell,
            fg_color="transparent",
        )
        nav.grid(
            row=0,
            column=0,
            columnspan=7,
            sticky="ew",
            padx=8,
            pady=(8, 6),
        )
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav,
            text="‹",
            width=36,
            height=30,
            command=self._previous_month,
        ).grid(row=0, column=0)

        self.month_label = ctk.CTkLabel(
            nav,
            text="",
            font=ctk.CTkFont(
                size=15,
                weight="bold",
            ),
            text_color="#0A2E63",
        )
        self.month_label.grid(
            row=0,
            column=1,
            padx=12,
        )

        ctk.CTkButton(
            nav,
            text="›",
            width=36,
            height=30,
            command=self._next_month,
        ).grid(row=0, column=2)

        for column, weekday in enumerate(self.WEEKDAYS):
            ctk.CTkLabel(
                shell,
                text=weekday,
                width=38,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold",
                ),
                text_color="#607D8B",
            ).grid(
                row=1,
                column=column,
                padx=2,
                pady=(2, 4),
            )

        self.days_frame = ctk.CTkFrame(
            shell,
            fg_color="transparent",
        )
        self.days_frame.grid(
            row=2,
            column=0,
            columnspan=7,
            padx=6,
            pady=2,
        )

        footer = ctk.CTkFrame(
            shell,
            fg_color="transparent",
        )
        footer.grid(
            row=3,
            column=0,
            columnspan=7,
            sticky="ew",
            padx=8,
            pady=(6, 8),
        )

        ctk.CTkButton(
            footer,
            text="Today",
            width=82,
            height=30,
            fg_color="#E3F2FD",
            hover_color="#BBDEFB",
            text_color="#0D47A1",
            command=lambda: self.on_select(
                date.today()
            ),
        ).pack(side="left")

        if self.on_clear is not None:
            ctk.CTkButton(
                footer,
                text="Clear",
                width=72,
                height=30,
                fg_color="#ECEFF1",
                hover_color="#CFD8DC",
                text_color="#455A64",
                command=self.on_clear,
            ).pack(side="right")

        self._render_month()

    def _render_month(self):
        self.month_label.configure(
            text=(
                f"{calendar.month_name[self.display_month]} "
                f"{self.display_year}"
            )
        )

        for widget in self.days_frame.winfo_children():
            widget.destroy()

        month_rows = calendar.Calendar(
            firstweekday=calendar.MONDAY
        ).monthdayscalendar(
            self.display_year,
            self.display_month,
        )

        today = date.today()

        for row_index, week in enumerate(month_rows):
            for column_index, day_number in enumerate(week):
                if day_number == 0:
                    ctk.CTkLabel(
                        self.days_frame,
                        text="",
                        width=38,
                        height=34,
                    ).grid(
                        row=row_index,
                        column=column_index,
                        padx=2,
                        pady=2,
                    )
                    continue

                current = date(
                    self.display_year,
                    self.display_month,
                    day_number,
                )

                is_selected = (
                    current == self.selected_date
                )
                is_today = (
                    current == today
                )

                if is_selected:
                    fg = "#1976D2"
                    hover = "#0D47A1"
                    text_color = "#FFFFFF"
                elif is_today:
                    fg = "#E3F2FD"
                    hover = "#BBDEFB"
                    text_color = "#0D47A1"
                else:
                    fg = "transparent"
                    hover = "#ECEFF1"
                    text_color = "#111827"

                ctk.CTkButton(
                    self.days_frame,
                    text=str(day_number),
                    width=38,
                    height=34,
                    corner_radius=8,
                    fg_color=fg,
                    hover_color=hover,
                    text_color=text_color,
                    command=lambda value=current: (
                        self.on_select(value)
                    ),
                ).grid(
                    row=row_index,
                    column=column_index,
                    padx=2,
                    pady=2,
                )

    def _previous_month(self):
        if self.display_month == 1:
            self.display_month = 12
            self.display_year -= 1
        else:
            self.display_month -= 1
        self._render_month()

    def _next_month(self):
        if self.display_month == 12:
            self.display_month = 1
            self.display_year += 1
        else:
            self.display_month += 1
        self._render_month()

    def _position_near_owner(self):
        self.update_idletasks()

        try:
            x = self.owner.winfo_rootx()
            y = (
                self.owner.winfo_rooty()
                + self.owner.winfo_height()
                + 4
            )
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass