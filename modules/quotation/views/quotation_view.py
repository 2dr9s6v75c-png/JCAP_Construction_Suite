import customtkinter as ctk
from modules.quotation.dialogs.new_request_dialog import NewRequestDialog

class QuotationView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="#F5F7FA", corner_radius=0)

        self.user = user
        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Quotation Monitoring",
            font=("Segoe UI", 28, "bold"),
            text_color="#0A2E63"
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        panel = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14
        )
        panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        ctk.CTkLabel(
            panel,
            text="Production Quotation Monitoring Module",
            font=("Segoe UI", 22, "bold"),
            text_color="#0D47A1"
        ).pack(pady=(80, 10))

        ctk.CTkLabel(
            panel,
            text="This module will manage project material requests, supplier quotation monitoring, attachments, status tracking, and multi-user record locking.",
            font=("Segoe UI", 14),
            text_color="#607D8B",
            wraplength=700
        ).pack(pady=10)

        ctk.CTkButton(
            panel,
            text="+ New Material Request",
            width=240,
            height=42,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            font=("Segoe UI", 13, "bold"),
            command=self.open_new_request_dialog
        ).pack(pady=30)
    def open_new_request_dialog(self):
        NewRequestDialog(self, self.user)
    