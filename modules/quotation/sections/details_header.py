import customtkinter as ctk

from core.theme import JCAPTheme


class DetailsHeader(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        title,
        subtitle="Material Request",
        on_open_folder=None,
        on_assign=None,
        on_archive=None,
        on_restore=None,
        on_edit=None,
        on_back=None,
    ):
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=14,
        )

        self.title = title
        self.subtitle = subtitle

        self.on_open_folder = on_open_folder
        self.on_assign = on_assign
        self.on_archive = on_archive
        self.on_restore = on_restore
        self.on_edit = on_edit
        self.on_back = on_back

        self.assignment_button = None
        self.edit_button = None
        self.archive_button = None
        self.restore_button = None

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        title_block.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=14,
        )

        ctk.CTkLabel(
            title_block,
            text=self.title,
            font=("Segoe UI", 26, "bold"),
            text_color="#0A2E63",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=self.subtitle,
            font=("Segoe UI", 13),
            text_color="#607D8B",
        ).pack(anchor="w", pady=(2, 0))

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        button_frame.grid(
            row=0,
            column=1,
            sticky="e",
            padx=15,
            pady=14,
        )

        ctk.CTkButton(
            button_frame,
            text="Open Folder",
            width=130,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self.on_open_folder,
        ).pack(side="left", padx=5)

        self.assignment_button = ctk.CTkButton(
            button_frame,
            text="Assign",
            width=110,
            fg_color="#00ACC1",
            hover_color="#00838F",
            command=self.on_assign,
        )
        self.assignment_button.pack(
            side="left",
            padx=5,
        )

        self.archive_button = ctk.CTkButton(
            button_frame,
            text="Archive",
            width=110,
            fg_color="#FB8C00",
            hover_color="#EF6C00",
            command=self.on_archive,
        )
        self.archive_button.pack(
            side="left",
            padx=5,
        )

        self.restore_button = ctk.CTkButton(
            button_frame,
            text="Restore",
            width=110,
            fg_color="#43A047",
            hover_color="#2E7D32",
            command=self.on_restore,
        )

        self.edit_button = ctk.CTkButton(
            button_frame,
            text="Edit",
            width=100,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self.on_edit,
        )
        self.edit_button.pack(
            side="left",
            padx=5,
        )

        ctk.CTkButton(
            button_frame,
            text="Back",
            width=100,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self.on_back,
        ).pack(
            side="left",
            padx=5,
        )

    # ============================================================
    # ASSIGNMENT ACTION STATE
    # ============================================================

    def set_assignment_state(self, assigned=False):
        """
        Update the assignment action for the current record.

        Args:
            assigned:
                False -> button displays Assign.
                True -> button displays Reassign.
        """
        if not self.assignment_button:
            return

        if assigned:
            self.assignment_button.configure(
                text="Reassign",
                fg_color="#8E24AA",
                hover_color="#6A1B9A",
            )
        else:
            self.assignment_button.configure(
                text="Assign",
                fg_color="#00ACC1",
                hover_color="#00838F",
            )

    def set_assignment_enabled(self, enabled=True):
        if self.assignment_button:
            self.assignment_button.configure(
                state="normal" if enabled else "disabled"
            )

    def set_assignment_visible(self, visible=True):
        if not self.assignment_button:
            return

        if visible:
            if not self.assignment_button.winfo_manager():
                self.assignment_button.pack(
                    side="left",
                    padx=5,
                    before=self.archive_button,
                )
        elif self.assignment_button.winfo_manager():
            self.assignment_button.pack_forget()

    # ============================================================
    # EXISTING HEADER ACTION STATE
    # ============================================================

    def set_edit_enabled(self, enabled=True):
        if self.edit_button:
            self.edit_button.configure(
                state="normal" if enabled else "disabled"
            )

    def set_archive_enabled(self, enabled=True):
        if self.archive_button:
            self.archive_button.configure(
                state="normal" if enabled else "disabled"
            )

    def set_record_state(self, state):
        """
        Supported values:
            active
            archived
        """
        if state == "archived":
            if self.archive_button.winfo_manager():
                self.archive_button.pack_forget()

            if self.assignment_button.winfo_manager():
                self.assignment_button.pack_forget()

            if not self.restore_button.winfo_manager():
                self.restore_button.pack(
                    side="left",
                    padx=5,
                    before=self.edit_button,
                )

            self.edit_button.configure(
                state="disabled"
            )

        else:
            if self.restore_button.winfo_manager():
                self.restore_button.pack_forget()

            if not self.assignment_button.winfo_manager():
                self.assignment_button.pack(
                    side="left",
                    padx=5,
                    before=self.archive_button,
                )

            if not self.archive_button.winfo_manager():
                self.archive_button.pack(
                    side="left",
                    padx=5,
                    before=self.edit_button,
                )

            self.edit_button.configure(
                state="normal"
            )