import customtkinter as ctk

from modules.quotation.components.attachment_panel import AttachmentPanel


class AttachmentsTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        attachments=None,
        on_open=None,
        on_show_folder=None,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.attachments = attachments or []
        self.on_open = on_open
        self.on_show_folder = on_show_folder

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        self.panel = AttachmentPanel(
            self,
            attachments=self.attachments,
            on_open=self.on_open,
            on_show_folder=self.on_show_folder,
        )

        self.panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )