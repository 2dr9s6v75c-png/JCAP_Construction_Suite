BEGIN;

-- ============================================================
-- PHASE 1 DEVELOPMENT TRANSACTION RESET
-- Database: jcap_construction_suite
--
-- PURPOSE
--   Remove Material Request test transactions only.
--
-- PRESERVED
--   - Users
--   - Roles and permissions
--   - Master clients, projects, and sites
--   - Numbering configuration
--   - Application settings
--
-- IMPORTANT
--   This script intentionally does not modify table structures.
--   It prepares the development database for the controlled
--   Material Request migration to master.projects/master.sites.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Safety check: stop if connected to another database
-- ------------------------------------------------------------

DO $$
BEGIN
    IF current_database() <> 'jcap_construction_suite' THEN
        RAISE EXCEPTION
            'Reset stopped. Connected database is %, expected jcap_construction_suite.',
            current_database();
    END IF;
END
$$;

-- ------------------------------------------------------------
-- 2. Safety check: confirm required transaction tables exist
-- ------------------------------------------------------------

DO $$
DECLARE
    required_table TEXT;
BEGIN
    FOREACH required_table IN ARRAY ARRAY[
        'quotation.material_requests',
        'quotation.material_request_assignments',
        'quotation.clarifications',
        'quotation.clarification_messages',
        'quotation.material_request_attachments',
        'quotation.material_request_items',
        'quotation.attachments',
        'quotation.record_locks'
    ]
    LOOP
        IF to_regclass(required_table) IS NULL THEN
            RAISE EXCEPTION
                'Reset stopped. Required table % does not exist.',
                required_table;
        END IF;
    END LOOP;
END
$$;

-- ------------------------------------------------------------
-- 3. Break the Material Request -> current assignment reference
--    before deleting assignment records
-- ------------------------------------------------------------

UPDATE quotation.material_requests
SET current_assignment_id = NULL
WHERE current_assignment_id IS NOT NULL;

-- ------------------------------------------------------------
-- 4. Delete second-level dependent records first
-- ------------------------------------------------------------

DELETE FROM quotation.clarification_messages;

-- ------------------------------------------------------------
-- 5. Delete direct Material Request child records
-- ------------------------------------------------------------

DELETE FROM quotation.clarifications;
DELETE FROM quotation.material_request_attachments;
DELETE FROM quotation.material_request_items;
DELETE FROM quotation.attachments;
DELETE FROM quotation.record_locks;

-- ------------------------------------------------------------
-- 6. Delete assignment records after the current assignment
--    reference has been cleared
-- ------------------------------------------------------------

DELETE FROM quotation.material_request_assignments;

-- ------------------------------------------------------------
-- 7. Delete Material Request test records
-- ------------------------------------------------------------

DELETE FROM quotation.material_requests;

COMMIT;

-- ============================================================
-- VERIFICATION
-- Every record_count below should be 0.
-- ============================================================

SELECT
    'quotation.clarification_messages' AS table_name,
    COUNT(*) AS record_count
FROM quotation.clarification_messages

UNION ALL

SELECT
    'quotation.clarifications',
    COUNT(*)
FROM quotation.clarifications

UNION ALL

SELECT
    'quotation.material_request_attachments',
    COUNT(*)
FROM quotation.material_request_attachments

UNION ALL

SELECT
    'quotation.material_request_items',
    COUNT(*)
FROM quotation.material_request_items

UNION ALL

SELECT
    'quotation.attachments',
    COUNT(*)
FROM quotation.attachments

UNION ALL

SELECT
    'quotation.record_locks',
    COUNT(*)
FROM quotation.record_locks

UNION ALL

SELECT
    'quotation.material_request_assignments',
    COUNT(*)
FROM quotation.material_request_assignments

UNION ALL

SELECT
    'quotation.material_requests',
    COUNT(*)
FROM quotation.material_requests

ORDER BY table_name;

-- Confirm Master Data was preserved.
SELECT
    (SELECT COUNT(*) FROM master.clients) AS master_clients,
    (SELECT COUNT(*) FROM master.projects) AS master_projects,
    (SELECT COUNT(*) FROM master.sites) AS master_sites;