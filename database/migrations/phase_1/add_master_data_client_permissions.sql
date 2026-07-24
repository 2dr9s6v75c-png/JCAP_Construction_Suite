BEGIN;

-- ============================================================
-- CLIENT MASTER PERMISSION REGISTRY
-- ============================================================

INSERT INTO core.permissions (
    permission_name,
    description
)
SELECT
    permission_name,
    description
FROM (
    VALUES
        (
            'master_data.clients.view',
            'View Client Master records'
        ),
        (
            'master_data.clients.create',
            'Create Client Master records'
        ),
        (
            'master_data.clients.edit',
            'Edit Client Master records'
        ),
        (
            'master_data.clients.archive',
            'Deactivate or archive Client Master records'
        ),
        (
            'master_data.clients.restore',
            'Restore inactive Client Master records'
        )
) AS new_permissions (
    permission_name,
    description
)
WHERE NOT EXISTS (
    SELECT 1
    FROM core.permissions existing_permission
    WHERE LOWER(existing_permission.permission_name) =
          LOWER(new_permissions.permission_name)
);

-- ============================================================
-- VIEW PERMISSION
-- Assigned to all current Phase 1 roles.
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
INNER JOIN core.permissions permission_record
    ON LOWER(permission_record.permission_name) =
       LOWER('master_data.clients.view')
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager'),
    LOWER('Purchasing Officer'),
    LOWER('Project Manager'),
    LOWER('Project Engineer'),
    LOWER('Accounting Personnel'),
    LOWER('Executive / Management'),
    LOWER('Warehouse Personnel'),
    LOWER('Viewer / Auditor')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- CREATE PERMISSION
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
INNER JOIN core.permissions permission_record
    ON LOWER(permission_record.permission_name) =
       LOWER('master_data.clients.create')
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager'),
    LOWER('Purchasing Officer')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- EDIT PERMISSION
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
INNER JOIN core.permissions permission_record
    ON LOWER(permission_record.permission_name) =
       LOWER('master_data.clients.edit')
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager'),
    LOWER('Purchasing Officer')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- ARCHIVE / DEACTIVATE PERMISSION
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
INNER JOIN core.permissions permission_record
    ON LOWER(permission_record.permission_name) =
       LOWER('master_data.clients.archive')
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- RESTORE PERMISSION
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
INNER JOIN core.permissions permission_record
    ON LOWER(permission_record.permission_name) =
       LOWER('master_data.clients.restore')
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

COMMIT;