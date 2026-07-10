import customtkinter as ctk


class SummaryCards(ctk.CTkFrame):
    def __init__(self, parent, items=None):
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=14,
        )

        self.items = items or []
        self.build_ui()

    def build_ui(self):
        total_columns = max(len(self.items), 1)

        for column in range(total_columns):
            self.grid_columnconfigure(column, weight=1)

        if not self.items:
            ctk.CTkLabel(
                self,
                text="No summary information available.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).grid(
                row=0,
                column=0,
                padx=20,
                pady=20,
            )
            return

        for index, item in enumerate(self.items):
            label = item.get("label", "")
            value = item.get("value", "")

            card = ctk.CTkFrame(
                self,
                fg_color="#F5F7FA",
                corner_radius=10,
            )
            card.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=10,
                pady=15,
            )

            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 12, "bold"),
                text_color="#607D8B",
            ).pack(pady=(12, 3))

            ctk.CTkLabel(
                card,
                text=str(value or ""),
                font=("Segoe UI", 14, "bold"),
                text_color="#0A2E63",
                wraplength=260,
            ).pack(pady=(0, 12))