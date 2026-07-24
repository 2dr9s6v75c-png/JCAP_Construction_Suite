BEGIN;

-- ============================================================
-- SITE MASTER PERMISSION REGISTRY
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
            'master_data.sites.view',
            'View Site Master records'
        ),
        (
            'master_data.sites.create',
            'Create Site Master records'
        ),
        (
            'master_data.sites.edit',
            'Edit Site Master records'
        ),
        (
            'master_data.sites.archive',
            'Deactivate or archive Site Master records'
        ),
        (
            'master_data.sites.restore',
            'Restore inactive Site Master records'
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
       LOWER('master_data.sites.view')
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
       LOWER('master_data.sites.create')
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
       LOWER('master_data.sites.edit')
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
       LOWER('master_data.sites.archive')
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
       LOWER('master_data.sites.restore')
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

-- ============================================================
-- OPTIONAL VERIFICATION QUERY
-- ============================================================

SELECT
    permission.permission_name,
    role_record.role_name
FROM core.permissions permission
LEFT JOIN core.role_permissions role_permission
    ON role_permission.permission_id = permission.id
LEFT JOIN core.roles role_record
    ON role_record.id = role_permission.role_id
WHERE permission.permission_name LIKE 'master_data.sites.%'
ORDER BY
    permission.permission_name,
    role_record.role_name;