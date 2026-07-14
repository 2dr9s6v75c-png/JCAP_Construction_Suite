import customtkinter as ctk

from config import settings

from core.clarifications.clarification_service import (
    ClarificationService,
)
from core.navigation.navigation_service import NavigationService
from core.notifications.notification_service import NotificationService
from core.security.permissions import PermissionService
from core.theme import JCAPTheme

from modules.administration.views.administration_view import (
    AdministrationView,
)
from modules.administration.views.create_user_view import (
    CreateUserView,
)
from modules.administration.views.edit_user_view import (
    EditUserView,
)
from modules.administration.views.roles_permissions_view import (
    RolesPermissionsView,
)
from modules.administration.views.user_management_view import (
    UserManagementView,
)

from modules.quotation.views.clarification_details_view import (
    ClarificationDetailsView,
)
from modules.quotation.views.material_request_details_view import (
    MaterialRequestDetailsView,
)
from modules.quotation.views.material_request_edit_view import (
    MaterialRequestEditView,
)
from modules.quotation.views.material_request_view import (
    MaterialRequestView,
)
from modules.quotation.views.quotation_view import (
    QuotationView,
)
from modules.quotation.views.record_supplier_clarification_view import (
    RecordSupplierClarificationView,
)
from modules.shared.notification_bell import (
    NotificationBell,
)
from modules.shared.notification_panel import (
    NotificationPanel,
)


