from datetime import datetime

from core.database.connection import get_connection
from core.documents.storage_service import copy_attachments_to_request_folder
from core.lifecycle.document_lifecycle import DocumentLifecycle
from core.logging.activity_logger import ActivityLogger
from core.numbering.numbering_service import generate_document_number
from core.security.permissions import PermissionService


LOCK_TIMEOUT_MINUTES = 30


# ============================================================
# CREATE
# ============================================================

def create_material_request(data: dict, user: dict) -> str:
    conn = get_connection()
    cur = conn.cursor()

    mr_number = generate_document_number("MR")

    try:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM master.sites s
                JOIN master.projects p
                    ON p.id = s.project_id
                WHERE s.id = %s
                  AND s.project_id = %s
                  AND s.is_active = TRUE
                  AND p.is_active = TRUE
            )
            """,
            (
                data.get("site_id"),
                data.get("project_id"),
            ),
        )

        if not cur.fetchone()[0]:
            raise ValueError(
                "The selected active Site does not belong to "
                "the selected active Project."
            )

        saved_files = copy_attachments_to_request_folder(
            attachments=data.get("attachments", []),
            project_code=data.get("project_code"),
            project_name=data["project_name"],
            request_no=mr_number,
        )

        cur.execute(
            """
            INSERT INTO quotation.material_requests (
                request_no,
                mr_number,
                project_id,
                site_id,
                request_description,
                material_request_description,
                requested_by,
                assigned_to,
                priority,
                status,
                due_date,
                remarks,
                folder_name,
                created_by
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
            """,
            (
                mr_number,
                mr_number,
                data["project_id"],
                data["site_id"],
                data["material_request_description"],
                data["material_request_description"],
                data["requested_by"],
                data["assigned_to"],
                data["priority"],
                "New",
                data["due_date"],
                data.get("remarks", ""),
                mr_number,
                user["id"],
            ),
        )

        material_request_id = cur.fetchone()[0]

        for file_data in saved_files:
            cur.execute(
                """
                INSERT INTO quotation.material_request_attachments (
                    material_request_id,
                    original_filename,
                    stored_filename,
                    file_extension,
                    file_size,
                    relative_module,
                    uploaded_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    material_request_id,
                    file_data["original_filename"],
                    file_data["stored_filename"],
                    file_data["file_extension"],
                    file_data["file_size"],
                    file_data["relative_module"],
                    user["id"],
                ),
            )

        ActivityLogger.log_create(
            cur,
            user_id=user["id"],
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=f"Created Material Request {mr_number}",
        )

        conn.commit()
        return mr_number

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


# ============================================================
# LIST AND FILTER
# ============================================================

