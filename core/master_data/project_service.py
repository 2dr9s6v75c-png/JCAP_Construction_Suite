from core.database.connection import get_connection


def get_active_projects():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            p.id,
            p.project_code,
            p.project_name,
            c.client_name,
            p.location
        FROM core.projects p
        LEFT JOIN core.clients c ON p.client_id = c.id
        WHERE p.status = 'Active'
        ORDER BY p.project_name
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": str(row[0]),
            "project_code": row[1],
            "project_name": row[2],
            "client_name": row[3] or "",
            "location": row[4] or "",
        }
        for row in rows
    ]


def get_active_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, full_name, role
        FROM core.users
        WHERE is_active = TRUE
        ORDER BY full_name
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": str(row[0]),
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
        }
        for row in rows
    ]