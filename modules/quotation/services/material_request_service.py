from core.database.connection import get_connection
from core.numbering.numbering_service import generate_document_number
from core.documents.storage_service import copy_attachments_to_request_folder


def create_material_request(data: dict, user: dict) -> str:
    conn = get_connection()
    cur = conn.cursor()

    mr_number = generate_document_number("MR")

    try:
        saved_files = copy_attachments_to_request_folder(
            attachments=data["attachments"],
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
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            RETURNING id
            """,
            (
                mr_number,
                mr_number,
                data["project_id"],

                # Both columns receive the same value for now
                data["material_request_description"],
                data["material_request_description"],

                data["requested_by"],
                data["assigned_to"],
                data["priority"],
                "New",
                data["due_date"],
                data["remarks"],

                mr_number,

                user["id"],
            ),
        )

        material_request_id = cur.fetchone()[0]

        for file in saved_files:

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
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    material_request_id,
                    file["original_filename"],
                    file["stored_filename"],
                    file["file_extension"],
                    file["file_size"],
                    file["relative_module"],
                    user["id"],
                ),
            )

        cur.execute(
            """
            INSERT INTO core.activity_logs (
                user_id,
                action,
                module,
                record_id,
                details
            )
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                user["id"],
                "CREATE",
                "Quotation Monitoring",
                material_request_id,
                f"Created Material Request {mr_number}",
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

def get_material_requests():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            mr.id,
            mr.mr_number,
            p.project_code,
            p.project_name,
            mr.material_request_description,
            mr.requested_by,
            mr.assigned_to,
            mr.priority,
            mr.status,
            mr.due_date,
            mr.created_at,
            COUNT(att.id) AS attachment_count
        FROM quotation.material_requests mr
        JOIN core.projects p
            ON mr.project_id = p.id
        LEFT JOIN quotation.material_request_attachments att
            ON mr.id = att.material_request_id
        GROUP BY
            mr.id,
            mr.mr_number,
            p.project_code,
            p.project_name,
            mr.material_request_description,
            mr.requested_by,
            mr.assigned_to,
            mr.priority,
            mr.status,
            mr.due_date,
            mr.created_at
        ORDER BY mr.created_at DESC
        """
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": str(row[0]),
            "mr_number": row[1],
            "project_code": row[2] or "",
            "project_name": row[3],
            "description": row[4],
            "requested_by": row[5],
            "assigned_to": row[6],
            "priority": row[7],
            "status": row[8],
            "due_date": row[9],
            "created_at": row[10],
            "attachment_count": row[11],
        }
        for row in rows
    ]
def get_material_request(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            mr.id,
            mr.mr_number,
            mr.project_id,
            p.project_code,
            p.project_name,
            c.client_name,
            p.location,
            mr.material_request_description,
            mr.requested_by,
            mr.assigned_to,
            mr.priority,
            mr.status,
            mr.due_date,
            mr.remarks,
            mr.folder_name,
            mr.created_at
        FROM quotation.material_requests mr
        JOIN core.projects p ON mr.project_id = p.id
        LEFT JOIN core.clients c ON p.client_id = c.id
        WHERE mr.id = %s
        """,
        (material_request_id,)
    )

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
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
        (material_request_id,)
    )

    attachments = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "id": str(row[0]),
        "mr_number": row[1],
        "project_id": str(row[2]),
        "project_code": row[3] or "",
        "project_name": row[4],
        "client_name": row[5] or "",
        "location": row[6] or "",
        "material_request_description": row[7],
        "requested_by": row[8],
        "assigned_to": row[9],
        "priority": row[10],
        "status": row[11],
        "due_date": row[12],
        "remarks": row[13] or "",
        "folder_name": row[14],
        "created_at": row[15],
        "attachments": [
            {
                "original_filename": att[0],
                "stored_filename": att[1],
                "file_extension": att[2],
                "file_size": att[3],
                "relative_module": att[4],
                "uploaded_at": att[5],
            }
            for att in attachments
        ],
    }
