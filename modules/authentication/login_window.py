import customtkinter as ctk
from config import settings
from core.auth.auth_service import authenticate_user
from core.database.connection import test_connection
from modules.dashboard.main_window import MainWindow


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class JCAPTheme:
    PRIMARY_BLUE = "#0D47A1"
    PRIMARY_BLUE_LIGHT = "#1976D2"
    DARK_BLUE = "#0A2E63"
    RED = "#E53935"
    GREEN = "#43A047"
    BG_LIGHT = "#F5F7FA"
    CARD_BG = "#FFFFFF"
    TEXT_MUTED = "#607D8B"


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        try:
            self.state("zoomed")
        except Exception:
            pass

        self.build_login_ui()

    def build_login_ui(self):
        self.configure(fg_color=JCAPTheme.BG_LIGHT)

        main_frame = ctk.CTkFrame(self, fg_color=JCAPTheme.BG_LIGHT, corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        login_card = ctk.CTkFrame(
            main_frame,
            width=440,
            height=500,
            fg_color=JCAPTheme.CARD_BG,
            corner_radius=20
        )
        login_card.place(relx=0.5, rely=0.5, anchor="center")

        logo_box = ctk.CTkFrame(
            login_card,
            width=80,
            height=80,
            fg_color=JCAPTheme.PRIMARY_BLUE,
            corner_radius=18
        )
        logo_box.pack(pady=(35, 15))

        logo_text = ctk.CTkLabel(
            logo_box,
            text="JCAP",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(
            login_card,
            text="JCAP CONSTRUCTION SUITE",
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.DARK_BLUE
        )
        title.pack(pady=(5, 5))

        subtitle = ctk.CTkLabel(
            login_card,
            text="Construction Procurement System",
            font=("Segoe UI", 14),
            text_color=JCAPTheme.TEXT_MUTED
        )
        subtitle.pack(pady=(0, 30))

        self.username_entry = ctk.CTkEntry(
            login_card,
            width=320,
            height=42,
            placeholder_text="Username",
            font=("Segoe UI", 13),
            corner_radius=8
        )
        self.username_entry.pack(pady=8)

        self.password_entry = ctk.CTkEntry(
            login_card,
            width=320,
            height=42,
            placeholder_text="Password",
            show="*",
            font=("Segoe UI", 13),
            corner_radius=8
        )
        self.password_entry.pack(pady=8)

        login_button = ctk.CTkButton(
            login_card,
            text="LOGIN",
            width=320,
            height=44,
            font=("Segoe UI", 13, "bold"),
            fg_color=JCAPTheme.PRIMARY_BLUE,
            hover_color=JCAPTheme.DARK_BLUE,
            corner_radius=8,
            command=self.login
        )
        login_button.pack(pady=(20, 25))

        success, _ = test_connection()
        status_text = "PostgreSQL Connected ✔" if success else "Database Connection Failed ✖"

        status_label = ctk.CTkLabel(
            login_card,
            text=status_text,
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.GREEN if success else JCAPTheme.RED
        )
        status_label.pack(pady=5)

        version_label = ctk.CTkLabel(
            login_card,
            text=f"Version {settings.APP_VERSION}",
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_MUTED
        )
        version_label.pack()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        success, message, user = authenticate_user(username, password)

        if success:
            self.destroy()
            main_window = MainWindow(user)
            main_window.mainloop()
        else:
            print("Login failed:", message)