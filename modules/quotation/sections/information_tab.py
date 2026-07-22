import customtkinter as ctk


class InformationTab(ctk.CTkScrollableFrame):
    """
    Scrollable information panel for Material Request details.

    The fields are displayed in a responsive two-column layout.
    """

    def __init__(
        self,
        parent,
        fields=None,
    ):
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=0,
            scrollbar_button_color="#90A4AE",
            scrollbar_button_hover_color="#607D8B",
        )

        self.fields = fields or []

        self.grid_columnconfigure(
            0,
            weight=1,
            uniform="information_column",
        )

        self.grid_columnconfigure(
            1,
            weight=1,
            uniform="information_column",
        )

        self.build_fields()

    def build_fields(self):
        """
        Create all information cards.
        """

        for widget in self.winfo_children():
            widget.destroy()

        for index, field in enumerate(self.fields):
            row = index // 2
            column = index % 2

            self.add_information_field(
                label=field.get(
                    "label",
                    "",
                ),
                value=field.get(
                    "value",
                    "",
                ),
                row=row,
                column=column,
            )

        # Adds a small space below the final row so the last
        # information card is not pressed against the bottom.
        final_row = (
            len(self.fields) + 1
        ) // 2

        self.grid_rowconfigure(
            final_row,
            minsize=10,
        )

    def add_information_field(
        self,
        *,
        label,
        value,
        row,
        column,
    ):
        """
        Add one information card to the panel.
        """

        display_value = (
            str(value)
            if value not in (
                None,
                "",
            )
            else "-"
        )

        field_frame = ctk.CTkFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=10,
        )

        field_frame.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=10,
            pady=8,
        )

        field_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        label_widget = ctk.CTkLabel(
            field_frame,
            text=str(label or ""),
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
            text_color="#607D8B",
            anchor="w",
            justify="left",
        )

        label_widget.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=15,
            pady=(12, 4),
        )

        value_widget = ctk.CTkLabel(
            field_frame,
            text=display_value,
            font=(
                "Segoe UI",
                13,
            ),
            text_color="#111827",
            anchor="w",
            justify="left",
            wraplength=620,
        )

        value_widget.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 14),
        )