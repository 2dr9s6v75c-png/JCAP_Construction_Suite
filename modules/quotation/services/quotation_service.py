from datetime import datetime
from core.database.connection import get_connection


def generate_request_no():
    year = datetime.now().year

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM quotation.material_requests
        WHERE request_no LIKE %s
        """,
        (f"MR-{year}-%",)
    )

    count = cur.fetchone()[0] + 1

    cur.close()
    conn.close()

    return f"MR-{year}-{count:06d}"


def get_or_create_project(project_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM core.projects
        WHERE project_name = %s
        """,
        (project_name,)
    )

    project = cur.fetchone()

    if project:
        project_id = project[0]
    else:
        cur.execute(
            """
            INSERT INTO core.projects (project_name)
            VALUES (%s)
            RETURNING id
            """,
            (project_name,)
        )
        project_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return project_id


def create_material_request(data, user_id):
    request_no = generate_request_no()
    project_id = get_or_create_project(data["project"])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO quotation.material_requests (
            request_no,
            project_id,
            request_description,
            requested_by,
            assigned_to,
            priority,
            status,
            due_date,
            remarks,
            created_by
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING request_no
        """,
        (
            request_no,
            project_id,
            data["description"],
            data["requested_by"],
            data["assigned_to"],
            data["priority"],
            data["status"],
            data["due_date"],
            data["remarks"],
            user_id
        )
    )

    saved_request_no = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return saved_request_no