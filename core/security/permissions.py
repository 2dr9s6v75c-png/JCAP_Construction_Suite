from core.database.repositories.permission_repository import (
    PermissionRepository,
)


class PermissionService:
    """
    Centralized permission service for the JCAP Construction Suite.

    RBAC v1 uses database-managed role permissions.

    Permission flow:

        User
            ↓
        role_id
            ↓
        core.role_permissions
            ↓
        core.permissions

    Legacy role-based compatibility is temporarily retained for
    accounts or sessions that do not yet contain role_id.
    """

    # ============================================================
    # LEGACY ROLE NAMES
    # ============================================================

    ADMINISTRATOR = "administrator"
    SYSTEM_ADMINISTRATOR = "system administrator"

    PURCHASING_MANAGER = "purchasing manager"
    PURCHASING_OFFICER = "purchasing officer"

    PROJECT_ENGINEER = "project engineer"
    PROJECT_MANAGER = "project manager"

    ACCOUNTING = "accounting"
    ACCOUNTING_PERSONNEL = "accounting personnel"

    WAREHOUSE = "warehouse"
    WAREHOUSE_PERSONNEL = "warehouse personnel"

    EXECUTIVE_MANAGEMENT = "executive / management"

    VIEWER = "viewer"
    VIEWER_AUDITOR = "viewer / auditor"

    # ============================================================
    # LEGACY PERMISSION ALIASES
    # ============================================================

    PERMISSION_ALIASES = {
        # --------------------------------------------------------
        # MATERIAL REQUEST LEGACY NAMES
        # --------------------------------------------------------

        "material_request.view": (
            "material_requests.view"
        ),
        "material_request.create": (
            "material_requests.create"
        ),
        "material_request.edit": (
            "material_requests.edit"
        ),
        "material_request.accept": (
            "material_requests.accept"
        ),
        "material_request.process": (
            "material_requests.process"
        ),
        "material_request.assign": (
            "material_requests.assign"
        ),
        "material_request.reassign": (
            "material_requests.reassign"
        ),
        "material_request.archive": (
            "material_requests.archive"
        ),
        "material_request.restore": (
            "material_requests.restore"
        ),
        "material_request.force_unlock": (
            "material_requests.force_unlock"
        ),

        # --------------------------------------------------------
        # OLD ADMINISTRATION PERMISSION NAMES
        # --------------------------------------------------------

        "users.manage": (
            "administration.users.manage"
        ),
        "roles.manage": (
            "administration.roles.manage"
        ),
        "departments.manage": (
            "administration.departments.manage"
        ),
        "job_titles.manage": (
            "administration.job_titles.manage"
        ),
        "permissions.manage": (
            "administration.roles.manage"
        ),
        "audit_logs.view": (
            "administration.audit.view"
        ),
    }

    # ============================================================
    # ROLE HELPERS
    # ============================================================

    @classmethod
    def normalize_role(
        cls,
        user: dict | None,
    ) -> str:
        if not user:
            return ""

        role_name = (
            user.get("role_name")
            or user.get("role")
            or user.get("legacy_role")
            or ""
        )

        return str(role_name).strip().lower()

    @classmethod
    def has_role(
        cls,
        user: dict | None,
        *roles: str,
    ) -> bool:
        user_role = cls.normalize_role(
            user
        )

        allowed_roles = {
            str(role).strip().lower()
            for role in roles
        }

        return user_role in allowed_roles

    @classmethod
    def is_administrator(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.SYSTEM_ADMINISTRATOR,
        )

    # ============================================================
    # DATABASE-DRIVEN PERMISSION CORE
    # ============================================================

    @classmethod
    def normalize_permission_name(
        cls,
        permission_name: str,
    ) -> str:
        permission_name = str(
            permission_name or ""
        ).strip().lower()

        if not permission_name:
            return ""

        return cls.PERMISSION_ALIASES.get(
            permission_name,
            permission_name,
        )

    @classmethod
    def get_user_permissions(
        cls,
        user: dict | None,
    ) -> set[str]:
        """
        Return all database permissions assigned to the user's role.

        Returns an empty set when:
        - no user is supplied
        - no role_id exists
        - the permission query cannot be resolved

        Legacy compatibility is handled by capability methods below.
        """

        if not user:
            return set()

        role_id = user.get(
            "role_id"
        )

        if not role_id:
            return set()

        permissions = (
            PermissionRepository.get_by_role(
                role_id
            )
        )

        return {
            cls.normalize_permission_name(
                permission["permission_name"]
            )
            for permission in permissions
            if permission.get(
                "permission_name"
            )
        }

    @classmethod
    def has_permission(
        cls,
        user: dict | None,
        permission_name: str,
    ) -> bool:
        """
        Check one RBAC permission.

        Database role permissions are authoritative when role_id exists.

        Legacy role fallback is only used for old sessions or unmigrated
        user dictionaries without role_id.
        """

        if not user:
            return False

        permission_name = (
            cls.normalize_permission_name(
                permission_name
            )
        )

        if not permission_name:
            return False

        role_id = user.get(
            "role_id"
        )

        if role_id:
            return (
                PermissionRepository
                .role_has_permission_name(
                    role_id,
                    permission_name,
                )
            )

        return cls._legacy_has_permission(
            user,
            permission_name,
        )

    @classmethod
    def has_any_permission(
        cls,
        user: dict | None,
        permission_names,
    ) -> bool:
        permission_names = list(
            permission_names or []
        )

        if not permission_names:
            return False

        return any(
            cls.has_permission(
                user,
                permission_name,
            )
            for permission_name in permission_names
        )

    @classmethod
    def has_all_permissions(
        cls,
        user: dict | None,
        permission_names,
    ) -> bool:
        permission_names = list(
            permission_names or []
        )

        if not permission_names:
            return True

        return all(
            cls.has_permission(
                user,
                permission_name,
            )
            for permission_name in permission_names
        )

    # ============================================================
    # MATERIAL REQUEST PERMISSIONS
    # ============================================================

    @classmethod
    def can_view_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.view",
        )

    @classmethod
    def can_create_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.create",
        )

    @classmethod
    def can_edit_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.edit",
        )

    @classmethod
    def can_accept_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.accept",
        )

    @classmethod
    def can_process_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.process",
        )

    @classmethod
    def can_assign_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.assign",
        )

    @classmethod
    def can_reassign_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.reassign",
        )

    @classmethod
    def can_archive_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.archive",
        )

    @classmethod
    def can_restore_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.restore",
        )

    @classmethod
    def can_force_unlock_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.force_unlock",
        )

    # ============================================================
    # MATERIAL REQUEST CLARIFICATIONS
    # ============================================================

    @classmethod
    def can_view_material_request_clarifications(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.view",
        )

    @classmethod
    def can_add_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.add",
        )

    @classmethod
    def can_reply_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.reply",
        )

    @classmethod
    def can_request_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.request",
        )

    @classmethod
    def can_record_supplier_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            (
                "material_requests."
                "clarifications.record_supplier"
            ),
        )

    @classmethod
    def can_forward_clarification_to_supplier(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.forward",
        )

    @classmethod
    def can_resolve_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.resolve",
        )

    @classmethod
    def can_reopen_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.reopen",
        )

    @classmethod
    def can_cancel_material_request_clarification(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.clarifications.cancel",
        )

    # ============================================================
    # MATERIAL REQUEST DOCUMENTS
    # ============================================================

    @classmethod
    def can_view_material_request_documents(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.documents.view",
        )

    @classmethod
    def can_upload_material_request_documents(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.documents.upload",
        )

    @classmethod
    def can_delete_own_material_request_documents(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.documents.delete_own",
        )

    @classmethod
    def can_acknowledge_material_request_documents(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.documents.acknowledge",
        )

    # ============================================================
    # MATERIAL REQUEST AMENDMENTS
    # ============================================================

    @classmethod
    def can_view_material_request_amendments(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.amendments.view",
        )

    @classmethod
    def can_request_material_request_amendment(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.amendments.request",
        )

    @classmethod
    def can_review_material_request_amendment(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.amendments.review",
        )

    @classmethod
    def can_approve_material_request_amendment(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.amendments.approve",
        )

    @classmethod
    def can_reject_material_request_amendment(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.amendments.reject",
        )

    @classmethod
    def can_view_material_request_revisions(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_requests.revisions.view",
        )

    # ============================================================
    # USER ADMINISTRATION
    # ============================================================

    @classmethod
    def can_manage_users(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "administration.users.manage",
        )

    @classmethod
    def can_manage_roles(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "administration.roles.manage",
        )

    @classmethod
    def can_manage_departments(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "administration.departments.manage",
        )

    @classmethod
    def can_manage_job_titles(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "administration.job_titles.manage",
        )

    @classmethod
    def can_view_audit_logs(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "administration.audit.view",
        )

    # ============================================================
    # SUPPLIER RFQ
    # ============================================================

    @classmethod
    def can_view_supplier_rfq(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "supplier_rfq.view",
        )

    @classmethod
    def can_manage_supplier_quotations(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_any_permission(
            user,
            (
                "supplier_rfq.create",
                "supplier_rfq.edit",
                "supplier_rfq.manage",
            ),
        )

    # ============================================================
    # MATERIAL COSTING
    # ============================================================

    @classmethod
    def can_view_material_costing(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "material_costing.view",
        )

    @classmethod
    def can_manage_material_costing(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_any_permission(
            user,
            (
                "material_costing.create",
                "material_costing.edit",
                "material_costing.manage",
            ),
        )

    # ============================================================
    # PURCHASE ORDERS
    # ============================================================

    @classmethod
    def can_view_purchase_orders(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "purchase_orders.view",
        )

    @classmethod
    def can_manage_purchase_orders(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_any_permission(
            user,
            (
                "purchase_orders.create",
                "purchase_orders.edit",
                "purchase_orders.monitor",
            ),
        )

    @classmethod
    def can_approve_purchase_orders(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "purchase_orders.approve",
        )

    # ============================================================
    # INVENTORY
    # ============================================================

    @classmethod
    def can_view_inventory(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "inventory.view",
        )

    @classmethod
    def can_manage_inventory(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "inventory.manage",
        )

    # ============================================================
    # INVOICE MONITORING
    # ============================================================

    @classmethod
    def can_view_invoices(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "invoice_monitoring.view",
        )

    @classmethod
    def can_manage_invoices(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "invoice_monitoring.manage",
        )

    # ============================================================
    # REPORTS
    # ============================================================

    @classmethod
    def can_view_reports(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "reports.view",
        )

    # ============================================================
    # SYSTEM SETTINGS
    # ============================================================

    @classmethod
    def can_manage_settings(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_permission(
            user,
            "settings.manage",
        )

    # ============================================================
    # LEGACY FALLBACK
    # ============================================================

    @classmethod
    def _legacy_has_permission(
        cls,
        user: dict | None,
        permission_name: str,
    ) -> bool:
        """
        Temporary fallback for old session dictionaries without role_id.

        This must not replace database RBAC for migrated users.
        """

        permission_name = (
            cls.normalize_permission_name(
                permission_name
            )
        )

        if cls.is_administrator(user):
            return True

        role = cls.normalize_role(
            user
        )

        legacy_permissions = {
            cls.PURCHASING_MANAGER: {
                "material_requests.view",
                "material_requests.create",
                "material_requests.edit",
                "material_requests.accept",
                "material_requests.process",
                "material_requests.assign",
                "material_requests.reassign",
                "material_requests.archive",
                "material_requests.restore",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                (
                    "material_requests."
                    "clarifications.add"
                ),
                (
                    "material_requests."
                    "clarifications.reply"
                ),
                (
                    "material_requests."
                    "clarifications.request"
                ),
                (
                    "material_requests."
                    "clarifications.record_supplier"
                ),
                (
                    "material_requests."
                    "clarifications.forward"
                ),
                (
                    "material_requests."
                    "clarifications.resolve"
                ),
                (
                    "material_requests."
                    "clarifications.reopen"
                ),
                (
                    "material_requests."
                    "clarifications.cancel"
                ),
                "supplier_rfq.view",
                "supplier_rfq.create",
                "supplier_rfq.edit",
                "supplier_rfq.manage",
                "supplier_rfq.close",
                "material_costing.view",
                "material_costing.create",
                "material_costing.edit",
                "material_costing.manage",
                "purchase_orders.view",
                "purchase_orders.create",
                "purchase_orders.edit",
                "purchase_orders.monitor",
                "inventory.view",
                "invoice_monitoring.view",
                "reports.view",
                "reports.purchasing.view",
                "administration.audit.view",
            },

            cls.PURCHASING_OFFICER: {
                "material_requests.view",
                "material_requests.edit",
                "material_requests.accept",
                "material_requests.process",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                (
                    "material_requests."
                    "clarifications.add"
                ),
                (
                    "material_requests."
                    "clarifications.reply"
                ),
                (
                    "material_requests."
                    "clarifications.request"
                ),
                (
                    "material_requests."
                    "clarifications.record_supplier"
                ),
                (
                    "material_requests."
                    "clarifications.forward"
                ),
                (
                    "material_requests."
                    "clarifications.resolve"
                ),
                (
                    "material_requests."
                    "clarifications.reopen"
                ),
                "supplier_rfq.view",
                "supplier_rfq.create",
                "supplier_rfq.edit",
                "supplier_rfq.manage",
                "material_costing.view",
                "material_costing.create",
                "material_costing.edit",
                "material_costing.manage",
                "purchase_orders.view",
                "purchase_orders.create",
                "purchase_orders.edit",
                "purchase_orders.monitor",
                "inventory.view",
                "invoice_monitoring.view",
                "reports.view",
                "reports.purchasing.view",
            },

            cls.PROJECT_ENGINEER: {
                "material_requests.view",
                "material_requests.create",
                "material_requests.edit",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                (
                    "material_requests."
                    "clarifications.add"
                ),
                (
                    "material_requests."
                    "clarifications.reply"
                ),
                "material_requests.documents.view",
                "material_requests.documents.upload",
                (
                    "material_requests."
                    "documents.delete_own"
                ),
                "material_requests.amendments.view",
                "material_requests.amendments.request",
                "material_requests.revisions.view",
                "supplier_rfq.view",
                "purchase_orders.view",
                "inventory.view",
                "reports.view",
                "reports.project.view",
            },

            cls.PROJECT_MANAGER: {
                "material_requests.view",
                "material_requests.create",
                "material_requests.edit",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                (
                    "material_requests."
                    "clarifications.add"
                ),
                (
                    "material_requests."
                    "clarifications.reply"
                ),
                "material_requests.documents.view",
                "material_requests.documents.upload",
                (
                    "material_requests."
                    "documents.delete_own"
                ),
                "material_requests.amendments.view",
                "material_requests.amendments.request",
                "material_requests.revisions.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "reports.view",
                "reports.project.view",
            },

            cls.WAREHOUSE: {
                "material_requests.view",
                "purchase_orders.view",
                "inventory.view",
                "inventory.manage",
                "inventory.stock_in",
                "inventory.stock_out",
                "inventory.adjust",
                "inventory.issue",
                "inventory.history.view",
                "receiving.view",
                "receiving.record",
                "receiving.documents.upload",
                "reports.view",
                "reports.inventory.view",
            },

            cls.WAREHOUSE_PERSONNEL: {
                "material_requests.view",
                "purchase_orders.view",
                "inventory.view",
                "inventory.manage",
                "inventory.stock_in",
                "inventory.stock_out",
                "inventory.adjust",
                "inventory.issue",
                "inventory.history.view",
                "receiving.view",
                "receiving.record",
                "receiving.documents.upload",
                "reports.view",
                "reports.inventory.view",
            },

            cls.ACCOUNTING: {
                "material_requests.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "receiving.view",
                "invoice_monitoring.view",
                "invoice_monitoring.create",
                "invoice_monitoring.edit",
                "invoice_monitoring.manage",
                "reports.view",
                "reports.accounting.view",
                "reports.purchasing.view",
            },

            cls.ACCOUNTING_PERSONNEL: {
                "material_requests.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "receiving.view",
                "invoice_monitoring.view",
                "invoice_monitoring.create",
                "invoice_monitoring.edit",
                "invoice_monitoring.manage",
                "reports.view",
                "reports.accounting.view",
                "reports.purchasing.view",
            },

            cls.EXECUTIVE_MANAGEMENT: {
                "material_requests.view",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                "material_requests.documents.view",
                "material_requests.amendments.view",
                "material_requests.revisions.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "receiving.view",
                "invoice_monitoring.view",
                "reports.view",
                "reports.purchasing.view",
                "reports.project.view",
                "reports.inventory.view",
                "reports.accounting.view",
                "reports.executive.view",
            },

            cls.VIEWER: {
                "material_requests.view",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                "material_requests.documents.view",
                "material_requests.amendments.view",
                "material_requests.revisions.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "receiving.view",
                "invoice_monitoring.view",
                "reports.view",
                "administration.audit.view",
            },

            cls.VIEWER_AUDITOR: {
                "material_requests.view",
                (
                    "material_requests."
                    "clarifications.view"
                ),
                "material_requests.documents.view",
                "material_requests.amendments.view",
                "material_requests.revisions.view",
                "supplier_rfq.view",
                "material_costing.view",
                "purchase_orders.view",
                "inventory.view",
                "receiving.view",
                "invoice_monitoring.view",
                "reports.view",
                "administration.audit.view",
            },
        }

        return permission_name in (
            legacy_permissions.get(
                role,
                set(),
            )
        )