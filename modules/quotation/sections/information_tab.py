import customtkinter as ctk


class InformationTab(ctk.CTkFrame):
    def __init__(self, parent, fields=None):
        super().__init__(parent, fg_color="transparent")

        self.fields = fields or []
        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        if not self.fields:
            ctk.CTkLabel(
                self,
                text="Material Request information is unavailable.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).grid(
                row=0,
                column=0,
                columnspan=2,
                pady=40,
            )
            return

        for index, field in enumerate(self.fields):
            row = index // 2
            column = index % 2

            self.add_info_field(
                label=field.get("label", ""),
                value=field.get("value", ""),
                row=row,
                column=column,
            )

    def add_info_field(self, label, value, row, column):
        box = ctk.CTkFrame(
            self,
            fg_color="#F5F7FA",
            corner_radius=10,
        )
        box.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=12,
            pady=8,
        )

        ctk.CTkLabel(
            box,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#607D8B",
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 2),
        )

        ctk.CTkLabel(
            box,
            text=str(value or ""),
            font=("Segoe UI", 13),
            text_color="#111827",
            wraplength=650,
            justify="left",
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 10),
        )