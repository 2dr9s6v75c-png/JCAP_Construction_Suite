BEGIN;

-- PHASE 1 MATERIAL REQUEST SITE INTEGRATION
-- Existing Material Requests are preserved.
-- Existing rows will keep site_id = NULL.
-- Safe to run more than once.

DO $$
BEGIN
    IF to_regclass('core.sites') IS NULL THEN
        RAISE EXCEPTION
            'Migration stopped: required table core.sites does not exist.';
    END IF;
END
$$;

ALTER TABLE quotation.material_requests
    ADD COLUMN IF NOT EXISTS site_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint constraint_record
        JOIN pg_class table_record
            ON table_record.oid = constraint_record.conrelid
        JOIN pg_namespace schema_record
            ON schema_record.oid = table_record.relnamespace
        WHERE constraint_record.conname =
              'material_requests_site_id_fk'
          AND schema_record.nspname = 'quotation'
          AND table_record.relname = 'material_requests'
    ) THEN
        ALTER TABLE quotation.material_requests
            ADD CONSTRAINT material_requests_site_id_fk
            FOREIGN KEY (site_id)
            REFERENCES core.sites(id)
            ON UPDATE RESTRICT
            ON DELETE RESTRICT;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_material_requests_site_id
    ON quotation.material_requests(site_id);

COMMIT;

-- VERIFICATION A: columns
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'quotation'
  AND table_name = 'material_requests'
  AND column_name IN ('project_id', 'site_id')
ORDER BY ordinal_position;

-- VERIFICATION B: foreign keys
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

-- VERIFICATION C: existing records
SELECT
    COUNT(*) AS material_request_count,
    COUNT(site_id) AS requests_with_site,
    COUNT(*) - COUNT(site_id) AS requests_without_site
FROM quotation.material_requests;

-- VERIFICATION D: index
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'quotation'
  AND tablename = 'material_requests'
  AND indexname = 'idx_material_requests_site_id';