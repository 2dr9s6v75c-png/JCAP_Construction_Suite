from typing import Any


class ActivityLogger:
    """
    Centralized activity-log writer for the JCAP Construction Suite.

    The caller provides an existing database cursor so the activity record
    participates in the same transaction as the business operation.

    This means:
    - if the business operation succeeds, the activity log is committed;
    - if the business operation fails, both changes are rolled back.
    """

    MODULE_QUOTATION = "Quotation Monitoring"
    MODULE_MASTER_DATA = "Master Data"
    MODULE_ADMINISTRATION = "Administration"
    MODULE_PURCHASE_ORDER = "Purchase Orders"
    MODULE_INVENTORY = "Inventory"
    MODULE_INVOICE = "Invoice Monitoring"

    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_ARCHIVE = "ARCHIVE"
    ACTION_RESTORE = "RESTORE"
    ACTION_LOCK = "LOCK"
    ACTION_UNLOCK = "UNLOCK"
    ACTION_FORCE_UNLOCK = "FORCE_UNLOCK"
    ACTION_STATUS_CHANGE = "STATUS_CHANGE"

    @classmethod
    def log(
        cls,
        cursor,
        *,
        user_id: Any,
        action: str,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        """
        Insert an activity-log record using the caller's active transaction.
        """
        if cursor is None:
            raise ValueError("A database cursor is required.")

        if not user_id:
            raise ValueError("A user ID is required for activity logging.")

        if not action or not str(action).strip():
            raise ValueError("An activity action is required.")

        if not module or not str(module).strip():
            raise ValueError("An activity module is required.")

        if not record_id:
            raise ValueError("A record ID is required for activity logging.")

        clean_details = str(details or "").strip()

        if not clean_details:
            raise ValueError("Activity details are required.")

        cursor.execute(
            """
            INSERT INTO core.activity_logs (
                user_id,
                action,
                module,
                record_id,
                details
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                str(action).strip().upper(),
                str(module).strip(),
                record_id,
                clean_details,
            ),
        )

    @classmethod
    def log_create(
        cls,
        cursor,
        *,
        user_id: Any,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        cls.log(
            cursor,
            user_id=user_id,
            action=cls.ACTION_CREATE,
            module=module,
            record_id=record_id,
            details=details,
        )

    @classmethod
    def log_update(
        cls,
        cursor,
        *,
        user_id: Any,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        cls.log(
            cursor,
            user_id=user_id,
            action=cls.ACTION_UPDATE,
            module=module,
            record_id=record_id,
            details=details,
        )

    @classmethod
    def log_archive(
        cls,
        cursor,
        *,
        user_id: Any,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        cls.log(
            cursor,
            user_id=user_id,
            action=cls.ACTION_ARCHIVE,
            module=module,
            record_id=record_id,
            details=details,
        )

    @classmethod
    def log_restore(
        cls,
        cursor,
        *,
        user_id: Any,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        cls.log(
            cursor,
            user_id=user_id,
            action=cls.ACTION_RESTORE,
            module=module,
            record_id=record_id,
            details=details,
        )

    @classmethod
    def log_force_unlock(
        cls,
        cursor,
        *,
        user_id: Any,
        module: str,
        record_id: Any,
        details: str,
    ) -> None:
        cls.log(
            cursor,
            user_id=user_id,
            action=cls.ACTION_FORCE_UNLOCK,
            module=module,
            record_id=record_id,
            details=details,
        )