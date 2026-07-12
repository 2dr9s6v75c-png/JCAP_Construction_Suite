import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from core.organization.organization_service import OrganizationService
from core.theme import JCAPTheme


class RolesPermissionsView(ctk.CTkFrame):
    """
    Role-focused Roles & Permissions Administration workspace.

    Loads active roles and displays the complete RBAC v1 permission
    registry grouped by system capability.
    """

    def __init__(
        self,
        parent,
        user,
        on_back=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.on_back = on_back

        self.roles = []
        self.role_map = {}

        self.current_role_id = None
        self.current_editor_data = None

        self.permission_vars = {}
        self.permission_checkboxes = {}

        self.role_var = ctk.StringVar()

        self.build_ui()
        self.load_roles()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_role_selector()
        self.build_permission_workspace()

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
            text="Roles & Permissions",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Manage database-driven RBAC permissions "
                "for JCAP system roles"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        self.save_button = ctk.CTkButton(
            header,
            text="Save Changes",
            width=140,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.save_changes,
        )
        self.save_button.grid(
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
            command=self.handle_back,
        ).grid(
            row=0,
            column=2,
            padx=(5, 20),
            pady=16,
        )

    def build_role_selector(self):
        selector = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        selector.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

        selector.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            selector,
            text="Role",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(20, 10),
            pady=16,
        )

        self.role_menu = ctk.CTkOptionMenu(
            selector,
            variable=self.role_var,
            values=["Loading..."],
            height=38,
            command=self.handle_role_change,
        )
        self.role_menu.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=10,
            pady=16,
        )

        self.role_status_label = ctk.CTkLabel(
            selector,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )
        self.role_status_label.grid(
            row=0,
            column=2,
            sticky="e",
            padx=(10, 20),
            pady=16,
        )

    def build_permission_workspace(self):
        workspace = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        workspace.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)

        summary = ctk.CTkFrame(
            workspace,
            fg_color="transparent",
        )
        summary.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(16, 8),
        )

        summary.grid_columnconfigure(0, weight=1)

        self.summary_label = ctk.CTkLabel(
            summary,
            text="Select a role",
            font=("Segoe UI", 15, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        )
        self.summary_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.message_label = ctk.CTkLabel(
            summary,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.RED,
        )
        self.message_label.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.permission_scroll = ctk.CTkScrollableFrame(
            workspace,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=10,
        )
        self.permission_scroll.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(0, 16),
        )

        self.permission_scroll.grid_columnconfigure(
            0,
            weight=1,
        )

    # ============================================================
    # ROLE LOADING
    # ============================================================

    def load_roles(self):
        try:
            self.roles = (
                OrganizationService
                .get_roles_permission_overview(
                    self.user
                )
            )

            self.role_map = {
                role["role_name"]: role
                for role in self.roles
            }

            role_names = list(
                self.role_map.keys()
            )

            self.role_menu.configure(
                values=(
                    role_names
                    or ["No active roles"]
                )
            )

            if not role_names:
                self.save_button.configure(
                    state="disabled"
                )
                return

            first_role_name = role_names[0]

            self.role_menu.set(
                first_role_name
            )

            self.load_role_editor(
                self.role_map[
                    first_role_name
                ]["id"]
            )

        except Exception as error:
            NotificationService.error(
                "Unable to load roles and permissions.",
                title="Roles & Permissions",
                error=error,
            )

            self.save_button.configure(
                state="disabled"
            )

    def handle_role_change(
        self,
        role_name,
    ):
        role = self.role_map.get(
            role_name
        )

        if not role:
            return

        self.load_role_editor(
            role["id"]
        )

    # ============================================================
    # ROLE EDITOR
    # ============================================================

    def load_role_editor(
        self,
        role_id,
    ):
        try:
            self.clear_message()

            self.current_editor_data = (
                OrganizationService
                .get_role_permission_editor_data(
                    role_id,
                    self.user,
                )
            )

            self.current_role_id = str(
                role_id
            )

            self.render_permissions()

        except Exception as error:
            NotificationService.error(
                "Unable to load role permissions.",
                title="Role Permission Load Failed",
                error=error,
            )

    def render_permissions(self):
        for widget in (
            self.permission_scroll
            .winfo_children()
        ):
            widget.destroy()

        self.permission_vars = {}
        self.permission_checkboxes = {}

        if not self.current_editor_data:
            return

        role = self.current_editor_data[
            "role"
        ]

        is_protected = bool(
            self.current_editor_data[
                "is_protected"
            ]
        )

        permission_count = (
            self.current_editor_data[
                "permission_count"
            ]
        )

        total_permission_count = (
            self.current_editor_data[
                "total_permission_count"
            ]
        )

        self.summary_label.configure(
            text=(
                f"{role['role_name']}  |  "
                f"{permission_count} of "
                f"{total_permission_count} permissions"
            )
        )

        if is_protected:
            self.role_status_label.configure(
                text="Protected Role",
                text_color=JCAPTheme.ARCHIVE,
            )

            self.save_button.configure(
                state="disabled"
            )

        else:
            self.role_status_label.configure(
                text="Editable Role",
                text_color=JCAPTheme.GREEN,
            )

            self.save_button.configure(
                state="normal"
            )

        groups = self.current_editor_data[
            "groups"
        ]

        current_row = 0

        for group in groups:
            group_card = ctk.CTkFrame(
                self.permission_scroll,
                fg_color=JCAPTheme.CARD,
                corner_radius=12,
            )
            group_card.grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=8,
                pady=8,
            )

            group_card.grid_columnconfigure(
                0,
                weight=1,
            )

            ctk.CTkLabel(
                group_card,
                text=group["title"],
                font=("Segoe UI", 16, "bold"),
                text_color=JCAPTheme.DARK_BLUE,
            ).grid(
                row=0,
                column=0,
                sticky="w",
                padx=18,
                pady=(14, 8),
            )

            for permission_index, permission in enumerate(
                group["permissions"],
                start=1,
            ):
                self.add_permission_row(
                    group_card,
                    permission,
                    permission_index,
                    is_protected,
                )

            current_row += 1

    def add_permission_row(
        self,
        parent,
        permission,
        row,
        is_protected,
    ):
        permission_id = str(
            permission["id"]
        )

        variable = ctk.BooleanVar(
            value=bool(
                permission["assigned"]
            )
        )

        self.permission_vars[
            permission_id
        ] = variable

        permission_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        permission_frame.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=18,
            pady=4,
        )

        permission_frame.grid_columnconfigure(
            1,
            weight=1,
        )

        checkbox = ctk.CTkCheckBox(
            permission_frame,
            text="",
            variable=variable,
            width=28,
            state=(
                "disabled"
                if is_protected
                else "normal"
            ),
        )
        checkbox.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=6,
        )

        self.permission_checkboxes[
            permission_id
        ] = checkbox

        text_frame = ctk.CTkFrame(
            permission_frame,
            fg_color="transparent",
        )
        text_frame.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        ctk.CTkLabel(
            text_frame,
            text=permission["description"],
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
            anchor="w",
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            text_frame,
            text=permission[
                "permission_name"
            ],
            font=("Consolas", 10),
            text_color=JCAPTheme.TEXT_SECONDARY,
            anchor="w",
        ).pack(
            anchor="w",
            pady=(1, 0),
        )

    # ============================================================
    # SAVE
    # ============================================================

    def save_changes(self):
        if not self.current_editor_data:
            return

        if self.current_editor_data[
            "is_protected"
        ]:
            self.show_error(
                (
                    "System Administrator permissions "
                    "are protected."
                )
            )
            return

        selected_permission_ids = [
            permission_id
            for permission_id, variable in (
                self.permission_vars.items()
            )
            if variable.get()
        ]

        role = self.current_editor_data[
            "role"
        ]

        confirmed = NotificationService.confirm(
            (
                "Save permission changes for:\n\n"
                f"{role['role_name']}\n\n"
                "Changes will affect users assigned "
                "to this role."
            ),
            title="Save Role Permissions",
        )

        if not confirmed:
            return

        self.save_button.configure(
            state="disabled",
            text="Saving...",
        )

        try:
            OrganizationService.update_role_permissions(
                self.current_role_id,
                selected_permission_ids,
                self.user,
            )

            NotificationService.success(
                (
                    f"Permissions for "
                    f"{role['role_name']} "
                    "were updated successfully."
                ),
                title="Permissions Updated",
            )

            self.load_roles()

            current_role = self.role_map.get(
                role["role_name"]
            )

            if current_role:
                self.role_menu.set(
                    role["role_name"]
                )

                self.load_role_editor(
                    current_role["id"]
                )

        except ValueError as error:
            self.show_error(
                str(error)
            )

        except Exception as error:
            NotificationService.error(
                "Unable to update role permissions.",
                title="Permission Update Failed",
                error=error,
            )

        finally:
            if (
                self.winfo_exists()
                and self.current_editor_data
                and not self.current_editor_data[
                    "is_protected"
                ]
            ):
                self.save_button.configure(
                    state="normal",
                    text="Save Changes",
                )

    # ============================================================
    # HELPERS
    # ============================================================

    def handle_back(self):
        if self.on_back:
            self.on_back()

    def clear_message(self):
        self.message_label.configure(
            text=""
        )

    def show_error(
        self,
        message,
    ):
        self.message_label.configure(
            text=str(message),
            text_color=JCAPTheme.RED,
        )