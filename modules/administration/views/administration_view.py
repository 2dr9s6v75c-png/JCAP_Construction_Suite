import customtkinter as ctk

from core.organization.organization_service import OrganizationService
from core.theme import JCAPTheme


class AdministrationView(ctk.CTkFrame):
    """
    Main Administration Module dashboard.

    Provides organization summary information and navigation
    entry points for administrative functions.
    """

    def __init__(
        self,
        parent,
        user,
        on_users=None,
        on_roles_permissions=None,
        on_departments=None,
        on_job_titles=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BG_LIGHT,
            corner_radius=0,
        )

        self.user = user

        self.on_users = on_users
        self.on_roles_permissions = on_roles_permissions
        self.on_departments = on_departments
        self.on_job_titles = on_job_titles

        self.summary = {}

        self.build_ui()
        self.refresh_dashboard()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_summary_section()
        self.build_management_section()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )

        header.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(
            header,
            fg_color="transparent",
        )
        title_block.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=16,
        )

        ctk.CTkLabel(
            title_block,
            text="Administration",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Manage users, roles, permissions, "
                "departments, and job titles"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        ctk.CTkButton(
            header,
            text="Refresh",
            width=110,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            command=self.refresh_dashboard,
        ).grid(
            row=0,
            column=1,
            padx=20,
            pady=16,
        )

    def build_summary_section(self):
        section = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        section.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

        for column in range(6):
            section.grid_columnconfigure(
                column,
                weight=1,
                uniform="summary",
            )

        self.summary_labels = {}

        cards = [
            (
                "total_users",
                "Total Users",
            ),
            (
                "active_users",
                "Active Users",
            ),
            (
                "disabled_users",
                "Disabled Users",
            ),
            (
                "roles",
                "Roles",
            ),
            (
                "departments",
                "Departments",
            ),
            (
                "job_titles",
                "Job Titles",
            ),
        ]

        for column, (key, title) in enumerate(cards):
            card = ctk.CTkFrame(
                section,
                fg_color="#FFFFFF",
                corner_radius=14,
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=5,
            )

            value_label = ctk.CTkLabel(
                card,
                text="0",
                font=("Segoe UI", 28, "bold"),
                text_color=JCAPTheme.PRIMARY_BLUE,
            )
            value_label.pack(
                pady=(18, 2),
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=("Segoe UI", 12, "bold"),
                text_color=JCAPTheme.TEXT_MUTED,
            ).pack(
                pady=(0, 18),
            )

            self.summary_labels[key] = value_label

    def build_management_section(self):
        section = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=14,
        )
        section.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        section.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="management",
        )

        ctk.CTkLabel(
            section,
            text="Administration Tools",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(18, 10),
        )

        tools = [
            (
                "User Management",
                (
                    "Create, update, enable, and disable "
                    "JCAP user accounts."
                ),
                self.on_users,
            ),
            (
                "Roles & Permissions",
                (
                    "Manage system roles and the centralized "
                    "permission matrix."
                ),
                self.on_roles_permissions,
            ),
            (
                "Departments",
                (
                    "Manage the JCAP organization "
                    "department structure."
                ),
                self.on_departments,
            ),
            (
                "Job Titles",
                (
                    "Manage job titles and department "
                    "assignments."
                ),
                self.on_job_titles,
            ),
        ]

        for index, (
            title,
            description,
            command,
        ) in enumerate(tools):
            row = (index // 2) + 1
            column = index % 2

            self.add_management_card(
                section,
                title,
                description,
                row,
                column,
                command,
            )

    def add_management_card(
        self,
        parent,
        title,
        description,
        row,
        column,
        command,
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color=JCAPTheme.BG_LIGHT,
            corner_radius=12,
        )
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=12,
            pady=10,
        )

        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 16, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(18, 4),
        )

        ctk.CTkLabel(
            card,
            text=description,
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_MUTED,
            justify="left",
            wraplength=420,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 14),
        )

        button = ctk.CTkButton(
            card,
            text="Open",
            width=110,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            command=command,
        )
        button.grid(
            row=2,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 18),
        )

        if command is None:
            button.configure(
                state="disabled"
            )

    # ============================================================
    # DATA
    # ============================================================

    def refresh_dashboard(self):
        try:
            self.summary = (
                OrganizationService
                .get_organization_summary()
            )

            for key, label in (
                self.summary_labels.items()
            ):
                value = self.summary.get(
                    key,
                    0,
                )

                label.configure(
                    text=str(value)
                )

        except Exception as error:
            print(
                "Failed to load Administration dashboard:"
            )
            print(error)