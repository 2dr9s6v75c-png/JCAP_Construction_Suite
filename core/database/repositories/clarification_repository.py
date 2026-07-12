from core.database.repositories.base_repository import BaseRepository


class ClarificationRepository(BaseRepository):
    """
    PostgreSQL data-access repository for the Supplier Clarification
    Workflow.

    Repository responsibilities:
    - Create and read clarifications
    - Read Material Request clarifications
    - Update clarification workflow status
    - Create and read clarification messages
    - Create and read message attachments

    Workflow, permissions, notifications, and transaction orchestration
    belong to the service layer.
    """

    # ============================================================
    # CLARIFICATIONS
    # ============================================================

    @classmethod
    def create_clarification(
        cls,
        material_request_id,
        subject: str,
        created_by,
        *,
        supplier_name: str | None = None,
        supplier_reference: str | None = None,
        status: str = "Awaiting Engineering Response",
        assigned_to=None,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO quotation.clarifications (
                material_request_id,
                subject,
                supplier_name,
                supplier_reference,
                status,
                assigned_to,
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
                material_request_id,
                subject,
                supplier_name,
                supplier_reference,
                status,
                assigned_to,
                created_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Clarification was not created."
            )

        return str(row[0])

    @classmethod
    def get_clarification_by_id(
        cls,
        clarification_id,
        *,
        cursor=None,
    ):
        row = cls.fetch_one(
            """
            SELECT
                c.id,
                c.material_request_id,
                c.subject,
                c.supplier_name,
                c.supplier_reference,
                c.status,
                c.assigned_to,
                c.created_by,
                c.created_at,
                c.updated_at,
                c.resolved_at,
                c.resolved_by,

                mr.request_no,
                mr.mr_number,
                mr.request_description,

                assigned.username,
                assigned.full_name,

                creator.username,
                creator.full_name,

                resolver.username,
                resolver.full_name

            FROM quotation.clarifications c

            INNER JOIN quotation.material_requests mr
                ON mr.id = c.material_request_id

            LEFT JOIN core.users assigned
                ON assigned.id = c.assigned_to

            INNER JOIN core.users creator
                ON creator.id = c.created_by

            LEFT JOIN core.users resolver
                ON resolver.id = c.resolved_by

            WHERE c.id = %s
            """,
            (
                clarification_id,
            ),
            cursor=cursor,
        )

        return cls._map_clarification_detail(row)

    @classmethod
    def get_by_material_request(
        cls,
        material_request_id,
        *,
        status: str | None = None,
        cursor=None,
    ) -> list[dict]:
        conditions = [
            "c.material_request_id = %s"
        ]

        params = [
            material_request_id
        ]

        if status:
            conditions.append(
                "c.status = %s"
            )
            params.append(status)

        rows = cls.fetch_all(
            f"""
            SELECT
                c.id,
                c.material_request_id,
                c.subject,
                c.supplier_name,
                c.supplier_reference,
                c.status,
                c.assigned_to,
                c.created_by,
                c.created_at,
                c.updated_at,
                c.resolved_at,
                c.resolved_by,

                assigned.full_name,
                creator.full_name,
                resolver.full_name,

                (
                    SELECT COUNT(*)
                    FROM quotation.clarification_messages cm
                    WHERE cm.clarification_id = c.id
                ) AS message_count

            FROM quotation.clarifications c

            LEFT JOIN core.users assigned
                ON assigned.id = c.assigned_to

            INNER JOIN core.users creator
                ON creator.id = c.created_by

            LEFT JOIN core.users resolver
                ON resolver.id = c.resolved_by

            WHERE {" AND ".join(conditions)}

            ORDER BY
                c.created_at DESC,
                c.id DESC
            """,
            params,
            cursor=cursor,
        )

        return [
            cls._map_clarification_list(row)
            for row in rows
        ]

    @classmethod
    def update_status(
        cls,
        clarification_id,
        status: str,
        *,
        cursor=None,
    ) -> bool:
        row = cls.execute_returning(
            """
            UPDATE quotation.clarifications
            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (
                status,
                clarification_id,
            ),
            cursor=cursor,
        )

        return row is not None

    @classmethod
    def update_assignment(
        cls,
        clarification_id,
        assigned_to,
        *,
        cursor=None,
    ) -> bool:
        row = cls.execute_returning(
            """
            UPDATE quotation.clarifications
            SET
                assigned_to = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (
                assigned_to,
                clarification_id,
            ),
            cursor=cursor,
        )

        return row is not None

    @classmethod
    def resolve(
        cls,
        clarification_id,
        resolved_by,
        *,
        cursor=None,
    ) -> bool:
        row = cls.execute_returning(
            """
            UPDATE quotation.clarifications
            SET
                status = 'Resolved',
                resolved_at = CURRENT_TIMESTAMP,
                resolved_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (
                resolved_by,
                clarification_id,
            ),
            cursor=cursor,
        )

        return row is not None

    # ============================================================
    # MESSAGES
    # ============================================================

    @classmethod
    def create_message(
        cls,
        clarification_id,
        message_type: str,
        message_text: str,
        sent_by,
        *,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO quotation.clarification_messages (
                clarification_id,
                message_type,
                message_text,
                sent_by
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                clarification_id,
                message_type,
                message_text,
                sent_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Clarification message was not created."
            )

        return str(row[0])

    @classmethod
    def get_messages(
        cls,
        clarification_id,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                cm.id,
                cm.clarification_id,
                cm.message_type,
                cm.message_text,
                cm.sent_by,
                cm.created_at,

                sender.username,
                sender.full_name,

                (
                    SELECT COUNT(*)
                    FROM quotation.clarification_message_attachments cma
                    WHERE cma.clarification_message_id = cm.id
                ) AS attachment_count

            FROM quotation.clarification_messages cm

            INNER JOIN core.users sender
                ON sender.id = cm.sent_by

            WHERE cm.clarification_id = %s

            ORDER BY
                cm.created_at ASC,
                cm.id ASC
            """,
            (
                clarification_id,
            ),
            cursor=cursor,
        )

        return [
            cls._map_message(row)
            for row in rows
        ]

    # ============================================================
    # MESSAGE ATTACHMENTS
    # ============================================================

    @classmethod
    def create_message_attachment(
        cls,
        clarification_message_id,
        original_filename: str,
        stored_filename: str,
        *,
        file_extension: str | None = None,
        file_size: int | None = None,
        relative_module: str = "02 Supplier Clarifications",
        uploaded_by=None,
        cursor=None,
    ) -> str:
        row = cls.execute_returning(
            """
            INSERT INTO quotation.clarification_message_attachments (
                clarification_message_id,
                original_filename,
                stored_filename,
                file_extension,
                file_size,
                relative_module,
                uploaded_by
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
                clarification_message_id,
                original_filename,
                stored_filename,
                file_extension,
                file_size,
                relative_module,
                uploaded_by,
            ),
            cursor=cursor,
        )

        if not row:
            raise RuntimeError(
                "Clarification message attachment was not created."
            )

        return str(row[0])

    @classmethod
    def get_message_attachments(
        cls,
        clarification_message_id,
        *,
        cursor=None,
    ) -> list[dict]:
        rows = cls.fetch_all(
            """
            SELECT
                cma.id,
                cma.clarification_message_id,
                cma.original_filename,
                cma.stored_filename,
                cma.file_extension,
                cma.file_size,
                cma.relative_module,
                cma.uploaded_by,
                cma.uploaded_at,

                uploader.username,
                uploader.full_name

            FROM quotation.clarification_message_attachments cma

            LEFT JOIN core.users uploader
                ON uploader.id = cma.uploaded_by

            WHERE cma.clarification_message_id = %s

            ORDER BY
                cma.uploaded_at ASC,
                cma.id ASC
            """,
            (
                clarification_message_id,
            ),
            cursor=cursor,
        )

        return [
            cls._map_attachment(row)
            for row in rows
        ]

    # ============================================================
    # EXISTENCE
    # ============================================================

    @classmethod
    def exists(
        cls,
        clarification_id,
        *,
        cursor=None,
    ) -> bool:
        return super().exists(
            """
            SELECT EXISTS (
                SELECT 1
                FROM quotation.clarifications
                WHERE id = %s
            )
            """,
            (
                clarification_id,
            ),
            cursor=cursor,
        )

    # ============================================================
    # ROW MAPPING
    # ============================================================

    @staticmethod
    def _map_clarification_detail(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "material_request_id": str(row[1]),
            "subject": row[2],
            "supplier_name": row[3],
            "supplier_reference": row[4],
            "status": row[5],
            "assigned_to": (
                str(row[6])
                if row[6]
                else None
            ),
            "created_by": str(row[7]),
            "created_at": row[8],
            "updated_at": row[9],
            "resolved_at": row[10],
            "resolved_by": (
                str(row[11])
                if row[11]
                else None
            ),
            "request_no": row[12],
            "mr_number": row[13],
            "request_description": row[14],
            "assigned_username": row[15],
            "assigned_full_name": row[16],
            "created_by_username": row[17],
            "created_by_full_name": row[18],
            "resolved_by_username": row[19],
            "resolved_by_full_name": row[20],
        }

    @staticmethod
    def _map_clarification_list(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "material_request_id": str(row[1]),
            "subject": row[2],
            "supplier_name": row[3],
            "supplier_reference": row[4],
            "status": row[5],
            "assigned_to": (
                str(row[6])
                if row[6]
                else None
            ),
            "created_by": str(row[7]),
            "created_at": row[8],
            "updated_at": row[9],
            "resolved_at": row[10],
            "resolved_by": (
                str(row[11])
                if row[11]
                else None
            ),
            "assigned_full_name": row[12],
            "created_by_full_name": row[13],
            "resolved_by_full_name": row[14],
            "message_count": int(row[15] or 0),
        }

    @staticmethod
    def _map_message(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "clarification_id": str(row[1]),
            "message_type": row[2],
            "message_text": row[3],
            "sent_by": str(row[4]),
            "created_at": row[5],
            "sent_by_username": row[6],
            "sent_by_full_name": row[7],
            "attachment_count": int(row[8] or 0),
        }

    @staticmethod
    def _map_attachment(row):
        if not row:
            return None

        return {
            "id": str(row[0]),
            "clarification_message_id": str(row[1]),
            "original_filename": row[2],
            "stored_filename": row[3],
            "file_extension": row[4],
            "file_size": row[5],
            "relative_module": row[6],
            "uploaded_by": (
                str(row[7])
                if row[7]
                else None
            ),
            "uploaded_at": row[8],
            "uploaded_by_username": row[9],
            "uploaded_by_full_name": row[10],
        }