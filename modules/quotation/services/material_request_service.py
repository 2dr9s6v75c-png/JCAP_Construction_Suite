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