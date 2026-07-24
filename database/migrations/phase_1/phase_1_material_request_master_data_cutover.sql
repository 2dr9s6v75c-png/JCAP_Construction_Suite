BEGIN;

-- ============================================================
-- PHASE 1: MATERIAL REQUEST MASTER DATA CUTOVER
-- Database: jcap_construction_suite
--
-- Preconditions:
--   - Material Request transactional test records were cleared.
--   - master.projects and master.sites contain valid test data.
--
-- Changes:
--   - project_id now references master.projects(id)
--   - site_id is added and references master.sites(id)
--   - site_id is required for every new Material Request
-- ============================================================

DO $$
BEGIN
    IF current_database() <> 'jcap_construction_suite' THEN
        RAISE EXCEPTION
            'Migration stopped. Connected database is %, expected jcap_construction_suite.',
            current_database();
    END IF;

    IF EXISTS (
        SELECT 1
        FROM quotation.material_requests
    ) THEN
        RAISE EXCEPTION
            'Migration stopped. quotation.material_requests must be empty before cutover.';
    END IF;

    IF to_regclass('master.projects') IS NULL
       OR to_regclass('master.sites') IS NULL THEN
        RAISE EXCEPTION
            'Migration stopped. master.projects and master.sites are required.';
    END IF;
END
$$;

-- Drop the current project foreign key regardless of its generated name.
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
           AND tc.constraint_schema = kcu.constraint_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'quotation'
          AND tc.table_name = 'material_requests'
          AND kcu.column_name = 'project_id'
    LOOP
        EXECUTE format(
            'ALTER TABLE quotation.material_requests DROP CONSTRAINT %I',
            constraint_record.constraint_name
        );
    END LOOP;
END
$$;

ALTER TABLE quotation.material_requests
    ADD CONSTRAINT material_requests_project_id_fk
    FOREIGN KEY (project_id)
    REFERENCES master.projects(id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;

ALTER TABLE quotation.material_requests
    ADD COLUMN IF NOT EXISTS site_id UUID;

ALTER TABLE quotation.material_requests
    ALTER COLUMN site_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'quotation'
          AND tc.table_name = 'material_requests'
          AND tc.constraint_name = 'material_requests_site_id_fk'
    ) THEN
        ALTER TABLE quotation.material_requests
            ADD CONSTRAINT material_requests_site_id_fk
            FOREIGN KEY (site_id)
            REFERENCES master.sites(id)
            ON UPDATE RESTRICT
            ON DELETE RESTRICT;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_material_requests_project_id
    ON quotation.material_requests(project_id);

CREATE INDEX IF NOT EXISTS idx_material_requests_site_id
    ON quotation.material_requests(site_id);

COMMIT;

-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'quotation'
  AND table_name = 'material_requests'
  AND column_name IN ('project_id', 'site_id')
ORDER BY ordinal_position;

SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_schema AS referenced_schema,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.constraint_schema = kcu.constraint_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
   AND ccu.constraint_schema = tc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'quotation'
  AND tc.table_name = 'material_requests'
  AND kcu.column_name IN ('project_id', 'site_id')
ORDER BY kcu.column_name;