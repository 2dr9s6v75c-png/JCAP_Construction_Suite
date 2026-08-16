from __future__ import annotations

import customtkinter as ctk

from core.documents.smb_authentication_service import (
    SMBAuthenticationError,
    SMBAuthenticationService,
)


class SMBLoginDialog(ctk.CTkToplevel):
    """
    JCAP Synology SMB authentication dialog.

    The password exists only for the lifetime of this dialog.
    It is never stored by the dialog itself.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.result = False

        self.title("Synology NAS Access Required")
        self.geometry("470x390")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.username_var = ctk.StringVar(value="")
        self.password_var = ctk.StringVar(value="")
        self.remember_var = ctk.BooleanVar(value=True)
        self.status_var = ctk.StringVar(value="")

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self.after(100, self._finish_setup)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self,
            text="Synology NAS Access Required",
            font=("Segoe UI", 20, "bold"),
            text_color="#0A2E63",
        )
        title_label.grid(
            row=0,
            column=0,
            padx=30,
            pady=(25, 8),
            sticky="w",
        )

        description = ctk.CTkLabel(
            self,
            text=(
                "JCAP needs access to the company shared folder.\n"
                "Enter your Synology account credentials."
            ),
            font=("Segoe UI", 12),
            justify="left",
            anchor="w",
            text_color="#455A64",
        )
        description.grid(
            row=1,
            column=0,
            padx=30,
            pady=(0, 18),
            sticky="w",
        )

        form = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        form.grid(
            row=2,
            column=0,
            padx=30,
            sticky="ew",
        )
        form.grid_columnconfigure(0, weight=1)

        username_label = ctk.CTkLabel(
            form,
            text="Synology Username",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        username_label.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 5),
        )

        self.username_entry = ctk.CTkEntry(
            form,
            textvariable=self.username_var,
            height=38,
            font=("Segoe UI", 12),
            placeholder_text="Enter Synology username",
        )
        self.username_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )

        password_label = ctk.CTkLabel(
            form,
            text="Password",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        password_label.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 5),
        )

        self.password_entry = ctk.CTkEntry(
            form,
            textvariable=self.password_var,
            height=38,
            font=("Segoe UI", 12),
            placeholder_text="Enter Synology password",
            show="●",
        )
        self.password_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        self.remember_checkbox = ctk.CTkCheckBox(
            form,
            text="Remember on this computer",
            variable=self.remember_var,
            onvalue=True,
            offvalue=False,
            font=("Segoe UI", 11),
        )
        self.remember_checkbox.grid(
            row=4,
            column=0,
            sticky="w",
            pady=(2, 8),
        )

        self.status_label = ctk.CTkLabel(
            form,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            text_color="#C62828",
            justify="left",
            anchor="w",
            wraplength=400,
        )
        self.status_label.grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(0, 5),
        )

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        button_frame.grid(
            row=3,
            column=0,
            padx=30,
            pady=(12, 25),
            sticky="e",
        )

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            height=36,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self._cancel,
        )
        self.cancel_button.grid(
            row=0,
            column=0,
            padx=(0, 8),
        )

        self.connect_button = ctk.CTkButton(
            button_frame,
            text="Connect",
            width=110,
            height=36,
            fg_color="#0D47A1",
            hover_color="#0A2E63",
            command=self._connect,
        )
        self.connect_button.grid(
            row=0,
            column=1,
        )

        self.username_entry.bind(
            "<Return>",
            lambda _event: self.password_entry.focus_set(),
        )

        self.password_entry.bind(
            "<Return>",
            lambda _event: self._connect(),
        )

        self.bind(
            "<Escape>",
            lambda _event: self._cancel(),
        )

    def _finish_setup(self):
        try:
            self.update_idletasks()

            parent = self.master

            if parent and parent.winfo_exists():
                parent.update_idletasks()

                parent_x = parent.winfo_rootx()
                parent_y = parent.winfo_rooty()
                parent_width = parent.winfo_width()
                parent_height = parent.winfo_height()

                width = self.winfo_width()
                height = self.winfo_height()

                x = parent_x + max(
                    0,
                    (parent_width - width) // 2,
                )
                y = parent_y + max(
                    0,
                    (parent_height - height) // 2,
                )

                self.geometry(f"+{x}+{y}")

        except Exception:
            pass

        self.username_entry.focus_set()

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"

        self.username_entry.configure(state=state)
        self.password_entry.configure(state=state)
        self.remember_checkbox.configure(state=state)
        self.cancel_button.configure(state=state)
        self.connect_button.configure(state=state)

        self.connect_button.configure(
            text="Connecting..." if busy else "Connect"
        )

        self.update_idletasks()

    def _connect(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username:
            self.status_var.set(
                "Enter your Synology username."
            )
            self.username_entry.focus_set()
            return

        if not password:
            self.status_var.set(
                "Enter your Synology password."
            )
            self.password_entry.focus_set()
            return

        self.status_var.set("")
        self._set_busy(True)

        try:
            SMBAuthenticationService.authenticate(
                username=username,
                password=password,
                remember=bool(self.remember_var.get()),
            )

            self.result = True

            # Remove the password from the Tk variable before
            # destroying the dialog.
            self.password_var.set("")

            self.grab_release()
            self.destroy()

        except SMBAuthenticationError as error:
            self.password_var.set("")
            self.status_var.set(str(error))
            self._set_busy(False)
            self.password_entry.focus_set()

        except Exception:
            self.password_var.set("")
            self.status_var.set(
                "Unable to connect to the Synology NAS. "
                "Check the network connection and try again."
            )
            self._set_busy(False)
            self.password_entry.focus_set()

    def _cancel(self):
        self.result = False
        self.password_var.set("")

        try:
            self.grab_release()
        except Exception:
            pass

        self.destroy()

    @classmethod
    def request_access(cls, parent) -> bool:
        """
        Return True when SMB access is already available or when the
        user successfully authenticates.

        Return False when the user cancels authentication.
        """

        if SMBAuthenticationService.has_access():
            return True

        dialog = cls(parent)
        parent.wait_window(dialog)

        return bool(dialog.result)