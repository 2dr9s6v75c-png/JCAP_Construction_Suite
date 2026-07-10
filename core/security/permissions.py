class PermissionService:
    """
    Centralized permission rules for the JCAP Construction Suite.

    During Version 1, permissions are based on the user's role name.
    Later, this can be connected to database-managed permissions without
    requiring changes throughout the views and services.
    """

    ADMINISTRATOR = "administrator"
    PURCHASING_MANAGER = "purchasing manager"
    PURCHASING_OFFICER = "purchasing officer"
    ACCOUNTING = "accounting"
    WAREHOUSE = "warehouse"
    VIEWER = "viewer"

    @classmethod
    def normalize_role(cls, user: dict | None) -> str:
        if not user:
            return ""

        return str(user.get("role", "")).strip().lower()

    @classmethod
    def has_role(cls, user: dict | None, *roles: str) -> bool:
        user_role = cls.normalize_role(user)
        allowed_roles = {
            str(role).strip().lower()
            for role in roles
        }

        return user_role in allowed_roles

    @classmethod
    def is_administrator(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
        )

    # ============================================================
    # Material Request permissions
    # ============================================================

    @classmethod
    def can_create_material_request(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
            cls.PURCHASING_OFFICER,
        )

    @classmethod
    def can_edit_material_request(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
            cls.PURCHASING_OFFICER,
        )

    @classmethod
    def can_archive_material_request(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
        )

    @classmethod
    def can_restore_material_request(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
        )

    @classmethod
    def can_force_unlock_material_request(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.is_administrator(user)

    # ============================================================
    # User administration permissions
    # ============================================================

    @classmethod
    def can_manage_users(cls, user: dict | None) -> bool:
        return cls.is_administrator(user)

    @classmethod
    def can_manage_roles(cls, user: dict | None) -> bool:
        return cls.is_administrator(user)

    @classmethod
    def can_view_audit_logs(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
        )

    # ============================================================
    # Future module permissions
    # ============================================================

    @classmethod
    def can_manage_supplier_quotations(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
            cls.PURCHASING_OFFICER,
        )

    @classmethod
    def can_manage_purchase_orders(
        cls,
        user: dict | None,
    ) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.PURCHASING_MANAGER,
            cls.PURCHASING_OFFICER,
        )

    @classmethod
    def can_manage_invoices(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.ACCOUNTING,
        )

    @classmethod
    def can_manage_inventory(cls, user: dict | None) -> bool:
        return cls.has_role(
            user,
            cls.ADMINISTRATOR,
            cls.WAREHOUSE,
        )