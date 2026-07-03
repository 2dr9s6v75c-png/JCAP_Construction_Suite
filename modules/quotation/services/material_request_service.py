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