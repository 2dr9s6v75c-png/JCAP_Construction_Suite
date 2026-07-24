import customtkinter as ctk

from core.theme import JCAPTheme


class MasterDataView(ctk.CTkFrame):
    """
    Landing workspace for foundational JCAP master records.

    This view does not directly edit records. It routes users to the
    Client, Project, and Site Management screens.
    """

    def __init__(
        self,
        parent,
        user,
        *,
        on_clients=None,
        on_projects=None,
        on_sites=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BG_LIGHT,
            corner_radius=0,
        )

        self.user = user
        self.on_clients = on_clients
        self.on_projects = on_projects
        self.on_sites = on_sites

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(0, 20),
        )

        ctk.CTkLabel(
            header,
            text="Master Data Management",
            font=("Segoe UI", 28, "bold"),
            text_color=JCAPTheme.TEXT_DARK,
        ).pack(
            anchor="w",
        )

        ctk.CTkLabel(
            header,
            text=(
                "Manage the foundational records used throughout "
                "the JCAP Construction Suite."
            ),
            font=("Segoe UI", 14),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack(
            anchor="w",
            pady=(6, 0),
        )

        self.create_module_card(
            column=0,
            title="Client Management",
            description=(
                "Create and maintain client records used by "
                "projects and material requests."
            ),
            button_text="Open Clients",
            command=self.on_clients,
        )

        self.create_module_card(
            column=1,
            title="Project Management",
            description=(
                "Create projects, connect them to clients, and "
                "manage project information."
            ),
            button_text="Open Projects",
            command=self.on_projects,
        )

        self.create_module_card(
            column=2,
            title="Site Management",
            description=(
                "Create and maintain project sites used when "
                "preparing material requests."
            ),
            button_text="Open Sites",
            command=self.on_sites,
        )

        information_card = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )
        information_card.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=8,
            pady=(20, 8),
        )

        ctk.CTkLabel(
            information_card,
            text="Master Data Relationship",
            font=("Segoe UI", 20, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            pady=(45, 12),
        )

        ctk.CTkLabel(
            information_card,
            text=(
                "Client  →  Project  →  Site  →  "
                "Material Request  →  Supplier Quotation"
            ),
            font=("Segoe UI", 16, "bold"),
            text_color=JCAPTheme.PRIMARY_BLUE,
        ).pack(
            pady=(0, 12),
        )

        ctk.CTkLabel(
            information_card,
            text=(
                "Create clients first, then connect projects to those "
                "clients and add the applicable project sites."
            ),
            font=("Segoe UI", 14),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack(
            pady=(0, 45),
        )

    def create_module_card(
        self,
        *,
        column,
        title,
        description,
        button_text,
        command,
    ):
        card = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )
        card.grid(
            row=1,
            column=column,
            sticky="nsew",
            padx=8,
            pady=5,
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 19, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            anchor="w",
            padx=22,
            pady=(24, 10),
        )

        ctk.CTkLabel(
            card,
            text=description,
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_MUTED,
            justify="left",
            wraplength=300,
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 20),
        )

        ctk.CTkButton(
            card,
            text=button_text,
            width=150,
            height=38,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            command=command,
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 24),
        )