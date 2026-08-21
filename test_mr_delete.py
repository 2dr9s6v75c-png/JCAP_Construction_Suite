from core.database.connection import get_connection
from modules.quotation.services.material_request_service import (
    delete_material_request,
)


TEST_MR = "MR-2026-000015"


# ============================================================
# 1. FIND THE CONTROLLED TEST MR
# ============================================================

conn = get_connection()
cur = conn.cursor()

try:
    cur.execute(
        """
        SELECT
            id,
            mr_number,
            request_description
        FROM quotation.material_requests
        WHERE mr_number = %s
        """,
        (TEST_MR,),
    )

    row = cur.fetchone()

finally:
    cur.close()
    conn.close()


if not row:
    raise RuntimeError(
        f"{TEST_MR} was not found. Nothing was deleted."
    )


material_request_id = str(row[0])

print("MR ID:", material_request_id)
print("MR Number:", row[1])
print("Description:", row[2])


# ============================================================
# 2. LOAD AN ACTIVE SYSTEM ADMINISTRATOR
# ============================================================

conn = get_connection()
cur = conn.cursor()

try:
    cur.execute(
        """
        SELECT
            u.id,
            u.username,
            u.full_name,
            u.role_id,
            r.role_name
        FROM core.users u
        JOIN core.roles r
            ON r.id = u.role_id
        WHERE LOWER(r.role_name) = LOWER(%s)
          AND u.is_active = TRUE
        ORDER BY u.created_at
        LIMIT 1
        """,
        ("System Administrator",),
    )

    user_row = cur.fetchone()

finally:
    cur.close()
    conn.close()


if not user_row:
    raise RuntimeError(
        "No active System Administrator account was found. "
        "Nothing was deleted."
    )


user = {
    "id": str(user_row[0]),
    "username": user_row[1],
    "full_name": user_row[2],
    "role_id": str(user_row[3]),
    "role_name": user_row[4],
    "role": user_row[4],
}


print()
print("Deletion user:")
print("Username:", user["username"])
print("Full Name:", user["full_name"])
print("Role:", user["role_name"])


# ============================================================
# 3. CONFIRM DELETE PERMISSION
# ============================================================

from core.security.permissions import PermissionService

has_delete_permission = (
    PermissionService.can_delete_material_request(user)
)

print()
print(
    "material_requests.delete permission:",
    has_delete_permission,
)


if not has_delete_permission:
    raise RuntimeError(
        "Selected System Administrator does not have "
        "material_requests.delete. Nothing was deleted."
    )


# ============================================================
# 4. PERMANENT DELETE THROUGH THE REAL SERVICE
# ============================================================

print()
print("Calling delete_material_request()...")

deleted_mr = delete_material_request(
    material_request_id,
    user,
)

print()
print("DELETE SUCCESSFUL:", deleted_mr)