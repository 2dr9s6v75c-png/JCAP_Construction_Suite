from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from core.theme import JCAPTheme


class MasterFormBase(ctk.CTkToplevel):
    """
    Reusable modal form base for Master Data dialogs.

    Subclasses should:
    - Override build_form_fields()
    - Override collect_form_data()
    - Optionally override validate_form_data()
    - Pass an on_save callback that accepts the cleaned form data

    The base class standardizes:
    - Modal dialog behavior
    - Header and description
    - Validation message area
    - Save and Cancel buttons
    - Enter / Escape keyboard shortcuts
    - Centering over the parent window
    """

    def __init__(
        self,
        parent,
        *,
        title: str,
        subtitle: str = "",
        save_text: str = "Save",
        cancel_text: str = "Cancel",
        width: int = 620,
        height: int = 640,
        on_save: Callable[[dict[str, Any]], Any] | None = None,
        on_cancel: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.parent = parent
        self.dialog_title = title
        self.dialog_subtitle = subtitle
        self.save_text = save_text
        self.cancel_text = cancel_text
        self.dialog_width = width
        self.dialog_height = height
        self.on_save = on_save
        self.on_cancel = on_cancel

        self._is_saving = False

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.configure(fg_color=JCAPTheme.BACKGROUND)

        self.protocol("WM_DELETE_WINDOW", self.handle_cancel)

        self._build_dialog()
        self._configure_modal_behavior()

    # ============================================================
    # UI BUILD
    # ============================================================

    def _build_dialog(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()

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

        ctk.CTkLabel(
            header,
            text=self.dialog_title,
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(16, 4 if self.dialog_subtitle else 16),
        )

        if self.dialog_subtitle:
            ctk.CTkLabel(
                header,
                text=self.dialog_subtitle,
                font=("Segoe UI", 12),
                text_color=JCAPTheme.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=max(self.dialog_width - 80, 300),
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                padx=20,
                pady=(0, 16),
            )

    def _build_body(self) -> None:
        body_card = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        body_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=10,
        )
        body_card.grid_columnconfigure(0, weight=1)
        body_card.grid_rowconfigure(0, weight=1)

        self.form_scroll = ctk.CTkScrollableFrame(
            body_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self.form_scroll.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(16, 8),
        )
        self.form_scroll.grid_columnconfigure(0, weight=1)

        self.form_container = ctk.CTkFrame(
            self.form_scroll,
            fg_color="transparent",
        )
        self.form_container.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.form_container.grid_columnconfigure(0, weight=1)

        self.build_form_fields(self.form_container)

        self.validation_label = ctk.CTkLabel(
            body_card,
            text="",
            font=("Segoe UI", 11),
            text_color=JCAPTheme.RED,
            anchor="w",
            justify="left",
            wraplength=max(self.dialog_width - 90, 300),
        )
        self.validation_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 14),
        )

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(10, 20),
        )
        footer.grid_columnconfigure(0, weight=1)

        self.cancel_button = ctk.CTkButton(
            footer,
            text=self.cancel_text,
            width=110,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self.handle_cancel,
        )
        self.cancel_button.grid(
            row=0,
            column=1,
            padx=(8, 4),
            pady=14,
        )

        self.save_button = ctk.CTkButton(
            footer,
            text=self.save_text,
            width=120,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.handle_save,
        )
        self.save_button.grid(
            row=0,
            column=2,
            padx=(4, 16),
            pady=14,
        )

    # ============================================================
    # SUBCLASS HOOKS
    # ============================================================

    def build_form_fields(
        self,
        container: ctk.CTkFrame,
    ) -> None:
        """
        Override this method and add form controls to container.
        """
        raise NotImplementedError(
            "Subclasses must implement build_form_fields()."
        )

    def collect_form_data(
        self,
    ) -> dict[str, Any]:
        """
        Override this method and return the current form values.
        """
        raise NotImplementedError(
            "Subclasses must implement collect_form_data()."
        )

    def validate_form_data(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Optional local UI validation hook.

        Return cleaned data or raise ValueError.
        Service-layer validation should still remain authoritative.
        """
        return data

    def on_save_success(
        self,
        _result: Any,
    ) -> None:
        """
        Called after the save callback succeeds.
        Subclasses may override this to keep the dialog open.
        """
        self.destroy()

    # ============================================================
    # FORM HELPERS
    # ============================================================

    def add_field_label(
        self,
        parent,
        *,
        row: int,
        text: str,
        required: bool = False,
        column: int = 0,
        columnspan: int = 1,
        padx: tuple[int, int] = (0, 0),
        pady: tuple[int, int] = (6, 4),
    ) -> ctk.CTkLabel:
        label_text = f"{text} *" if required else text

        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
            anchor="w",
        )
        label.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=padx,
            pady=pady,
        )

        return label

    def add_entry(
        self,
        parent,
        *,
        row: int,
        variable: ctk.StringVar | None = None,
        placeholder_text: str = "",
        column: int = 0,
        columnspan: int = 1,
        padx: tuple[int, int] = (0, 0),
        pady: tuple[int, int] = (0, 10),
        show: str | None = None,
    ) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder_text,
            height=38,
            show=show,
        )
        entry.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=padx,
            pady=pady,
        )

        return entry

    def add_textbox(
        self,
        parent,
        *,
        row: int,
        height: int = 90,
        column: int = 0,
        columnspan: int = 1,
        padx: tuple[int, int] = (0, 0),
        pady: tuple[int, int] = (0, 10),
    ) -> ctk.CTkTextbox:
        textbox = ctk.CTkTextbox(
            parent,
            height=height,
            border_width=1,
            border_color=JCAPTheme.BORDER,
            fg_color=JCAPTheme.CARD,
            text_color=JCAPTheme.TEXT,
        )
        textbox.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=padx,
            pady=pady,
        )

        return textbox

    @staticmethod
    def get_textbox_value(
        textbox: ctk.CTkTextbox,
    ) -> str:
        return textbox.get("1.0", "end").strip()

    @staticmethod
    def set_textbox_value(
        textbox: ctk.CTkTextbox,
        value: Any,
    ) -> None:
        textbox.delete("1.0", "end")
        if value is not None:
            textbox.insert("1.0", str(value))

    # ============================================================
    # VALIDATION MESSAGE
    # ============================================================

    def show_validation_error(
        self,
        message: str,
    ) -> None:
        self.validation_label.configure(
            text=str(message or "")
        )

    def clear_validation_error(self) -> None:
        self.validation_label.configure(text="")

    # ============================================================
    # SAVE / CANCEL
    # ============================================================

    def handle_save(self) -> None:
        if self._is_saving:
            return

        self.clear_validation_error()

        try:
            data = self.collect_form_data()
            data = self.validate_form_data(data)

            self._set_saving_state(True)

            result = (
                self.on_save(data)
                if self.on_save
                else data
            )

            self.on_save_success(result)

        except (ValueError, PermissionError) as exc:
            self.show_validation_error(str(exc))

        except Exception as exc:
            self.show_validation_error(
                f"Unable to save the record: {exc}"
            )

        finally:
            if self.winfo_exists():
                self._set_saving_state(False)

    def handle_cancel(self) -> None:
        if self._is_saving:
            return

        if self.on_cancel:
            self.on_cancel()

        self.destroy()

    def _set_saving_state(
        self,
        is_saving: bool,
    ) -> None:
        self._is_saving = is_saving

        self.save_button.configure(
            state="disabled" if is_saving else "normal",
            text="Saving..." if is_saving else self.save_text,
        )
        self.cancel_button.configure(
            state="disabled" if is_saving else "normal"
        )

    # ============================================================
    # MODAL / WINDOW BEHAVIOR
    # ============================================================

    def _configure_modal_behavior(self) -> None:
        self.transient(self.parent)
        self.grab_set()

        self.bind("<Escape>", self._handle_escape)
        self.bind("<Return>", self._handle_enter)

        self.after(20, self._center_over_parent)
        self.after(50, self._focus_first_input)

    def _handle_escape(
        self,
        _event=None,
    ) -> str:
        self.handle_cancel()
        return "break"

    def _handle_enter(
        self,
        event=None,
    ) -> str | None:
        focused_widget = self.focus_get()

        if isinstance(focused_widget, ctk.CTkTextbox):
            return None

        self.handle_save()
        return "break"

    def _focus_first_input(self) -> None:
        for widget in self._walk_widgets(self.form_container):
            if isinstance(
                widget,
                (
                    ctk.CTkEntry,
                    ctk.CTkOptionMenu,
                    ctk.CTkComboBox,
                    ctk.CTkTextbox,
                ),
            ):
                widget.focus_set()
                break

    def _center_over_parent(self) -> None:
        self.update_idletasks()

        width = max(
            self.winfo_width(),
            self.dialog_width,
        )
        height = max(
            self.winfo_height(),
            self.dialog_height,
        )

        try:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            x = parent_x + max((parent_width - width) // 2, 0)
            y = parent_y + max((parent_height - height) // 2, 0)
        except Exception:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            x = max((screen_width - width) // 2, 0)
            y = max((screen_height - height) // 2, 0)

        self.geometry(f"{width}x{height}+{x}+{y}")

    @classmethod
    def _walk_widgets(
        cls,
        parent,
    ):
        for child in parent.winfo_children():
            yield child
            yield from cls._walk_widgets(child)