from datetime import datetime

import customtkinter as ctk

from core.clarifications.clarification_service import (
    ClarificationService,
)
from core.notifications.notification_service import (
    NotificationService,
)
from core.security.permissions import PermissionService
from core.theme import JCAPTheme


class ClarificationDetailsView(ctk.CTkFrame):
    """
    Supplier Clarification conversation and workflow view.

    The UI exposes actions based on:
    - RBAC permissions
    - Clarification workflow status

    Final workflow enforcement remains inside ClarificationService.
    """

    def __init__(
        self,
        parent,
        user,
        clarification_id,
        on_back=None,
        on_status_change=None,
    ):
        super().__init__(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=0,
        )

        self.user = user
        self.clarification_id = clarification_id
        self.on_back = on_back
        self.on_status_change = on_status_change

        self.clarification = None
        self.messages = []

        self.action_textbox = None
        self.action_button = None
        self.secondary_action_button = None

        self.load_data()
        self.build_ui()

    # ============================================================
    # DATA
    # ============================================================

    def load_data(self):
        self.clarification = (
            ClarificationService.get_clarification(
                self.clarification_id
            )
        )

        if not self.clarification:
            raise ValueError(
                "Supplier clarification was not found."
            )

        self.messages = (
            ClarificationService.get_messages(
                self.clarification_id
            )
        )

    def reload_view(self):
        self.load_data()

        for widget in self.winfo_children():
            widget.destroy()

        self.action_textbox = None
        self.action_button = None
        self.secondary_action_button = None

        self.build_ui()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            2,
            weight=1,
        )

        self.build_header()
        self.build_summary()
        self.build_conversation()

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

        header.grid_columnconfigure(
            0,
            weight=1,
        )

        title_block = ctk.CTkFrame(
            header,
            fg_color="transparent",
        )

        title_block.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=18,
        )

        ctk.CTkLabel(
            title_block,
            text=self.clarification.get(
                "subject",
                "Supplier Clarification",
            ),
            font=("Segoe UI", 24, "bold"),
            text_color=JCAPTheme.TEXT,
        ).pack(
            anchor="w"
        )

        mr_number = (
            self.clarification.get(
                "mr_number"
            )
            or self.clarification.get(
                "request_no"
            )
            or ""
        )

        ctk.CTkLabel(
            title_block,
            text=(
                f"Supplier Clarification  |  "
                f"{mr_number}"
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ctk.CTkButton(
            header,
            text="Back",
            width=100,
            height=36,
            fg_color=JCAPTheme.BACK,
            hover_color=JCAPTheme.BACK_HOVER,
            command=self.handle_back,
        ).grid(
            row=0,
            column=1,
            padx=20,
            pady=18,
        )

    def build_summary(self):
        summary = ctk.CTkFrame(
            self,
            fg_color=JCAPTheme.CARD,
            corner_radius=14,
        )

        summary.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=10,
        )

        for column in range(4):
            summary.grid_columnconfigure(
                column,
                weight=1,
            )

        self.add_summary_item(
            summary,
            0,
            "Supplier",
            (
                self.clarification.get(
                    "supplier_name"
                )
                or "Not specified"
            ),
        )

        self.add_summary_item(
            summary,
            1,
            "Assigned To",
            (
                self.clarification.get(
                    "assigned_full_name"
                )
                or self.clarification.get(
                    "assigned_to"
                )
                or "Not assigned"
            ),
        )

        self.add_summary_item(
            summary,
            2,
            "Status",
            self.clarification.get(
                "status",
                "",
            ),
        )

        self.add_summary_item(
            summary,
            3,
            "Supplier Reference",
            (
                self.clarification.get(
                    "supplier_reference"
                )
                or "Not specified"
            ),
        )

    def add_summary_item(
        self,
        parent,
        column,
        label,
        value,
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=10,
        )

        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=8,
            pady=12,
        )

        ctk.CTkLabel(
            card,
            text=label,
            font=("Segoe UI", 11, "bold"),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).pack(
            pady=(12, 3),
        )

        ctk.CTkLabel(
            card,
            text=str(
                value or ""
            ),
            font=("Segoe UI", 13, "bold"),
            text_color=JCAPTheme.TEXT,
            wraplength=260,
        ).pack(
            pady=(0, 12),
            padx=10,
        )

    def build_conversation(self):
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

        workspace.grid_columnconfigure(
            0,
            weight=1,
        )

        workspace.grid_rowconfigure(
            0,
            weight=1,
        )

        conversation = ctk.CTkScrollableFrame(
            workspace,
            fg_color=JCAPTheme.BACKGROUND,
            corner_radius=10,
        )

        conversation.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=15,
            pady=(15, 8),
        )

        conversation.grid_columnconfigure(
            0,
            weight=1,
        )

        if not self.messages:
            ctk.CTkLabel(
                conversation,
                text=(
                    "No clarification messages recorded."
                ),
                font=("Segoe UI", 14),
                text_color=JCAPTheme.TEXT_SECONDARY,
            ).grid(
                row=0,
                column=0,
                pady=50,
            )

        else:
            for row, message in enumerate(
                self.messages
            ):
                self.build_message_card(
                    conversation,
                    message,
                    row,
                )

        action_frame = ctk.CTkFrame(
            workspace,
            fg_color="transparent",
        )

        action_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(8, 15),
        )

        action_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        self.build_workflow_actions(
            action_frame
        )

    # ============================================================
    # MESSAGE CARDS
    # ============================================================

    def build_message_card(
        self,
        parent,
        message,
        row,
    ):
        message_type = message.get(
            "message_type",
            "",
        )

        card = ctk.CTkFrame(
            parent,
            fg_color=JCAPTheme.CARD,
            corner_radius=12,
        )

        card.grid(
            row=row,
            column=0,
            sticky="ew",
            padx=8,
            pady=7,
        )

        card.grid_columnconfigure(
            0,
            weight=1,
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )

        top.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(14, 5),
        )

        top.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            top,
            text=message_type,
            font=("Segoe UI", 13, "bold"),
            text_color=self.get_message_type_color(
                message_type
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ctk.CTkLabel(
            top,
            text=self.format_datetime(
                message.get(
                    "created_at"
                )
            ),
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        ctk.CTkLabel(
            card,
            text=message.get(
                "message_text",
                "",
            ),
            font=("Segoe UI", 13),
            text_color=JCAPTheme.TEXT,
            justify="left",
            anchor="w",
            wraplength=1050,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
            pady=8,
        )

        sender = (
            message.get(
                "sent_by_full_name"
            )
            or message.get(
                "sent_by_username"
            )
            or "System"
        )

        attachment_count = int(
            message.get(
                "attachment_count",
                0,
            )
            or 0
        )

        footer_text = (
            f"By: {sender}"
        )

        if attachment_count:
            footer_text += (
                f"   |   "
                f"{attachment_count} attachment"
            )

            if attachment_count != 1:
                footer_text += "s"

        ctk.CTkLabel(
            card,
            text=footer_text,
            font=("Segoe UI", 11),
            text_color=JCAPTheme.TEXT_SECONDARY,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=16,
            pady=(2, 14),
        )

    # ============================================================
    # WORKFLOW ACTIONS
    # ============================================================

    def build_workflow_actions(
        self,
        parent,
    ):
        status = self.clarification.get(
            "status"
        )

        if (
            status
            == ClarificationService.STATUS_AWAITING_ENGINEERING
            and self.can_submit_engineering_response()
        ):
            self.build_engineering_response_action(
                parent
            )
            return

        if (
            status
            == ClarificationService.STATUS_RESPONSE_READY
            and self.can_forward_to_supplier()
        ):
            self.build_forward_action(
                parent
            )
            return

        if (
            status
            == ClarificationService.STATUS_FORWARDED
            and (
                self.can_record_supplier_follow_up()
                or self.can_resolve_clarification()
            )
        ):
            self.build_forwarded_actions(
                parent
            )
            return

        self.build_read_only_status(
            parent
        )

    def build_engineering_response_action(
        self,
        parent,
    ):
        self.build_action_title(
            parent,
            "Engineering Response",
            (
                "Provide the technical response requested "
                "by Purchasing."
            ),
        )

        self.action_textbox = ctk.CTkTextbox(
            parent,
            height=120,
        )

        self.action_textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(8, 10),
        )

        self.action_button = ctk.CTkButton(
            parent,
            text="Submit Engineering Response",
            width=220,
            height=38,
            fg_color=JCAPTheme.SAVE,
            hover_color=JCAPTheme.SAVE_HOVER,
            command=self.submit_engineering_response,
        )

        self.action_button.grid(
            row=2,
            column=0,
            sticky="e",
        )

    def build_forward_action(
        self,
        parent,
    ):
        self.build_action_title(
            parent,
            "Engineering Response Ready",
            (
                "Review the Engineering response, then "
                "record that it was forwarded to the supplier."
            ),
        )

        self.action_textbox = ctk.CTkTextbox(
            parent,
            height=90,
        )

        self.action_textbox.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(8, 10),
        )

        self.action_textbox.insert(
            "1.0",
            (
                "Engineering response forwarded "
                "to supplier."
            ),
        )

        self.action_button = ctk.CTkButton(
            parent,
            text="Mark Forwarded to Supplier",
            width=220,
            height=38,
            fg_color=JCAPTheme.APPROVE,
            hover_color=JCAPTheme.APPROVE_HOVER,
            command=self.mark_forwarded_to_supplier,
        )

        self.action_button.grid(
            row=2,
            column=0,
            sticky="e",
        )

    def build_forwarded_actions(
        self,
        parent,
    ):
        can_record_follow_up = (
            self.can_record_supplier_follow_up()
        )

        can_resolve = (
            self.can_resolve_clarification()
        )

        self.build_action_title(
            parent,
            "Supplier Response",
            (
                "Record a supplier follow-up question, "
                "or resolve the clarification when no "
                "further information is needed."
            ),
        )

        if can_record_follow_up:
            self.action_textbox = ctk.CTkTextbox(
                parent,
                height=100,
            )

            self.action_textbox.grid(
                row=1,
                column=0,
                sticky="ew",
                pady=(8, 10),
            )

        buttons = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        buttons.grid(
            row=2,
            column=0,
            sticky="e",
        )

        if can_resolve:
            self.secondary_action_button = (
                ctk.CTkButton(
                    buttons,
                    text="Resolve Clarification",
                    width=180,
                    height=38,
                    fg_color=JCAPTheme.APPROVE,
                    hover_color=(
                        JCAPTheme.APPROVE_HOVER
                    ),
                    command=self.resolve_clarification,
                )
            )

            self.secondary_action_button.pack(
                side="right",
                padx=(8, 0),
            )

        if can_record_follow_up:
            self.action_button = ctk.CTkButton(
                buttons,
                text="Record Supplier Follow-up",
                width=200,
                height=38,
                fg_color=JCAPTheme.PRIMARY_BLUE,
                hover_color=(
                    JCAPTheme.PRIMARY_BLUE_HOVER
                ),
                command=self.record_supplier_follow_up,
            )

            self.action_button.pack(
                side="right",
            )

    def build_read_only_status(
        self,
        parent,
    ):
        status = self.clarification.get(
            "status",
            "",
        )

        self.build_action_title(
            parent,
            status or "Clarification",
            self.get_status_message(
                status
            ),
        )

    def build_action_title(
        self,
        parent,
        title,
        description,
    ):
        header = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 15, "bold"),
            text_color=JCAPTheme.DARK_BLUE,
        ).pack(
            anchor="w",
        )

        ctk.CTkLabel(
            header,
            text=description,
            font=("Segoe UI", 12),
            text_color=JCAPTheme.TEXT_SECONDARY,
            justify="left",
            wraplength=1000,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

    # ============================================================
    # WORKFLOW COMMANDS
    # ============================================================

    def submit_engineering_response(self):
        response_text = self.get_action_text()

        if not response_text:
            NotificationService.validation(
                [
                    "Engineering response is required."
                ]
            )
            return

        confirmed = NotificationService.confirm(
            (
                "Submit this Engineering response?\n\n"
                "Purchasing will be notified that the "
                "technical response is ready."
            ),
            title="Submit Engineering Response",
        )

        if not confirmed:
            return

        try:
            (
                ClarificationService
                .submit_engineering_response(
                    clarification_id=(
                        self.clarification_id
                    ),
                    response_text=response_text,
                    current_user=self.user,
                )
            )

            NotificationService.success(
                (
                    "Engineering response was submitted "
                    "successfully.\n\n"
                    "Purchasing has been notified."
                ),
                title="Response Submitted",
            )

            self.handle_workflow_change()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to submit the "
                    "Engineering response."
                ),
                title="Response Failed",
                error=error,
            )

    def mark_forwarded_to_supplier(self):
        note = self.get_action_text()

        confirmed = NotificationService.confirm(
            (
                "Confirm that the Engineering response "
                "was forwarded to the supplier?"
            ),
            title="Forwarded to Supplier",
        )

        if not confirmed:
            return

        try:
            (
                ClarificationService
                .mark_forwarded_to_supplier(
                    clarification_id=(
                        self.clarification_id
                    ),
                    current_user=self.user,
                    note=note or None,
                )
            )

            NotificationService.success(
                (
                    "Clarification was marked as forwarded "
                    "to the supplier."
                ),
                title="Supplier Updated",
            )

            self.handle_workflow_change()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to update the clarification."
                ),
                title="Forwarding Failed",
                error=error,
            )

    def record_supplier_follow_up(self):
        follow_up_text = self.get_action_text()

        if not follow_up_text:
            NotificationService.validation(
                [
                    (
                        "Supplier follow-up question "
                        "is required."
                    )
                ]
            )
            return

        confirmed = NotificationService.confirm(
            (
                "Record this supplier follow-up and notify "
                "the assigned Project Engineer?"
            ),
            title="Record Supplier Follow-up",
        )

        if not confirmed:
            return

        try:
            (
                ClarificationService
                .record_supplier_follow_up(
                    clarification_id=(
                        self.clarification_id
                    ),
                    follow_up_text=follow_up_text,
                    current_user=self.user,
                )
            )

            NotificationService.success(
                (
                    "Supplier follow-up was recorded.\n\n"
                    "The assigned Project Engineer "
                    "has been notified."
                ),
                title="Follow-up Recorded",
            )

            self.handle_workflow_change()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to record the "
                    "supplier follow-up."
                ),
                title="Follow-up Failed",
                error=error,
            )

    def resolve_clarification(self):
        confirmed = NotificationService.confirm(
            (
                "Resolve this supplier clarification?\n\n"
                "Use this only when no further supplier or "
                "Engineering response is required."
            ),
            title="Resolve Clarification",
        )

        if not confirmed:
            return

        try:
            ClarificationService.resolve_clarification(
                clarification_id=self.clarification_id,
                current_user=self.user,
            )

            NotificationService.success(
                (
                    "Supplier clarification was resolved."
                ),
                title="Clarification Resolved",
            )

            self.handle_workflow_change()

        except Exception as error:
            NotificationService.error(
                (
                    "Unable to resolve the clarification."
                ),
                title="Resolve Failed",
                error=error,
            )

    # ============================================================
    # PERMISSION HELPERS
    # ============================================================

    def can_submit_engineering_response(self):
        return (
            PermissionService.has_permission(
                self.user,
                (
                    "material_requests."
                    "clarifications.reply"
                ),
            )
            and self.clarification.get(
                "assigned_to"
            )
            == str(
                self.user.get(
                    "id"
                )
            )
        )

    def can_forward_to_supplier(self):
        return PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.forward"
            ),
        )

    def can_record_supplier_follow_up(self):
        return PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        )

    def can_resolve_clarification(self):
        return PermissionService.has_permission(
            self.user,
            (
                "material_requests."
                "clarifications.resolve"
            ),
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def get_action_text(self):
        if not self.action_textbox:
            return ""

        return self.action_textbox.get(
            "1.0",
            "end",
        ).strip()

    def handle_workflow_change(self):
        if self.on_status_change:
            self.on_status_change(
                self.clarification_id
            )

        self.reload_view()

    def handle_back(self):
        if self.on_back:
            self.on_back()

    @staticmethod
    def get_message_type_color(
        message_type,
    ):
        colors = {
            "Supplier Question": "#E53935",
            "Engineering Response": "#43A047",
            "Purchasing Note": "#0D47A1",
            "Supplier Follow-up": "#FB8C00",
            "System": "#607D8B",
        }

        return colors.get(
            str(
                message_type or ""
            ),
            JCAPTheme.TEXT_SECONDARY,
        )

    @staticmethod
    def get_status_message(
        status,
    ):
        messages = {
            "Awaiting Engineering Response": (
                "The assigned Project Engineer must submit "
                "a technical response."
            ),
            "Response Ready": (
                "Engineering has submitted a response. "
                "Purchasing must review and forward it."
            ),
            "Forwarded to Supplier": (
                "The response has been forwarded "
                "to the supplier."
            ),
            "Resolved": (
                "This supplier clarification is complete."
            ),
            "Cancelled": (
                "This supplier clarification was cancelled."
            ),
        }

        return messages.get(
            str(
                status or ""
            ),
            (
                "No workflow action is currently available."
            ),
        )

    @staticmethod
    def format_datetime(
        value,
    ):
        if isinstance(
            value,
            datetime,
        ):
            return value.strftime(
                "%d %b %Y %I:%M %p"
            )

        return str(
            value or ""
        )