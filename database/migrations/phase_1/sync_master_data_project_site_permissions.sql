BEGIN;

-- ============================================================
-- PHASE 1 MASTER DATA RBAC SYNCHRONIZATION
-- Projects and Sites
--
-- Safe to run more than once:
-- - Missing permissions are inserted only when absent.
-- - Existing role-permission assignments are not duplicated.
-- ============================================================

-- ============================================================
-- 1. REGISTER MISSING PROJECT AND SITE PERMISSIONS
-- ============================================================

INSERT INTO core.permissions (
    permission_name,
    description
)
SELECT
    new_permission.permission_name,
    new_permission.description
FROM (
    VALUES
        (
            'master_data.projects.view',
            'View Project Master records'
        ),
        (
            'master_data.projects.create',
            'Create Project Master records'
        ),
        (
            'master_data.projects.edit',
            'Edit Project Master records'
        ),
        (
            'master_data.projects.archive',
            'Deactivate or archive Project Master records'
        ),
        (
            'master_data.projects.restore',
            'Restore inactive Project Master records'
        ),
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
) AS new_permission (
    permission_name,
    description
)
WHERE NOT EXISTS (
    SELECT 1
    FROM core.permissions existing_permission
    WHERE LOWER(existing_permission.permission_name) =
          LOWER(new_permission.permission_name)
);

-- ============================================================
-- 2. VIEW PERMISSIONS
-- All current Phase 1 roles may view Project and Site masters.
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
CROSS JOIN core.permissions permission_record
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
AND LOWER(permission_record.permission_name) IN (
    LOWER('master_data.projects.view'),
    LOWER('master_data.sites.view')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- 3. CREATE AND EDIT PERMISSIONS
-- System Administrator, Purchasing Manager, Purchasing Officer.
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
CROSS JOIN core.permissions permission_record
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager'),
    LOWER('Purchasing Officer')
)
AND LOWER(permission_record.permission_name) IN (
    LOWER('master_data.projects.create'),
    LOWER('master_data.projects.edit'),
    LOWER('master_data.sites.create'),
    LOWER('master_data.sites.edit')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

-- ============================================================
-- 4. ARCHIVE AND RESTORE PERMISSIONS
-- System Administrator and Purchasing Manager only.
-- ============================================================

INSERT INTO core.role_permissions (
    role_id,
    permission_id
)
SELECT
    role_record.id,
    permission_record.id
FROM core.roles role_record
CROSS JOIN core.permissions permission_record
WHERE LOWER(role_record.role_name) IN (
    LOWER('System Administrator'),
    LOWER('Purchasing Manager')
)
AND LOWER(permission_record.permission_name) IN (
    LOWER('master_data.projects.archive'),
    LOWER('master_data.projects.restore'),
    LOWER('master_data.sites.archive'),
    LOWER('master_data.sites.restore')
)
ON CONFLICT (
    role_id,
    permission_id
)
DO NOTHING;

COMMIT;

-- ============================================================
-- VERIFICATION
-- Expected:
-- - 10 permission names
-- - System Administrator has all 10
-- - Purchasing Manager has all 10
-- - Purchasing Officer has View/Create/Edit for both modules
-- ============================================================

SELECT
    permission_record.permission_name,
    role_record.role_name
FROM core.permissions permission_record
LEFT JOIN core.role_permissions role_permission
    ON role_permission.permission_id = permission_record.id
LEFT JOIN core.roles role_record
    ON role_record.id = role_permission.role_id
WHERE permission_record.permission_name LIKE 'master_data.projects.%'
   OR permission_record.permission_name LIKE 'master_data.sites.%'
ORDER BY
    permission_record.permission_name,
    role_record.role_name;