import customtkinter as ctk

from core.notifications.notification_service import NotificationService
from core.organization.organization_service import OrganizationService
from core.theme import JCAPTheme


class EditUserView(ctk.CTkFrame):
    """
    Administration Edit User workspace.

    Supports:
    - user profile updates
    - role assignment
    - department assignment
    - job-title assignment
    - password reset
    - account enable / disable
    """

    def __init__(
        self,
        parent,
        user,
        user_id,
        on_back=None,
        on_saved=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.user_id = user_id

        self.on_back = on_back
        self.on_saved = on_saved

        self.account = None

        self.roles = []
        self.departments = []
        self.job_titles = []

        self.role_map = {}
        self.department_map = {}
        self.job_title_map = {}

        self.save_button = None
        self.account_status_button = None
        self.account_status_label = None
        self.message_label = None

        self.build_ui()
        self.load_user()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_form()

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

        self.title_label = ctk.CTkLabel(
            title_block,
            text="Edit User",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="Update JCAP user account information.",
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )
        self.subtitle_label.pack(
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

    def build_form(self):
        self.form_card = ctk.CTkScrollableFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        self.form_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        self.form_card.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="edit_user_form",
        )

        self.build_account_information()
        self.build_organization_assignment()
        self.build_contact_information()
        self.build_password_section()
        self.build_account_status_section()

    def build_account_information(self):
        ctk.CTkLabel(
            self.form_card,
            text="Account Information",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(20, 10),
        )

        self.employee_number_entry = self.add_entry(
            self.form_card,
            "Employee Number",
            1,
            0,
        )
        self.employee_number_entry.configure(
            state="disabled"
        )

        self.username_entry = self.add_entry(
            self.form_card,
            "Username *",
            1,
            1,
            placeholder="Enter username",
        )

        self.full_name_entry = self.add_entry(
            self.form_card,
            "Full Name *",
            2,
            0,
            columnspan=2,
            placeholder="Enter employee full name",
        )

    def build_organization_assignment(self):
        ctk.CTkLabel(
            self.form_card,
            text="Organization Assignment",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(25, 10),
        )

        self.role_menu = self.add_option(
            self.form_card,
            "System Role *",
            4,
            0,
        )

        self.department_menu = self.add_option(
            self.form_card,
            "Department *",
            4,
            1,
            command=self.handle_department_change,
        )

        self.job_title_menu = self.add_option(
            self.form_card,
            "Job Title *",
            5,
            0,
            columnspan=2,
        )

    def build_contact_information(self):
        ctk.CTkLabel(
            self.form_card,
            text="Contact Information",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(25, 10),
        )

        self.email_entry = self.add_entry(
            self.form_card,
            "Email",
            7,
            0,
            placeholder="Enter email address",
        )

        self.phone_entry = self.add_entry(
            self.form_card,
            "Phone",
            7,
            1,
            placeholder="Enter phone number",
        )

    def build_password_section(self):
        ctk.CTkLabel(
            self.form_card,
            text="Password Reset",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(25, 10),
        )

        ctk.CTkLabel(
            self.form_card,
            text=(
                "Leave both password fields blank to keep "
                "the current password."
            ),
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(0, 5),
        )

        self.password_entry = self.add_entry(
            self.form_card,
            "New Password",
            10,
            0,
            placeholder="Minimum 8 characters",
            show="●",
        )

        self.confirm_password_entry = self.add_entry(
            self.form_card,
            "Confirm New Password",
            10,
            1,
            placeholder="Re-enter new password",
            show="●",
        )

    def build_account_status_section(self):
        ctk.CTkLabel(
            self.form_card,
            text="Account Status",
            font=("Segoe UI", 18, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=11,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(25, 10),
        )

        status_card = ctk.CTkFrame(
            self.form_card,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=12,
        )
        status_card.grid(
            row=12,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=8,
        )

        status_card.grid_columnconfigure(
            0,
            weight=1,
        )

        status_text_frame = ctk.CTkFrame(
            status_card,
            fg_color="transparent",
        )
        status_text_frame.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=16,
        )

        ctk.CTkLabel(
            status_text_frame,
            text="Current Account Status",
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(anchor="w")

        self.account_status_label = ctk.CTkLabel(
            status_text_frame,
            text="Loading...",
            font=("Segoe UI", 16, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        )
        self.account_status_label.pack(
            anchor="w",
            pady=(3, 0),
        )

        self.account_status_button = ctk.CTkButton(
            status_card,
            text="Loading...",
            width=150,
            command=self.toggle_account_status,
        )
        self.account_status_button.grid(
            row=0,
            column=1,
            padx=18,
            pady=16,
        )

        self.message_label = ctk.CTkLabel(
            self.form_card,
            text="",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.RED,
            wraplength=900,
            justify="left",
        )
        self.message_label.grid(
            row=13,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(20, 5),
        )

        ctk.CTkLabel(
            self.form_card,
            text=(
                "* Required fields. Account status changes "
                "are logged separately from profile changes."
            ),
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=14,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(5, 25),
        )

    # ============================================================
    # FIELD HELPERS
    # ============================================================

    def add_entry(
        self,
        parent,
        label,
        row,
        column,
        columnspan=1,
        placeholder="",
        show=None,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=20,
            pady=8,
        )
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        entry = ctk.CTkEntry(
            wrapper,
            height=38,
            placeholder_text=placeholder,
            show=show,
        )
        entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        return entry

    def add_option(
        self,
        parent,
        label,
        row,
        column,
        columnspan=1,
        command=None,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=20,
            pady=8,
        )
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=JCAPTheme.TEXT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        option = ctk.CTkOptionMenu(
            wrapper,
            values=["Loading..."],
            height=38,
            command=command,
        )
        option.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        return option

    # ============================================================
    # DATA LOADING
    # ============================================================

    def load_user(self):
        try:
            self.account = OrganizationService.get_user(
                self.user_id
            )

            if not self.account:
                raise ValueError(
                    "User account was not found."
                )

            self.roles = (
                OrganizationService.get_active_roles()
            )

            self.departments = (
                OrganizationService
                .get_active_departments()
            )

            self.role_map = {
                role["role_name"]: role
                for role in self.roles
            }

            self.department_map = {
                department["department_name"]: department
                for department in self.departments
            }

            self.configure_reference_menus()
            self.populate_form()
            self.refresh_account_status()

        except Exception as error:
            NotificationService.error(
                "Unable to load the user account.",
                title="Load User Failed",
                error=error,
            )

            self.save_button.configure(
                state="disabled"
            )

            self.account_status_button.configure(
                state="disabled"
            )

    def configure_reference_menus(self):
        role_names = list(
            self.role_map.keys()
        )

        department_names = list(
            self.department_map.keys()
        )

        self.role_menu.configure(
            values=role_names or ["No active roles"]
        )

        self.department_menu.configure(
            values=(
                department_names
                or ["No active departments"]
            )
        )

    def populate_form(self):
        self.title_label.configure(
            text=(
                f"Edit {self.account['employee_number']}"
            )
        )

        self.subtitle_label.configure(
            text=(
                f"Manage user account for "
                f"{self.account['full_name']}."
            )
        )

        self.set_entry_value(
            self.employee_number_entry,
            self.account["employee_number"],
            disabled=True,
        )

        self.set_entry_value(
            self.username_entry,
            self.account["username"],
        )

        self.set_entry_value(
            self.full_name_entry,
            self.account["full_name"],
        )

        self.set_entry_value(
            self.email_entry,
            self.account["email"],
        )

        self.set_entry_value(
            self.phone_entry,
            self.account["phone"],
        )

        role_name = self.account.get(
            "role_name"
        )

        if role_name in self.role_map:
            self.role_menu.set(
                role_name
            )

        department_name = self.account.get(
            "department_name"
        )

        if department_name in self.department_map:
            self.department_menu.set(
                department_name
            )

            self.load_job_titles(
                department_name,
                selected_job_title_name=(
                    self.account.get(
                        "job_title_name"
                    )
                ),
            )

    def load_job_titles(
        self,
        department_name,
        selected_job_title_name=None,
    ):
        department = self.department_map.get(
            department_name
        )

        if not department:
            self.job_titles = []
            self.job_title_map = {}

            self.job_title_menu.configure(
                values=["No active job titles"]
            )
            self.job_title_menu.set(
                "No active job titles"
            )
            return

        self.job_titles = (
            OrganizationService
            .get_job_titles_by_department(
                department["id"],
                active_only=True,
            )
        )

        self.job_title_map = {
            job_title["job_title_name"]: job_title
            for job_title in self.job_titles
        }

        job_title_names = list(
            self.job_title_map.keys()
        )

        self.job_title_menu.configure(
            values=(
                job_title_names
                or ["No active job titles"]
            )
        )

        if (
            selected_job_title_name
            and selected_job_title_name
            in self.job_title_map
        ):
            self.job_title_menu.set(
                selected_job_title_name
            )

        elif job_title_names:
            self.job_title_menu.set(
                job_title_names[0]
            )

        else:
            self.job_title_menu.set(
                "No active job titles"
            )

    # ============================================================
    # EVENTS
    # ============================================================

    def handle_department_change(
        self,
        department_name,
    ):
        self.load_job_titles(
            department_name
        )

    def handle_back(self):
        if self.on_back:
            self.on_back()

    # ============================================================
    # SAVE PROFILE
    # ============================================================

    def save_changes(self):
        self.clear_message()

        username = self.username_entry.get().strip()

        full_name = self.full_name_entry.get().strip()

        role_name = self.role_menu.get()

        department_name = (
            self.department_menu.get()
        )

        job_title_name = (
            self.job_title_menu.get()
        )

        email = self.email_entry.get().strip()

        phone = self.phone_entry.get().strip()

        password = self.password_entry.get()

        confirm_password = (
            self.confirm_password_entry.get()
        )

        if not username:
            self.show_error(
                "Username is required."
            )
            return

        if not full_name:
            self.show_error(
                "Full name is required."
            )
            return

        role = self.role_map.get(
            role_name
        )

        department = self.department_map.get(
            department_name
        )

        job_title = self.job_title_map.get(
            job_title_name
        )

        if not role:
            self.show_error(
                "Please select a valid system role."
            )
            return

        if not department:
            self.show_error(
                "Please select a valid department."
            )
            return

        if not job_title:
            self.show_error(
                "Please select a valid job title."
            )
            return

        if password or confirm_password:
            if len(password) < 8:
                self.show_error(
                    "New password must contain "
                    "at least 8 characters."
                )
                return

            if password != confirm_password:
                self.show_error(
                    "New Password and Confirm New Password "
                    "do not match."
                )
                return

        update_data = {
            "username": username,
            "full_name": full_name,
            "role_id": role["id"],
            "department_id": department["id"],
            "job_title_id": job_title["id"],
            "email": email,
            "phone": phone,
        }

        if password:
            update_data["password"] = password

        self.save_button.configure(
            state="disabled",
            text="Saving...",
        )

        try:
            OrganizationService.update_user(
                self.user_id,
                update_data,
                self.user,
            )

            self.account = OrganizationService.get_user(
                self.user_id
            )

            self.password_entry.delete(
                0,
                "end",
            )

            self.confirm_password_entry.delete(
                0,
                "end",
            )

            self.populate_form()
            self.refresh_account_status()

            self.show_success(
                "User account changes saved successfully."
            )

            NotificationService.success(
                (
                    f"User account "
                    f"{self.account['employee_number']} "
                    "was updated successfully."
                ),
                title="User Updated",
            )

            if self.on_saved:
                self.on_saved(
                    self.user_id
                )

        except Exception as error:
            self.show_error(
                str(error)
            )

        finally:
            if self.winfo_exists():
                self.save_button.configure(
                    state="normal",
                    text="Save Changes",
                )

    # ============================================================
    # ACCOUNT STATUS
    # ============================================================

    def refresh_account_status(self):
        if not self.account:
            return

        is_active = bool(
            self.account.get("is_active")
        )

        if is_active:
            self.account_status_label.configure(
                text="Active",
                text_color=JCAPTheme.GREEN,
            )

            self.account_status_button.configure(
                text="Disable Account",
                fg_color=JCAPTheme.DELETE,
                hover_color=JCAPTheme.DELETE_HOVER,
                state="normal",
            )

        else:
            self.account_status_label.configure(
                text="Disabled",
                text_color=JCAPTheme.RED,
            )

            self.account_status_button.configure(
                text="Enable Account",
                fg_color=JCAPTheme.SAVE,
                hover_color=JCAPTheme.SAVE_HOVER,
                state="normal",
            )

        if str(self.user_id) == str(
            self.user.get("id")
        ):
            self.account_status_button.configure(
                text="Current Account",
                state="disabled",
            )

    def toggle_account_status(self):
        if not self.account:
            return

        is_active = bool(
            self.account.get("is_active")
        )

        if is_active:
            self.disable_account()
        else:
            self.enable_account()

    def disable_account(self):
        confirmed = NotificationService.confirm(
            (
                "Disable this user account?\n\n"
                f"{self.account['employee_number']}\n"
                f"{self.account['full_name']}\n\n"
                "The user will no longer be able to "
                "log in until the account is enabled again."
            ),
            title="Disable User Account",
        )

        if not confirmed:
            return

        try:
            OrganizationService.disable_user(
                self.user_id,
                self.user,
            )

            self.account = OrganizationService.get_user(
                self.user_id
            )

            self.refresh_account_status()

            NotificationService.success(
                "User account disabled successfully.",
                title="Account Disabled",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to disable the user account.",
                title="Disable Account Failed",
                error=error,
            )

    def enable_account(self):
        confirmed = NotificationService.confirm(
            (
                "Enable this user account?\n\n"
                f"{self.account['employee_number']}\n"
                f"{self.account['full_name']}\n\n"
                "The user will be allowed to log in again."
            ),
            title="Enable User Account",
        )

        if not confirmed:
            return

        try:
            OrganizationService.enable_user(
                self.user_id,
                self.user,
            )

            self.account = OrganizationService.get_user(
                self.user_id
            )

            self.refresh_account_status()

            NotificationService.success(
                "User account enabled successfully.",
                title="Account Enabled",
            )

        except Exception as error:
            NotificationService.error(
                "Unable to enable the user account.",
                title="Enable Account Failed",
                error=error,
            )

    # ============================================================
    # ENTRY HELPERS
    # ============================================================

    @staticmethod
    def set_entry_value(
        entry,
        value,
        *,
        disabled=False,
    ):
        entry.configure(
            state="normal"
        )

        entry.delete(
            0,
            "end",
        )

        entry.insert(
            0,
            str(value or ""),
        )

        if disabled:
            entry.configure(
                state="disabled"
            )

    # ============================================================
    # MESSAGE HELPERS
    # ============================================================

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

    def show_success(
        self,
        message,
    ):
        self.message_label.configure(
            text=str(message),
            text_color=JCAPTheme.GREEN,
        )