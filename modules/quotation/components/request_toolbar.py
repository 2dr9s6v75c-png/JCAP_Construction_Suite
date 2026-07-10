import customtkinter as ctk


class RequestToolbar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        mode="create",
        mr_number=None,
        on_save=None,
        on_edit=None,
        on_back=None,
        on_open_folder=None,
    ):
        super().__init__(parent, fg_color="#FFFFFF", corner_radius=14)

        self.mode = mode
        self.mr_number = mr_number
        self.on_save = on_save
        self.on_edit = on_edit
        self.on_back = on_back
        self.on_open_folder = on_open_folder

        self.build_ui()

    def build_ui(self):
        title_block = ctk.CTkFrame(self, fg_color="transparent")
        title_block.pack(
            side="left",
            fill="x",
            expand=True,
            padx=20,
            pady=14,
        )

        title_text = "New Material Request"
        subtitle_text = "Create a new material request for supplier quotation processing."

        if self.mode == "view":
            title_text = self.mr_number or "Material Request"
            subtitle_text = "View material request details and attachments."

        elif self.mode == "edit":
            title_text = f"Edit {self.mr_number}" if self.mr_number else "Edit Material Request"
            subtitle_text = "Update material request information and attachments."

        ctk.CTkLabel(
            title_block,
            text=title_text,
            font=("Segoe UI", 24, "bold"),
            text_color="#0A2E63",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=subtitle_text,
            font=("Segoe UI", 13),
            text_color="#607D8B",
        ).pack(anchor="w", pady=(2, 0))

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(side="right", padx=10, pady=14)

        if self.mode == "create":
            ctk.CTkButton(
                button_frame,
                text="Back",
                width=100,
                fg_color="#607D8B",
                hover_color="#455A64",
                command=self.on_back,
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                button_frame,
                text="Save",
                width=120,
                fg_color="#0D47A1",
                hover_color="#0A2E63",
                command=self.on_save,
            ).pack(side="left", padx=5)

        elif self.mode == "view":
            ctk.CTkButton(
                button_frame,
                text="Back",
                width=100,
                fg_color="#607D8B",
                hover_color="#455A64",
                command=self.on_back,
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                button_frame,
                text="Open Folder",
                width=130,
                fg_color="#607D8B",
                hover_color="#455A64",
                command=self.on_open_folder,
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                button_frame,
                text="Edit",
                width=100,
                fg_color="#0D47A1",
                hover_color="#0A2E63",
                command=self.on_edit,
            ).pack(side="left", padx=5)

        elif self.mode == "edit":
            ctk.CTkButton(
                button_frame,
                text="Back",
                width=100,
                fg_color="#607D8B",
                hover_color="#455A64",
                command=self.on_back,
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                button_frame,
                text="Save Changes",
                width=140,
                fg_color="#0D47A1",
                hover_color="#0A2E63",
                command=self.on_save,
            ).pack(side="left", padx=5)