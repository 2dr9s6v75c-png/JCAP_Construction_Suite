import customtkinter as ctk

from config import settings
from core.navigation.navigation_service import NavigationService
from modules.quotation.views.quotation_view import QuotationView
from modules.quotation.views.material_request_view import MaterialRequestView


class JCAPTheme:
    PRIMARY_BLUE = "#0D47A1"
    PRIMARY_BLUE_LIGHT = "#1976D2"
    DARK_BLUE = "#0A2E63"
    BG_LIGHT = "#F5F7FA"
    CARD_BG = "#FFFFFF"
    TEXT_DARK = "#111827"
    TEXT_MUTED = "#607D8B"
    GREEN = "#43A047"


class MainWindow(ctk.CTk):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.title(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.geometry("1400x850")
        self.minsize(1200, 720)

        try:
            self.state("zoomed")
        except Exception:
            pass

        self.build_ui()

    def build_ui(self):
        self.configure(fg_color=JCAPTheme.BG_LIGHT)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=JCAPTheme.DARK_BLUE)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=JCAPTheme.CARD_BG)
        self.header.grid(row=0, column=1, sticky="ew")
        self.header.grid_propagate(False)

        self.workspace = ctk.CTkFrame(self, corner_radius=0, fg_color=JCAPTheme.BG_LIGHT)
        self.workspace.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)

        self.navigation = NavigationService(self.workspace)

        self.status_bar = ctk.CTkFrame(self, height=35, corner_radius=0, fg_color=JCAPTheme.CARD_BG)
        self.status_bar.grid(row=2, column=1, sticky="ew")
        self.status_bar.grid_propagate(False)

        self.build_sidebar()
        self.build_header()
        self.show_dashboard()
        self.build_status_bar()

    def build_sidebar(self):
        logo = ctk.CTkLabel(
            self.sidebar,
            text="JCAP",
            font=("Segoe UI", 28, "bold"),
            text_color="white",
        )
        logo.pack(pady=(35, 5))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="CONSTRUCTION SUITE",
            font=("Segoe UI", 12, "bold"),
            text_color="#DDEBFF",
        )
        subtitle.pack(pady=(0, 30))

        menu_items = [
            {"text": "Dashboard", "command": self.show_dashboard},
            {"text": "Quotation Monitoring", "command": self.show_quotation_module},
            {"text": "Supplier RFQ", "command": self.show_coming_soon},
            {"text": "Material Costing", "command": self.show_coming_soon},
            {"text": "Purchase Orders", "command": self.show_coming_soon},
            {"text": "Inventory", "command": self.show_coming_soon},
            {"text": "Invoice Monitoring", "command": self.show_coming_soon},
            {"text": "Reports", "command": self.show_coming_soon},
            {"text": "Administration", "command": self.show_coming_soon},
            {"text": "Settings", "command": self.show_coming_soon},
            {"text": "Logout", "command": self.logout},
        ]

        for item in menu_items:
            button = ctk.CTkButton(
                self.sidebar,
                text=item["text"],
                width=210,
                height=38,
                anchor="w",
                font=("Segoe UI", 13),
                fg_color=JCAPTheme.PRIMARY_BLUE if item["text"] == "Dashboard" else "transparent",
                hover_color=JCAPTheme.PRIMARY_BLUE_LIGHT,
                text_color="white",
                corner_radius=8,
                command=item["command"],
            )
            button.pack(pady=4, padx=20)

    def build_header(self):
        title = ctk.CTkLabel(
            self.header,
            text="JCAP CONSTRUCTION SUITE",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        )
        title.pack(side="left", padx=25)

        user_info = ctk.CTkLabel(
            self.header,
            text=f"{self.user['full_name']}  |  {self.user['role']}",
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_MUTED,
        )
        user_info.pack(side="right", padx=25)

    def clear_workspace(self):
        for widget in self.workspace.winfo_children():
            widget.destroy()

        for col in range(10):
            self.workspace.grid_columnconfigure(col, weight=0)

        for row in range(10):
            self.workspace.grid_rowconfigure(row, weight=0)

    def show_dashboard(self):
        self.clear_workspace()
        self.build_dashboard()

    def show_quotation_module(self):
        self.navigation.navigate(
            QuotationView,
            self.user,
            on_new_request=self.show_new_material_request,
        )

    def show_new_material_request(self):
        self.navigation.navigate(
            MaterialRequestView,
            self.user,
            on_back=self.show_quotation_module,
        )

    def show_coming_soon(self):
        self.clear_workspace()

        frame = ctk.CTkFrame(self.workspace, fg_color=JCAPTheme.CARD_BG, corner_radius=14)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Module Coming Soon",
            font=("Segoe UI", 28, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(pady=(120, 10))

        ctk.CTkLabel(
            frame,
            text="This module is reserved for future JCAP Construction Suite development.",
            font=("Segoe UI", 15),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack()

    def logout(self):
        self.destroy()

        from modules.authentication.login_window import LoginWindow

        login = LoginWindow()
        login.mainloop()

    def build_dashboard(self):
        self.workspace.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.workspace.grid_rowconfigure(2, weight=1)

        page_title = ctk.CTkLabel(
            self.workspace,
            text="Dashboard",
            font=("Segoe UI", 26, "bold"),
            text_color=JCAPTheme.TEXT_DARK,
        )
        page_title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 20))

        cards = [
            ("Total Material Requests", "0"),
            ("Pending Quotations", "0"),
            ("In Progress", "0"),
            ("Completed", "0"),
        ]

        for index, (label, value) in enumerate(cards):
            card = ctk.CTkFrame(self.workspace, fg_color=JCAPTheme.CARD_BG, corner_radius=14)
            card.grid(row=1, column=index, sticky="ew", padx=8, pady=5)

            ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 13),
                text_color=JCAPTheme.TEXT_MUTED,
            ).pack(pady=(18, 5))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI", 32, "bold"),
                text_color=JCAPTheme.PRIMARY_BLUE,
            ).pack(pady=(0, 18))

        welcome_card = ctk.CTkFrame(
            self.workspace,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=14,
        )
        welcome_card.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=8, pady=20)

        ctk.CTkLabel(
            welcome_card,
            text="Welcome to JCAP Construction Suite",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(pady=(60, 10))

        ctk.CTkLabel(
            welcome_card,
            text="Quotation Monitoring will be the first active module.",
            font=("Segoe UI", 15),
            text_color=JCAPTheme.TEXT_MUTED,
        ).pack()

    def build_status_bar(self):
        status = ctk.CTkLabel(
            self.status_bar,
            text="● System Online   |   PostgreSQL Connected   |   Version 1.0.0-dev.1",
            font=("Segoe UI", 12),
            text_color=JCAPTheme.GREEN,
        )
        status.pack(side="left", padx=20)