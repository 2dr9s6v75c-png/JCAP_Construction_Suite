import customtkinter as ctk

from core.organization.organization_service import OrganizationService
from core.theme import JCAPTheme


class CreateUserView(ctk.CTkFrame):
    """
    Administration Create User workspace.

    Creates JCAP Construction Suite user accounts through
    OrganizationService.
    """

    def __init__(
        self,
        parent,
        user,
        on_back=None,
        on_saved=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.on_back = on_back
        self.on_saved = on_saved

        self.roles = []
        self.departments = []
        self.job_titles = []

        self.role_map = {}
        self.department_map = {}
        self.job_title_map = {}

        self.build_ui()
        self.load_reference_data()

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

        ctk.CTkLabel(
            title_block,
            text="Create User",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=(
                "Create a new JCAP Construction Suite "
                "user account"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        self.save_button = ctk.CTkButton(
            header,
            text="Create Account",
            width=140,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.save_user,
        )
        self.save_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=16,
        )

        ctk.CTkButton(
            header,
            text="Cancel",
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
        form_card = ctk.CTkScrollableFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )
        form_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20),
        )

        form_card.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="user_form",
        )

        ctk.CTkLabel(
            form_card,
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

        self.username_entry = self.add_entry(
            form_card,
            "Username *",
            1,
            0,
            placeholder="Enter username",
        )

        self.full_name_entry = self.add_entry(
            form_card,
            "Full Name *",
            1,
            1,
            placeholder="Enter employee full name",
        )

        self.password_entry = self.add_entry(
            form_card,
            "Password *",
            2,
            0,
            placeholder="Minimum 8 characters",
            show="●",
        )

        self.confirm_password_entry = self.add_entry(
            form_card,
            "Confirm Password *",
            2,
            1,
            placeholder="Re-enter password",
            show="●",
        )

        ctk.CTkLabel(
            form_card,
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
            form_card,
            "System Role *",
            4,
            0,
        )

        self.department_menu = self.add_option(
            form_card,
            "Department *",
            4,
            1,
            command=self.handle_department_change,
        )

        self.job_title_menu = self.add_option(
            form_card,
            "Job Title *",
            5,
            0,
        )

        self.employee_number_entry = self.add_entry(
            form_card,
            "Employee Number",
            5,
            1,
        )

        self.employee_number_entry.configure(
            state="disabled"
        )

        ctk.CTkLabel(
            form_card,
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
            form_card,
            "Email",
            7,
            0,
            placeholder="Enter email address",
        )

        self.phone_entry = self.add_entry(
            form_card,
            "Phone",
            7,
            1,
            placeholder="Enter phone number",
        )

        self.message_label = ctk.CTkLabel(
            form_card,
            text="",
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.RED,
            wraplength=900,
        )
        self.message_label.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(20, 5),
        )

        ctk.CTkLabel(
            form_card,
            text=(
                "* Required fields. Employee Number is "
                "automatically generated by the system."
            ),
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=9,
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
        command=None,
    ):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )
        wrapper.grid(
            row=row,
            column=column,
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
    # REFERENCE DATA
    # ============================================================

    def load_reference_data(self):
        try:
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

            if role_names:
                self.role_menu.set(
                    role_names[0]
                )

            if department_names:
                self.department_menu.set(
                    department_names[0]
                )

                self.load_job_titles(
                    department_names[0]
                )

            self.show_employee_number_preview()

        except Exception as error:
            self.show_error(
                f"Failed to load organization data: {error}"
            )

            self.save_button.configure(
                state="disabled"
            )

    def load_job_titles(
        self,
        department_name,
    ):
        department = self.department_map.get(
            department_name
        )

        if not department:
            self.job_titles = []
            self.job_title_map = {}

            self.job_title_menu.configure(
                values=["No job titles"]
            )
            self.job_title_menu.set(
                "No job titles"
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

        if job_title_names:
            self.job_title_menu.set(
                job_title_names[0]
            )
        else:
            self.job_title_menu.set(
                "No active job titles"
            )

    def show_employee_number_preview(self):
        employee_number = (
            OrganizationService
            .generate_employee_number()
        )

        self.employee_number_entry.configure(
            state="normal"
        )
        self.employee_number_entry.delete(
            0,
            "end",
        )
        self.employee_number_entry.insert(
            0,
            employee_number,
        )
        self.employee_number_entry.configure(
            state="disabled"
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
    # SAVE
    # ============================================================

    def save_user(self):
        self.clear_message()

        username = (
            self.username_entry.get()
            .strip()
        )

        full_name = (
            self.full_name_entry.get()
            .strip()
        )

        password = self.password_entry.get()

        confirm_password = (
            self.confirm_password_entry.get()
        )

        role_name = self.role_menu.get()
        department_name = (
            self.department_menu.get()
        )
        job_title_name = (
            self.job_title_menu.get()
        )

        email = self.email_entry.get().strip()
        phone = self.phone_entry.get().strip()

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

        if not password:
            self.show_error(
                "Password is required."
            )
            return

        if len(password) < 8:
            self.show_error(
                "Password must contain at least 8 characters."
            )
            return

        if password != confirm_password:
            self.show_error(
                "Password and Confirm Password do not match."
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

        self.save_button.configure(
            state="disabled",
            text="Creating...",
        )

        try:
            user_id = (
                OrganizationService.create_user(
                    {
                        "username": username,
                        "password": password,
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "role_id": role["id"],
                        "department_id": department["id"],
                        "job_title_id": job_title["id"],
                    },
                    self.user,
                )
            )

            created_user = (
                OrganizationService.get_user(
                    user_id
                )
            )

            employee_number = (
                created_user["employee_number"]
                if created_user
                else ""
            )

            self.show_success(
                (
                    "User account created successfully. "
                    f"Employee Number: {employee_number}"
                )
            )

            if self.on_saved:
                self.after(
                    500,
                    self.on_saved,
                )

        except Exception as error:
            self.show_error(
                str(error)
            )

            self.save_button.configure(
                state="normal",
                text="Create Account",
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
            text=message,
            text_color=JCAPTheme.RED,
        )

    def show_success(
        self,
        message,
    ):
        self.message_label.configure(
            text=message,
            text_color=JCAPTheme.GREEN,
        )