def get_material_request(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            mr.id,
            mr.mr_number,
            mr.project_id,
            p.project_code,
            p.project_name,
            c.client_name,
            p.location,
            mr.material_request_description,
            mr.requested_by,
            mr.assigned_to,
            mr.priority,
            mr.status,
            mr.due_date,
            mr.remarks,
            mr.folder_name,
            mr.created_at
        FROM quotation.material_requests mr
        JOIN core.projects p ON mr.project_id = p.id
        LEFT JOIN core.clients c ON p.client_id = c.id
        WHERE mr.id = %s
        """,
        (material_request_id,)
    )

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
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
        (material_request_id,)
    )

    attachments = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "id": str(row[0]),
        "mr_number": row[1],
        "project_id": str(row[2]),
        "project_code": row[3] or "",
        "project_name": row[4],
        "client_name": row[5] or "",
        "location": row[6] or "",
        "material_request_description": row[7],
        "requested_by": row[8],
        "assigned_to": row[9],
        "priority": row[10],
        "status": row[11],
        "due_date": row[12],
        "remarks": row[13] or "",
        "folder_name": row[14],
        "created_at": row[15],
        "attachments": [
            {
                "original_filename": att[0],
                "stored_filename": att[1],
                "file_extension": att[2],
                "file_size": att[3],
                "relative_module": att[4],
                "uploaded_at": att[5],
            }
            for att in attachments
        ],
    }


def get_material_request_activity(material_request_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            al.action,
            al.details,
            al.created_at,
            u.full_name
        FROM core.activity_logs al
        LEFT JOIN core.users u ON al.user_id = u.id
        WHERE al.record_id = %s
        ORDER BY al.created_at DESC
        """,
        (material_request_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "action": row[0],
            "details": row[1],
            "created_at": row[2],
            "user": row[3] or "System",
        }
        for row in rows
    ]
from datetime import datetime, timedelta


LOCK_TIMEOUT_MINUTES = 30


def lock_material_request(material_request_id: str, user: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT locked_by, lock_expires_at
            FROM quotation.material_requests
            WHERE id = %s
            """,
            (material_request_id,),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError("Material Request not found.")

        locked_by, lock_expires_at = row
        now = datetime.now()

        if locked_by and lock_expires_at and lock_expires_at > now and str(locked_by) != user["id"]:
            return {
                "success": False,
                "message": "This Material Request is currently locked by another user.",
            }

        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                locked_by = %s,
                locked_at = CURRENT_TIMESTAMP,
                lock_expires_at = CURRENT_TIMESTAMP + INTERVAL '30 minutes'
            WHERE id = %s
            """,
            (user["id"], material_request_id),
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
            (material_request_id, user["id"]),
        )

        conn.commit()

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
            LEFT JOIN core.users u ON mr.locked_by = u.id
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

        locked_by, locked_at, lock_expires_at, locked_by_name = row

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
            "locked_by_name": locked_by_name or "Unknown User",
            "locked_at": locked_at,
            "lock_expires_at": lock_expires_at,
        }

    finally:
        cur.close()
        conn.close()

        
def update_material_request(material_request_id: str, data: dict, user: dict):
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
                data["remarks"],
                material_request_id,
            ),
        )

        result = cur.fetchone()

        if not result:
            raise ValueError("Material Request not found.")

        mr_number = result[0]

        cur.execute(
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
                user["id"],
                "UPDATE",
                "Quotation Monitoring",
                material_request_id,
                f"Updated Material Request {mr_number}",
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

def archive_material_request(material_request_id: str, user: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE quotation.material_requests
            SET
                status = 'Archived',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING mr_number
            """,
            (material_request_id,),
        )

        result = cur.fetchone()

        if not result:
            raise ValueError("Material Request not found.")

        mr_number = result[0]

        cur.execute(
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
                user["id"],
                "ARCHIVE",
                "Quotation Monitoring",
                material_request_id,
                f"Archived Material Request {mr_number}",
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