def get_material_requests(status_filter="Active"):
    conn = get_connection()
    cur = conn.cursor()

    archived_status = DocumentLifecycle.ARCHIVED.value

    where_clause = ""
    params = []

    if status_filter == "Active":
        where_clause = "WHERE mr.status <> %s"
        params.append(archived_status)

    elif status_filter == "Archived":
        where_clause = "WHERE mr.status = %s"
        params.append(archived_status)

    elif status_filter != "All":
        where_clause = "WHERE mr.status = %s"
        params.append(status_filter)

    try:
        cur.execute(
            f"""
            SELECT
                mr.id,
                mr.mr_number,
                p.project_code,
                p.project_name,
                c.client_name,
                s.site_code,
                s.site_name,
                mr.material_request_description,
                mr.requested_by,
                mr.assigned_to,
                assigned_user.full_name,
                assigned_user.username,
                mr.priority,
                mr.status,
                mr.due_date,
                mr.created_at,
                COUNT(att.id) AS attachment_count
            FROM quotation.material_requests mr
            JOIN master.projects p
                ON mr.project_id = p.id
            JOIN master.clients c
                ON p.client_id = c.id
            JOIN master.sites s
                ON mr.site_id = s.id
            LEFT JOIN core.users assigned_user
                ON mr.assigned_to = assigned_user.id::text
            LEFT JOIN quotation.material_request_attachments att
                ON mr.id = att.material_request_id
            {where_clause}
            GROUP BY
                mr.id,
                mr.mr_number,
                p.project_code,
                p.project_name,
                c.client_name,
                s.site_code,
                s.site_name,
                mr.material_request_description,
                mr.requested_by,
                mr.assigned_to,
                assigned_user.full_name,
                assigned_user.username,
                mr.priority,
                mr.status,
                mr.due_date,
                mr.created_at
            ORDER BY mr.created_at DESC
            """,
            params,
        )

        rows = cur.fetchall()

        return [
            {
                "id": str(row[0]),
                "mr_number": row[1],
                "project_code": row[2] or "",
                "project_name": row[3] or "",
                "client_name": row[4] or "",
                "site_code": row[5] or "",
                "site_name": row[6] or "",
                "description": row[7] or "",
                "requested_by": row[8] or "",
                "assigned_to": (
                    str(row[9]) if row[9] else None
                ),
                "assigned_to_id": (
                    str(row[9]) if row[9] else None
                ),
                "assigned_to_name": row[10] or "",
                "assigned_to_username": row[11] or "",
                "priority": row[12] or "",
                "status": row[13] or "",
                "due_date": row[14],
                "created_at": row[15],
                "attachment_count": row[16] or 0,
            }
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()


# ============================================================
# GET SINGLE RECORD
# ============================================================

def get_material_request(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr.id,
                mr.mr_number,
                mr.project_id,
                p.project_code,
                p.project_name,
                c.client_name,
                mr.site_id,
                s.site_code,
                s.site_name,
                mr.material_request_description,
                mr.requested_by,
                mr.assigned_to,
                assigned_user.full_name,
                assigned_user.username,
                mr.priority,
                mr.status,
                mr.due_date,
                mr.remarks,
                mr.folder_name,
                mr.created_at,
                mr.current_assignment_id
            FROM quotation.material_requests mr
            JOIN master.projects p
                ON mr.project_id = p.id
            JOIN master.clients c
                ON p.client_id = c.id
            JOIN master.sites s
                ON mr.site_id = s.id
            LEFT JOIN core.users assigned_user
                ON mr.assigned_to = assigned_user.id::text
            WHERE mr.id = %s
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            return None

        cur.execute(
            """
            SELECT
                original_filename,
                stored_filename,
                file_extension,
                file_size,
                relative_module,
                uploaded_at
            FROM quotation.material_request_attachments
            WHERE material_request_id = %s
            ORDER BY uploaded_at
            """,
            (material_request_id,),
        )

        attachments = cur.fetchall()

        assigned_to_id = row[11]

        return {
            "id": str(row[0]),
            "mr_number": row[1],
            "project_id": str(row[2]),
            "project_code": row[3] or "",
            "project_name": row[4] or "",
            "client_name": row[5] or "",
            "site_id": str(row[6]),
            "site_code": row[7] or "",
            "site_name": row[8] or "",
            "location": row[8] or "",
            "material_request_description": row[9] or "",
            "requested_by": row[10] or "",
            "assigned_to": (
                str(assigned_to_id)
                if assigned_to_id
                else None
            ),
            "assigned_to_id": (
                str(assigned_to_id)
                if assigned_to_id
                else None
            ),
            "assigned_to_name": row[12] or "",
            "assigned_to_username": row[13] or "",
            "priority": row[14] or "",
            "status": row[15] or "",
            "due_date": row[16],
            "remarks": row[17] or "",
            "folder_name": row[18] or "",
            "created_at": row[19],
            "current_assignment_id": (
                str(row[20]) if row[20] else None
            ),
            "assignment_id": (
                str(row[20]) if row[20] else None
            ),
            "attachments": [
                {
                    "original_filename": attachment[0],
                    "stored_filename": attachment[1],
                    "file_extension": attachment[2],
                    "file_size": attachment[3],
                    "relative_module": attachment[4],
                    "uploaded_at": attachment[5],
                }
                for attachment in attachments
            ],
        }

    finally:
        cur.close()
        conn.close()


# ============================================================
# ACTIVITY TIMELINE
# ============================================================

def get_material_request_activity(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                al.action,
                al.details,
                al.created_at,
                u.full_name
            FROM core.activity_logs al
            LEFT JOIN core.users u
                ON al.user_id = u.id
            WHERE al.record_id = %s
            ORDER BY al.created_at DESC
            """,
            (material_request_id,),
        )

        rows = cur.fetchall()

        return [
            {
                "action": row[0],
                "details": row[1],
                "created_at": row[2],
                "user": row[3] or "System",
            }
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()


# ============================================================
# LOCKING
# ============================================================

def lock_material_request(material_request_id: str, user: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                locked_by,
                lock_expires_at
            FROM quotation.material_requests
            WHERE id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError("Material Request not found.")

        locked_by, lock_expires_at = row
        now = datetime.now()

        if (
            locked_by
            and lock_expires_at
            and lock_expires_at > now
            and str(locked_by) != str(user["id"])
        ):
            return {
                "success": False,
                "message": (
                    "This Material Request is currently "
                    "locked by another user."
                ),
            }

        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                locked_by = %s,
                locked_at = CURRENT_TIMESTAMP,
                lock_expires_at =
                    CURRENT_TIMESTAMP + INTERVAL '30 minutes'
            WHERE id = %s
            """,
            (
                user["id"],
                material_request_id,
            ),
        )

        conn.commit()

        return {
            "success": True,
            "message": "Material Request locked successfully.",
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def unlock_material_request(material_request_id: str, user: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                locked_by = NULL,
                locked_at = NULL,
                lock_expires_at = NULL
            WHERE id = %s
              AND locked_by = %s
            """,
            (
                material_request_id,
                user["id"],
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def force_unlock_material_request(
    material_request_id: str,
    user: dict,
) -> str:
    if not PermissionService.can_force_unlock_material_request(user):
        raise PermissionError(
            "Only an Administrator can force-unlock "
            "a Material Request."
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr.mr_number,
                mr.locked_by,
                u.full_name
            FROM quotation.material_requests mr
            LEFT JOIN core.users u
                ON mr.locked_by = u.id
            WHERE mr.id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError("Material Request not found.")

        mr_number, locked_by, locked_by_name = row

        if not locked_by:
            raise ValueError(
                "This Material Request is not currently locked."
            )

        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                locked_by = NULL,
                locked_at = NULL,
                lock_expires_at = NULL
            WHERE id = %s
            """,
            (material_request_id,),
        )

        ActivityLogger.log_force_unlock(
            cur,
            user_id=user["id"],
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=(
                f"Force-unlocked Material Request {mr_number}. "
                f"Previous lock owner: "
                f"{locked_by_name or 'Unknown User'}"
            ),
        )

        conn.commit()
        return mr_number

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def get_material_request_lock_status(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr.locked_by,
                mr.locked_at,
                mr.lock_expires_at,
                u.full_name
            FROM quotation.material_requests mr
            LEFT JOIN core.users u
                ON mr.locked_by = u.id
            WHERE mr.id = %s
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            return {
                "locked": False,
                "message": "Material Request not found.",
            }

        (
            locked_by,
            locked_at,
            lock_expires_at,
            locked_by_name,
        ) = row

        now = datetime.now()

        if (
            locked_by
            and lock_expires_at
            and lock_expires_at <= now
        ):
            return {
                "locked": False,
                "locked_by": None,
                "locked_by_name": None,
                "locked_at": None,
                "lock_expires_at": None,
            }

        if not locked_by:
            return {
                "locked": False,
                "locked_by": None,
                "locked_by_name": None,
                "locked_at": None,
                "lock_expires_at": None,
            }

        return {
            "locked": True,
            "locked_by": str(locked_by),
            "locked_by_name": (
                locked_by_name or "Unknown User"
            ),
            "locked_at": locked_at,
            "lock_expires_at": lock_expires_at,
        }

    finally:
        cur.close()
        conn.close()


# ============================================================
# UPDATE
# ============================================================

def update_material_request(
    material_request_id: str,
    data: dict,
    user: dict,
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                material_request_description = %s,
                request_description = %s,
                assigned_to = %s,
                priority = %s,
                due_date = %s,
                remarks = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING mr_number
            """,
            (
                data["material_request_description"],
                data["material_request_description"],
                data["assigned_to"],
                data["priority"],
                data["due_date"],
                data.get("remarks", ""),
                material_request_id,
            ),
        )

        result = cur.fetchone()

        if not result:
            raise ValueError("Material Request not found.")

        mr_number = result[0]

        ActivityLogger.log_update(
            cur,
            user_id=user["id"],
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=f"Updated Material Request {mr_number}",
        )

        conn.commit()
        return mr_number

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


# ============================================================
# ARCHIVE
# ============================================================

def archive_material_request(
    material_request_id: str,
    user: dict,
):
    if not PermissionService.can_archive_material_request(user):
        raise PermissionError(
            "You do not have permission to archive "
            "Material Requests."
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr_number,
                status
            FROM quotation.material_requests
            WHERE id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError("Material Request not found.")

        mr_number, current_status = row

        if DocumentLifecycle.is_archived(current_status):
            raise ValueError(
                "This Material Request is already archived."
            )

        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                status = %s,
                locked_by = NULL,
                locked_at = NULL,
                lock_expires_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                DocumentLifecycle.ARCHIVED.value,
                material_request_id,
            ),
        )

        ActivityLogger.log_archive(
            cur,
            user_id=user["id"],
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=f"Archived Material Request {mr_number}",
        )

        conn.commit()
        return mr_number

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


# ============================================================
# RESTORE
# ============================================================

def restore_material_request(
    material_request_id: str,
    user: dict,
) -> str:
    if not PermissionService.can_restore_material_request(user):
        raise PermissionError(
            "You do not have permission to restore "
            "Material Requests."
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                mr_number,
                status
            FROM quotation.material_requests
            WHERE id = %s
            FOR UPDATE
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError("Material Request not found.")

        mr_number, current_status = row

        if not DocumentLifecycle.is_archived(current_status):
            raise ValueError(
                "Only archived Material Requests can be restored."
            )

        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                status = %s,
                locked_by = NULL,
                locked_at = NULL,
                lock_expires_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                DocumentLifecycle.RESTORED.value,
                material_request_id,
            ),
        )

        ActivityLogger.log_restore(
            cur,
            user_id=user["id"],
            module=ActivityLogger.MODULE_QUOTATION,
            record_id=material_request_id,
            details=f"Restored Material Request {mr_number}",
        )

        conn.commit()
        return mr_number

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()