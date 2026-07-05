import customtkinter as ctk


class AttachmentPanel(ctk.CTkFrame):
    def __init__(self, parent, attachments=None, on_open=None, on_show_folder=None):
        super().__init__(parent, fg_color="#FFFFFF", corner_radius=14)

        self.attachments = attachments or []
        self.on_open = on_open
        self.on_show_folder = on_show_folder

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkLabel(
            self,
            text=(
                    f"Attachments "
                    f"({len(self.attachments)} files • {self.format_total_size()})"
            ),
            font=("Segoe UI", 18, "bold"),
            text_color="#0A2E63",
)
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        if not self.attachments:
            ctk.CTkLabel(
                self,
                text="No attachments found.",
                font=("Segoe UI", 14),
                text_color="#607D8B",
            ).grid(row=1, column=0, pady=40)
            return

        for index, attachment in enumerate(self.attachments, start=1):
            self.create_attachment_row(index, attachment)

    def create_attachment_row(self, row_index, attachment):
        row = ctk.CTkFrame(self, fg_color="#F5F7FA", corner_radius=10)
        row.grid(row=row_index, column=0, sticky="ew", padx=15, pady=6)
        row.grid_columnconfigure(1, weight=1)

        icon = self.get_file_icon(attachment.get("file_extension"))

        ctk.CTkLabel(
            row,
            text=icon,
            font=("Segoe UI", 22),
            text_color="#0D47A1",
        ).grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=12)

        ctk.CTkLabel(
            row,
            text=attachment.get(
                "original_filename",
                attachment.get("stored_filename", ""),
            ),
            font=("Segoe UI", 13, "bold"),
            text_color="#111827",
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(10, 2))

        details = (
            f"{self.format_extension(attachment.get('file_extension'))} • "
            f"{self.format_file_size(attachment.get('file_size'))} • "
            f"Uploaded {self.format_datetime(attachment.get('uploaded_at'))}"
        )

        ctk.CTkLabel(
            row,
            text=details,
            font=("Segoe UI", 12),
            text_color="#607D8B",
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        ctk.CTkButton(
            row,
            text="Open",
            width=80,
            height=30,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=lambda a=attachment: self.on_open(a) if self.on_open else None,
        ).grid(row=0, column=2, rowspan=2, padx=5)

        ctk.CTkButton(
            row,
            text="Show Folder",
            width=110,
            height=30,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=lambda a=attachment: self.on_show_folder(a) if self.on_show_folder else None,
        ).grid(row=0, column=3, rowspan=2, padx=(5, 15))
    def get_total_size(self):
        return sum(
        int(attachment.get("file_size") or 0)
        for attachment in self.attachments
    )

    def format_total_size(self):
        return self.format_file_size(self.get_total_size())        
    
    def get_file_icon(self, extension):
        ext = (extension or "").lower()

        if ext == "pdf":
            return "📄"
        if ext in ["xlsx", "xls", "csv"]:
            return "📊"
        if ext in ["doc", "docx"]:
            return "📝"
        if ext in ["jpg", "jpeg", "png", "bmp"]:
            return "🖼"
        if ext in ["dwg", "dxf"]:
            return "📐"

        return "📎"

    def format_extension(self, extension):
        return (extension or "file").upper()

    def format_file_size(self, size):
        if not size:
            return "0 KB"

        size = int(size)

        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"

        return f"{size / (1024 * 1024):.1f} MB"

    def format_datetime(self, value):
        if not value:
            return ""

        try:
            return value.strftime("%d %b %Y %I:%M %p")
        except Exception:
            return str(value)