class MainWindow(ctk.CTk):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.sidebar_buttons = {}
        self.active_navigation = None
        self.notification_panel = None

        self.title(
            f"{settings.APP_NAME} v{settings.APP_VERSION}"
        )

        self.geometry("1400x850")
        self.minsize(1200, 720)

        try:
            self.state("zoomed")
        except Exception:
            pass

        self.build_ui()

    # ============================================================
    # MAIN UI
    # ============================================================

    def build_ui(self):
        self.configure(
            fg_color=JCAPTheme.BG_LIGHT
        )

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color=JCAPTheme.DARK_BLUE,
        )
        self.sidebar.grid(
            row=0,
            column=0,
            rowspan=3,
            sticky="nsew",
        )
        self.sidebar.grid_propagate(False)

        self.header = ctk.CTkFrame(
            self,
            height=70,
            corner_radius=0,
            fg_color=JCAPTheme.CARD_BG,
        )
        self.header.grid(
            row=0,
            column=1,
            sticky="ew",
        )
        self.header.grid_propagate(False)

        self.workspace = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=JCAPTheme.BG_LIGHT,
        )
        self.workspace.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=15,
            pady=15,
        )

        self.navigation = NavigationService(
            self.workspace
        )

        self.status_bar = ctk.CTkFrame(
            self,
            height=35,
            corner_radius=0,
            fg_color=JCAPTheme.CARD_BG,
        )
        self.status_bar.grid(
            row=2,
            column=1,
            sticky="ew",
        )
        self.status_bar.grid_propagate(False)

        self.build_sidebar()
        self.build_header()
        self.build_status_bar()

        self.show_dashboard()

    # ============================================================
    # SIDEBAR
    # ============================================================

    def build_sidebar(self):
        ctk.CTkLabel(
            self.sidebar,
            text="JCAP",
            font=("Segoe UI", 28, "bold"),
            text_color="white",
        ).pack(
            pady=(35, 5)
        )

        ctk.CTkLabel(
            self.sidebar,
            text="CONSTRUCTION SUITE",
            font=("Segoe UI", 12, "bold"),
            text_color="#DDEBFF",
        ).pack(
            pady=(0, 30)
        )

        menu_items = [
            {
                "key": "dashboard",
                "text": "Dashboard",
                "command": self.show_dashboard,
                "visible": True,
            },
            {
                "key": "quotation",
                "text": "Quotation Monitoring",
                "command": self.show_quotation_module,
                "visible": True,
            },
            {
                "key": "supplier_rfq",
                "text": "Supplier RFQ",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "material_costing",
                "text": "Material Costing",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "purchase_orders",
                "text": "Purchase Orders",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "inventory",
                "text": "Inventory",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "invoice_monitoring",
                "text": "Invoice Monitoring",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "reports",
                "text": "Reports",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "administration",
                "text": "Administration",
                "command": self.show_administration,
                "visible": PermissionService.can_manage_users(
                    self.user
                ),
            },
            {
                "key": "settings",
                "text": "Settings",
                "command": self.show_coming_soon,
                "visible": True,
            },
            {
                "key": "logout",
                "text": "Logout",
                "command": self.logout,
                "visible": True,
            },
        ]

        for item in menu_items:
            if not item["visible"]:
                continue

            button = ctk.CTkButton(
                self.sidebar,
                text=item["text"],
                width=210,
                height=38,
                anchor="w",
                font=("Segoe UI", 13),
                fg_color="transparent",
                hover_color=JCAPTheme.PRIMARY_BLUE_LIGHT,
                text_color="white",
                corner_radius=8,
                command=item["command"],
            )

            button.pack(
                pady=4,
                padx=20,
            )

            self.sidebar_buttons[
                item["key"]
            ] = button

    def set_active_navigation(self, key):
        self.close_notification_panel()
        self.active_navigation = key

        for button_key, button in (
            self.sidebar_buttons.items()
        ):
            if button_key == key:
                button.configure(
                    fg_color=JCAPTheme.PRIMARY_BLUE
                )
            else:
                button.configure(
                    fg_color="transparent"
                )

    # ============================================================
    # HEADER
    # ============================================================

    def build_header(self):
        self.header.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            self.header,
            text="JCAP CONSTRUCTION SUITE",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=25,
        )

        right_side = ctk.CTkFrame(
            self.header,
            fg_color="transparent",
        )

        right_side.grid(
            row=0,
            column=1,
            sticky="e",
            padx=20,
        )

        self.notification_bell = NotificationBell(
            right_side,
            self.user,
            on_click=self.show_notifications,
        )

        self.notification_bell.pack(
            side="left",
            padx=(0, 20),
        )

        display_role = (
            self.user.get("role_name")
            or self.user.get("role")
            or ""
        )

        ctk.CTkLabel(
            right_side,
            text=(
                f"{self.user.get('full_name', '')}"
                f"  |  {display_role}"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack(
            side="left",
        )

    # ============================================================
    # WORKSPACE
    # ============================================================

    def clear_workspace(self):
        for widget in self.workspace.winfo_children():
            widget.destroy()

        for column in range(10):
            self.workspace.grid_columnconfigure(
                column,
                weight=0,
            )

        for row in range(10):
            self.workspace.grid_rowconfigure(
                row,
                weight=0,
            )

    # ============================================================
    # MAIN DASHBOARD
    # ============================================================

    def show_dashboard(self):
        self.set_active_navigation(
            "dashboard"
        )

        self.clear_workspace()
        self.build_dashboard()

    def build_dashboard(self):
        self.workspace.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1,
        )

        self.workspace.grid_rowconfigure(
            2,
            weight=1,
        )

        ctk.CTkLabel(
            self.workspace,
            text="Dashboard",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.TEXT_DARK,
        ).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 20),
        )

        cards = [
            (
                "Total Material Requests",
                "0",
            ),
            (
                "Pending Quotations",
                "0",
            ),
            (
                "In Progress",
                "0",
            ),
            (
                "Completed",
                "0",
            ),
        ]

        for index, (
            label,
            value,
        ) in enumerate(cards):
            card = ctk.CTkFrame(
                self.workspace,
                fg_color=JCAPTheme.CARD_BG,
                corner_radius=14,
            )

            card.grid(
                row=1,
                column=index,
                sticky="ew",
                padx=8,
                pady=5,
            )

            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 13),
                text_color=JCAPTheme.TEXT_MUTED,
            ).pack(
                pady=(18, 5)
            )

            ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI", 32, "bold"),
                text_color=JCAPTheme.PRIMARY_BLUE,
            ).pack(
                pady=(0, 18)
            )

        welcome_card = ctk.CTkFrame(
            self.workspace,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )

        welcome_card.grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="nsew",
            padx=8,
            pady=20,
        )

        ctk.CTkLabel(
            welcome_card,
            text="Welcome to JCAP Construction Suite",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            pady=(60, 10)
        )

        ctk.CTkLabel(
            welcome_card,
            text=(
                "Quotation Monitoring and Material Requests "
                "are currently active."
            ),
            font=("Segoe UI", 15),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack()

    # ============================================================
    # QUOTATION MODULE
    # ============================================================

    def show_quotation_module(self):
        self.set_active_navigation(
            "quotation"
        )

        self.navigation.navigate(
            QuotationView,
            self.user,
            on_new_request=self.show_new_material_request,
            on_open_request=self.show_existing_material_request,
        )

    def show_new_material_request(self):
        """
        Open the New Material Request view.

        RBAC v1 defense-in-depth guard.
        """

        if not PermissionService.can_create_material_request(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to create "
                    "Material Requests."
                ),
                title="Permission Denied",
            )
            return

        self.navigation.navigate(
            MaterialRequestView,
            self.user,
            on_back=self.show_quotation_module,
        )

    def show_existing_material_request(
        self,
        material_request_id,
    ):
        self.set_active_navigation(
            "quotation"
        )

        self.navigation.navigate(
            MaterialRequestDetailsView,
            self.user,
            material_request_id,
            on_back=self.show_quotation_module,
            on_edit=self.show_edit_material_request,
            on_record_clarification=(
                self.show_record_supplier_clarification
            ),
            on_open_clarification=(
                self.show_clarification_details
            ),
        )

    def show_edit_material_request(
        self,
        material_request_id,
    ):
        self.set_active_navigation(
            "quotation"
        )

        self.navigation.navigate(
            MaterialRequestEditView,
            self.user,
            material_request_id,
            on_cancel=lambda: (
                self.show_existing_material_request(
                    material_request_id
                )
            ),
        )

    # ============================================================
    # SUPPLIER CLARIFICATIONS
    # ============================================================

    def show_record_supplier_clarification(
        self,
        material_request_id,
    ):
        if not PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        ):
            NotificationService.error(
                (
                    "You do not have permission to record "
                    "supplier clarifications."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "quotation"
        )

        self.navigation.navigate(
            RecordSupplierClarificationView,
            self.user,
            material_request_id,
            on_cancel=lambda: (
                self.show_existing_material_request(
                    material_request_id
                )
            ),
            on_saved=lambda clarification_id: (
                self.handle_clarification_saved(
                    material_request_id,
                    clarification_id,
                )
            ),
        )

    def handle_clarification_saved(
        self,
        material_request_id,
        clarification_id,
    ):
        self.show_existing_material_request(
            material_request_id
        )

    def show_clarification_details(
        self,
        clarification_id,
    ):
        if not PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.view"
            ),
        ):
            NotificationService.error(
                (
                    "You do not have permission to view "
                    "supplier clarifications."
                ),
                title="Permission Denied",
            )
            return

        clarification = (
            ClarificationService.get_clarification(
                clarification_id
            )
        )

        if not clarification:
            NotificationService.warning(
                (
                    "The selected clarification "
                    "was not found."
                ),
                title="Clarification Unavailable",
            )
            return

        material_request_id = clarification.get(
            "material_request_id"
        )

        self.set_active_navigation(
            "quotation"
        )

        self.navigation.navigate(
            ClarificationDetailsView,
            self.user,
            clarification_id,
            on_back=lambda: (
                self.show_existing_material_request(
                    material_request_id
                )
            ),
            on_status_change=(
                self.handle_clarification_status_change
            ),
        )

    def handle_clarification_status_change(
        self,
        clarification_id,
    ):
        """
        ClarificationDetailsView reloads itself after each
        successful workflow action.

        This callback is reserved for future dashboard counters,
        notification badges, and live quotation monitoring refresh.
        """
        pass

    # ============================================================
    # NOTIFICATIONS
    # ============================================================

    def show_notifications(self):
        """
        Toggle the Notification Center panel.
        """
        if (
            self.notification_panel is not None
            and self.notification_panel.winfo_exists()
        ):
            self.close_notification_panel()
            return

        self.open_notification_panel()

    def open_notification_panel(self):
        """
        Open the read-only Notification Center below the header.
        """
        self.close_notification_panel()

        self.notification_panel = NotificationPanel(
            self,
            self.user,
            on_close=self.close_notification_panel,
            on_notification_selected=(
                self.handle_notification_selected
            ),
            limit=50,
        )

        self.notification_panel.place(
            relx=1.0,
            y=74,
            anchor="ne",
            x=-18,
        )

        self.notification_panel.lift()

    def close_notification_panel(self):
        """
        Close and release the current Notification Center panel.
        """
        panel = getattr(
            self,
            "notification_panel",
            None,
        )

        if panel is None:
            return

        try:
            if panel.winfo_exists():
                panel.destroy()
        except Exception:
            pass

        self.notification_panel = None

    def handle_notification_selected(
        self,
        notification,
    ):
        """
        Placeholder for click-to-open navigation.

        Read status and entity navigation will be implemented
        in the next notification milestone.
        """
        title = (
            notification.get("title")
            or "Notification"
        )

        entity_type = (
            notification.get("entity_type")
            or "Not specified"
        )

        NotificationService.info(
            (
                f"{title}\n\n"
                f"Entity type: {entity_type}\n\n"
                "Click-to-open navigation will be enabled "
                "in the next milestone."
            ),
            title="Notification",
        )

    # ============================================================
    # ADMINISTRATION MODULE
    # ============================================================

    def show_administration(self):
        if not PermissionService.can_manage_users(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to access "
                    "the Administration module."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "administration"
        )

        self.navigation.navigate(
            AdministrationView,
            self.user,
            on_users=self.show_user_management,
            on_roles_permissions=(
                self.show_roles_permissions
            ),
            on_departments=self.show_departments,
            on_job_titles=self.show_job_titles,
        )

    def show_user_management(self):
        if not PermissionService.can_manage_users(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to manage "
                    "user accounts."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "administration"
        )

        self.navigation.navigate(
            UserManagementView,
            self.user,
            on_back=self.show_administration,
            on_create_user=self.show_create_user,
            on_edit_user=self.show_edit_user,
        )

    def show_create_user(self):
        if not PermissionService.can_manage_users(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to create "
                    "user accounts."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "administration"
        )

        self.navigation.navigate(
            CreateUserView,
            self.user,
            on_back=self.show_user_management,
            on_saved=self.show_user_management,
        )

    def show_edit_user(
        self,
        user_id,
    ):
        if not PermissionService.can_manage_users(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to edit "
                    "user accounts."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "administration"
        )

        self.navigation.navigate(
            EditUserView,
            self.user,
            user_id,
            on_back=self.show_user_management,
            on_saved=self.show_edit_user,
        )

    def show_roles_permissions(self):
        if not PermissionService.can_manage_roles(
            self.user
        ):
            NotificationService.error(
                (
                    "You do not have permission to manage "
                    "roles and permissions."
                ),
                title="Permission Denied",
            )
            return

        self.set_active_navigation(
            "administration"
        )

        self.navigation.navigate(
            RolesPermissionsView,
            self.user,
            on_back=self.show_administration,
        )

    def show_departments(self):
        self.show_administration_placeholder(
            title="Departments",
            description=(
                "Manage the JCAP organizational "
                "department structure."
            ),
        )

    def show_job_titles(self):
        self.show_administration_placeholder(
            title="Job Titles",
            description=(
                "Manage job titles and department "
                "assignments."
            ),
        )

    def show_administration_placeholder(
        self,
        title,
        description,
    ):
        self.clear_workspace()

        frame = ctk.CTkFrame(
            self.workspace,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Segoe UI", 28, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            pady=(100, 10)
        )

        ctk.CTkLabel(
            frame,
            text=description,
            font=("Segoe UI", 15),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack()

        ctk.CTkButton(
            frame,
            text="Back to Administration",
            width=190,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            command=self.show_administration,
        ).pack(
            pady=25
        )

    # ============================================================
    # COMING SOON
    # ============================================================

    def show_coming_soon(self):
        self.clear_workspace()

        frame = ctk.CTkFrame(
            self.workspace,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        ctk.CTkLabel(
            frame,
            text="Module Coming Soon",
            font=("Segoe UI", 28, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            pady=(120, 10)
        )

        ctk.CTkLabel(
            frame,
            text=(
                "This module is reserved for future "
                "JCAP Construction Suite development."
            ),
            font=("Segoe UI", 15),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack()

    # ============================================================
    # LOGOUT
    # ============================================================

    def logout(self):
        self.close_notification_panel()
        self.destroy()

        from modules.authentication.login_window import (
            LoginWindow,
        )

        login = LoginWindow()
        login.mainloop()

    # ============================================================
    # STATUS BAR
    # ============================================================

    def build_status_bar(self):
        ctk.CTkLabel(
            self.status_bar,
            text=(
                "● System Online   |   "
                "PostgreSQL Connected   |   "
                f"Version {settings.APP_VERSION}"
            ),
            font=("Segoe UI", 12),
            text_color=JCAPTheme.GREEN,
        ).pack(
            side="left",
            padx=20,
        )