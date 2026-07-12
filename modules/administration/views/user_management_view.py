import customtkinter as ctk

from core.organization.organization_service import OrganizationService
from core.theme import JCAPTheme


class UserManagementView(ctk.CTkFrame):
    """
    Administration User Management workspace.

    Displays JCAP user accounts and provides the entry point
    for account creation and maintenance.
    """

    FILTER_ALL = "All Accounts"
    FILTER_ACTIVE = "Active"
    FILTER_DISABLED = "Disabled"

    def __init__(
        self,
        parent,
        user,
        on_back=None,
        on_create_user=None,
        on_edit_user=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user

        self.on_back = on_back
        self.on_create_user = on_create_user
        self.on_edit_user = on_edit_user

        self.users = []
        self.filtered_users = []

        self.search_var = ctk.StringVar()
        self.filter_var = ctk.StringVar(
            value=self.FILTER_ALL
        )

        self.build_ui()
        self.load_users()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_toolbar()
        self.build_user_table()

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
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
            text="User Management",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Manage JCAP Construction Suite "
                "user accounts"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        ctk.CTkButton(
            header,
            text="Create User",
            width=130,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.handle_create_user,
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=16,
        )

        ctk.CTkButton(
            header,
            text="Back",
            width=100,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self.on_back,
        ).grid(
            row=0,
            column=2,
            padx=(5, 20),
            pady=16,
        )

    def build_toolbar(self):
        toolbar = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

        toolbar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text=(
                "Search employee number, name, "
                "username, role, department..."
            ),
            height=38,
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(16, 8),
            pady=14,
        )

        self.search_var.trace_add(
            "write",
            self.handle_filter_change,
        )

        self.filter_menu = ctk.CTkOptionMenu(
            toolbar,
            variable=self.filter_var,
            values=[
                self.FILTER_ALL,
                self.FILTER_ACTIVE,
                self.FILTER_DISABLED,
            ],
            width=150,
            command=lambda _value: self.apply_filters(),
        )
        self.filter_menu.grid(
            row=0,
            column=1,
            padx=8,
            pady=14,
        )

        ctk.CTkButton(
            toolbar,
            text="Refresh",
            width=100,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.PRIMARY_BLUE_HOVER,
            command=self.load_users,
        ).grid(
            row=0,
            column=2,
            padx=(8, 16),
            pady=14,
        )

    def build_user_table(self):
        table_card = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        table_card.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(2, weight=1)

        summary_frame = ctk.CTkFrame(
            table_card,
            fg_color="transparent",
        )
        summary_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(16, 8),
        )

        self.result_label = ctk.CTkLabel(
            summary_frame,
            text="0 users",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )
        self.result_label.pack(side="left")

        header = ctk.CTkFrame(
            table_card,
            fg_color=JCAPTheme.DARK_BLUE,
            corner_radius=8,
        )
        header.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 4),
        )

        self.configure_table_columns(header)

        headers = [
            "Employee No.",
            "Full Name",
            "Username",
            "Role",
            "Department",
            "Job Title",
            "Status",
            "Action",
        ]

        for column, text in enumerate(headers):
            ctk.CTkLabel(
                header,
                text=text,
                font=("Segoe UI", 11, "bold"),
                text_color="white",
                anchor="w",
            ).grid(
                row=0,
                column=column,
                sticky="ew",
                padx=8,
                pady=11,
            )

        self.table_scroll = ctk.CTkScrollableFrame(
            table_card,
            fg_color="transparent",
            corner_radius=0,
        )
        self.table_scroll.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 12),
        )

        self.configure_table_columns(
            self.table_scroll
        )

    def configure_table_columns(self, widget):
        weights = [
            1,
            2,
            1,
            2,
            2,
            2,
            1,
            1,
        ]

        for column, weight in enumerate(weights):
            widget.grid_columnconfigure(
                column,
                weight=weight,
                uniform=f"user_column_{column}",
            )

    # ============================================================
    # DATA
    # ============================================================

    def load_users(self):
        self.users = OrganizationService.get_users()

        self.apply_filters()

    def apply_filters(self):
        search_text = (
            self.search_var.get()
            .strip()
            .lower()
        )

        selected_filter = self.filter_var.get()

        filtered = []

        for user in self.users:
            is_active = bool(
                user.get("is_active")
            )

            if (
                selected_filter == self.FILTER_ACTIVE
                and not is_active
            ):
                continue

            if (
                selected_filter == self.FILTER_DISABLED
                and is_active
            ):
                continue

            searchable_values = [
                user.get("employee_number"),
                user.get("full_name"),
                user.get("username"),
                user.get("role_name"),
                user.get("department_name"),
                user.get("job_title_name"),
            ]

            searchable_text = " ".join(
                str(value or "")
                for value in searchable_values
            ).lower()

            if (
                search_text
                and search_text not in searchable_text
            ):
                continue

            filtered.append(user)

        self.filtered_users = filtered

        self.render_users()

    def render_users(self):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.result_label.configure(
            text=(
                f"{len(self.filtered_users)} "
                f"user"
                f"{'' if len(self.filtered_users) == 1 else 's'}"
            )
        )

        if not self.filtered_users:
            ctk.CTkLabel(
                self.table_scroll,
                text="No user accounts found.",
                font=("Segoe UI", 14),
                text_color=JCAPTheme.TEXT_SECONDARY,
            ).grid(
                row=0,
                column=0,
                columnspan=8,
                pady=40,
            )

            return

        for row_index, user in enumerate(
            self.filtered_users
        ):
            self.add_user_row(
                row_index,
                user,
            )

    def add_user_row(
        self,
        row_index,
        user,
    ):
        row_color = (
            "#FFFFFF"
            if row_index % 2 == 0
            else "#F8FAFC"
        )

        values = [
            user.get("employee_number") or "",
            user.get("full_name") or "",
            user.get("username") or "",
            user.get("role_name")
            or user.get("role")
            or "",
            user.get("department_name") or "",
            user.get("job_title_name") or "",
        ]

        for column, value in enumerate(values):
            ctk.CTkLabel(
                self.table_scroll,
                text=str(value),
                font=("Segoe UI", 11),
                text_color=JCAPTheme.TEXT,
                anchor="w",
                fg_color=row_color,
            ).grid(
                row=row_index,
                column=column,
                sticky="nsew",
                padx=1,
                pady=1,
                ipadx=8,
                ipady=10,
            )

        is_active = bool(
            user.get("is_active")
        )

        status_text = (
            "Active"
            if is_active
            else "Disabled"
        )

        status_color = (
            JCAPTheme.GREEN
            if is_active
            else JCAPTheme.RED
        )

        ctk.CTkLabel(
            self.table_scroll,
            text=status_text,
            font=("Segoe UI", 11, "bold"),
            text_color=status_color,
            anchor="w",
            fg_color=row_color,
        ).grid(
            row=row_index,
            column=6,
            sticky="nsew",
            padx=1,
            pady=1,
            ipadx=8,
            ipady=10,
        )

        action_frame = ctk.CTkFrame(
            self.table_scroll,
            fg_color=row_color,
            corner_radius=0,
        )
        action_frame.grid(
            row=row_index,
            column=7,
            sticky="nsew",
            padx=1,
            pady=1,
        )

        ctk.CTkButton(
            action_frame,
            text="Edit",
            width=70,
            height=28,
            fg_color=JCAPTheme.EDIT,
            hover_color=JCAPTheme.EDIT_HOVER,
            command=lambda selected_user=user: (
                self.handle_edit_user(
                    selected_user
                )
            ),
        ).pack(
            padx=6,
            pady=7,
        )

    # ============================================================
    # EVENTS
    # ============================================================

    def handle_filter_change(
        self,
        *_args,
    ):
        self.apply_filters()

    def handle_create_user(self):
        if self.on_create_user:
            self.on_create_user()

    def handle_edit_user(
        self,
        user,
    ):
        if self.on_edit_user:
            self.on_edit_user(
                user["id"]
            )