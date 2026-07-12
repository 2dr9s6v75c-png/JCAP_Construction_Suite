from core.database.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    """
    PostgreSQL data-access repository for core.notifications.

    Repository responsibilities:
    - Create notification records
    - Read user notifications
    - Count unread notifications
    - Mark notifications as read
    - Mark all notifications as read
    - Check notification existence for an entity

    Workflow and business rules belong to the service layer.
    """

    # ============================================================
    # CREATE
    # ============================================================

    @classmethod
    def create(
        cls,
        recipient_user_id,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str | None = None,
        entity_id=None,
        created_by=None,
        *,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO core.notifications (
                recipient_user_id,
                notification_type,
                title,
                message,
                entity_type,
                entity_id,
                created_by
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                recipient_user_id,
                notification_type,
                title,
                message,
                entity_type,
                entity_id,
                created_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Notification was not created."
            )

        return str(row[0])

    # ============================================================
    # READ
    # ============================================================

    @classmethod
    def get_by_id(
        cls,
        notification_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                n.id,
                n.recipient_user_id,
                n.notification_type,
                n.title,
                n.message,
                n.entity_type,
                n.entity_id,
                n.is_read,
                n.created_by,
                n.created_at,
                n.read_at,

                recipient.username,
                recipient.full_name,

                creator.username,
                creator.full_name

            FROM core.notifications n

            INNER JOIN core.users recipient
                ON recipient.id = n.recipient_user_id

            LEFT JOIN core.users creator
                ON creator.id = n.created_by

            WHERE n.id = %s
            """,
            (
                notification_id,
            ),
            cursor=cursor,
        )

        return cls._map_notification_detail(
            row
        )

    @classmethod
    def get_by_recipient(
        cls,
        recipient_user_id,
        *,
        unread_only: bool = False,
        limit: int = 100,
        cursor=None,
    ) -> list[dict]:
        if not recipient_user_id:
            return []

        limit = max(
            int(limit),
            1,
        )

        conditions = [
            "n.recipient_user_id = %s"
        ]

        params = [
            recipient_user_id
        ]

        if unread_only:
            conditions.append(
                "n.is_read = FALSE"
            )

        params.append(
            limit
        )

        rows = cls.fetch_all(
            f"""
            SELECT
                n.id,
                n.recipient_user_id,
                n.notification_type,
                n.title,
                n.message,
                n.entity_type,
                n.entity_id,
                n.is_read,
                n.created_by,
                n.created_at,
                n.read_at,

                creator.username,
                creator.full_name

            FROM core.notifications n

            LEFT JOIN core.users creator
                ON creator.id = n.created_by

            WHERE {" AND ".join(conditions)}

            ORDER BY
                n.created_at DESC,
                n.id DESC

            LIMIT %s
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_notification_list(row)
            for row in rows
        ]

    # ============================================================
    # COUNTS
    # ============================================================

    @classmethod
    def count_unread(
        cls,
        recipient_user_id,
        *,
        cursor=None,
    ) -> int:
        if not recipient_user_id:
            return 0

        return cls.count(
            """
            SELECT COUNT(*)
            FROM core.notifications
            WHERE recipient_user_id = %s
              AND is_read = FALSE
            """,
            (
                recipient_user_id,
            ),
            cursor=cursor,
        )

    # ============================================================
    # READ STATUS
    # ============================================================

    @classmethod
    def mark_as_read(
        cls,
        notification_id,
        recipient_user_id,
        *,
        cursor=None,
    ) -> bool:
        row = cls.execute_returning(
            """
            UPDATE core.notifications
            SET
                is_read = TRUE,
                read_at = COALESCE(
                    read_at,
                    CURRENT_TIMESTAMP
                )
            WHERE id = %s
              AND recipient_user_id = %s
            RETURNING id
            """,
            (
                notification_id,
                recipient_user_id,
            ),
            cursor=cursor,
        )

        return row is not None

    @classmethod
    def mark_all_as_read(
        cls,
        recipient_user_id,
        *,
        cursor=None,
    ) -> int:
        if not recipient_user_id:
            return 0

        return cls.execute(
            """
            UPDATE core.notifications
            SET
                is_read = TRUE,
                read_at = COALESCE(
                    read_at,
                    CURRENT_TIMESTAMP
                )
            WHERE recipient_user_id = %s
              AND is_read = FALSE
            """,
            (
                recipient_user_id,
            ),
            cursor=cursor,
        )

    # ============================================================
    # EXISTENCE
    # ============================================================

    @classmethod
    def exists_for_entity(
        cls,
        recipient_user_id,
        notification_type: str,
        entity_type: str,
        entity_id,
        *,
        unread_only: bool = False,
        cursor=None,
    ) -> bool:
        if (
            not recipient_user_id
            or not notification_type
            or not entity_type
            or not entity_id
        ):
            return False

        conditions = [
            "recipient_user_id = %s",
            "notification_type = %s",
            "entity_type = %s",
            "entity_id = %s",
        ]

        params = [
            recipient_user_id,
            notification_type,
            entity_type,
            entity_id,
        ]

        if unread_only:
            conditions.append(
                "is_read = FALSE"
            )

        return cls.exists(
            f"""
            SELECT EXISTS (
                SELECT 1
                FROM core.notifications
                WHERE {" AND ".join(conditions)}
            )
            """,
            params,
            cursor=cursor,
        )

    # ============================================================
    # ROW MAPPING
    # ============================================================

    @staticmethod
    def _map_notification_detail(
        row,
    ):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "recipient_user_id": str(row[1]),
            "notification_type": row[2],
            "title": row[3],
            "message": row[4],
            "entity_type": row[5],
            "entity_id": (
                str(row[6])
                if row[6]
                else None
            ),
            "is_read": bool(row[7]),
            "created_by": (
                str(row[8])
                if row[8]
                else None
            ),
            "created_at": row[9],
            "read_at": row[10],
            "recipient_username": row[11],
            "recipient_full_name": row[12],
            "created_by_username": row[13],
            "created_by_full_name": row[14],
        }

    @staticmethod
    def _map_notification_list(
        row,
    ):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "recipient_user_id": str(row[1]),
            "notification_type": row[2],
            "title": row[3],
            "message": row[4],
            "entity_type": row[5],
            "entity_id": (
                str(row[6])
                if row[6]
                else None
            ),
            "is_read": bool(row[7]),
            "created_by": (
                str(row[8])
                if row[8]
                else None
            ),
            "created_at": row[9],
            "read_at": row[10],
            "created_by_username": row[11],
            "created_by_full_name": row[12],
        }