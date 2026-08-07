import customtkinter as ctk

from modules.quotation.components.attachment_panel import AttachmentPanel


class AttachmentsTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        material_request_id,
        material_request,
        current_user,
        is_archived=False,
        attachment_process=None,
        on_data_changed=None,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.material_request_id = material_request_id
        self.material_request = material_request
        self.current_user = current_user
        self.is_archived = bool(is_archived)
        self.attachment_process = attachment_process
        self.on_data_changed = on_data_changed

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        self.panel = AttachmentPanel(
            self,
            material_request_id=self.material_request_id,
            material_request=self.material_request,
            current_user=self.current_user,
            is_archived=self.is_archived,
            attachment_process=self.attachment_process,
            on_data_changed=self.on_data_changed,
        )

        self.panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10,
        )