BEGIN;

DO $$
BEGIN
    IF current_database() <> 'jcap_construction_suite' THEN
        RAISE EXCEPTION
            'Migration stopped. Connected database is %, expected jcap_construction_suite.',
            current_database();
    END IF;

    IF to_regclass('quotation.material_requests') IS NULL THEN
        RAISE EXCEPTION
            'Migration stopped. quotation.material_requests does not exist.';
    END IF;

    IF to_regclass('core.users') IS NULL THEN
        RAISE EXCEPTION
            'Migration stopped. core.users does not exist.';
    END IF;
END
$$;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS quotation.supplier_quotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_request_id UUID NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    quotation_reference VARCHAR(100),
    quotation_date DATE,
    remarks TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Received',
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,

    CONSTRAINT supplier_quotations_material_request_fk
        FOREIGN KEY (material_request_id)
        REFERENCES quotation.material_requests(id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT supplier_quotations_created_by_fk
        FOREIGN KEY (created_by)
        REFERENCES core.users(id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT supplier_quotations_updated_by_fk
        FOREIGN KEY (updated_by)
        REFERENCES core.users(id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT supplier_quotations_supplier_name_not_blank
        CHECK (BTRIM(supplier_name) <> ''),

    CONSTRAINT supplier_quotations_status_check
        CHECK (
            status IN (
                'Received',
                'Under Review',
                'Clarification Required',
                'Accepted',
                'Rejected'
            )
        )
);

CREATE TABLE IF NOT EXISTS quotation.supplier_quotation_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_quotation_id UUID NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    folder_path TEXT NOT NULL,
    file_extension VARCHAR(20),
    file_size BIGINT,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploaded_by UUID NOT NULL,

    CONSTRAINT supplier_quotation_files_quotation_fk
        FOREIGN KEY (supplier_quotation_id)
        REFERENCES quotation.supplier_quotations(id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT supplier_quotation_files_uploaded_by_fk
        FOREIGN KEY (uploaded_by)
        REFERENCES core.users(id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT supplier_quotation_files_original_name_not_blank
        CHECK (BTRIM(original_filename) <> ''),

    CONSTRAINT supplier_quotation_files_stored_name_not_blank
        CHECK (BTRIM(stored_filename) <> ''),

    CONSTRAINT supplier_quotation_files_size_check
        CHECK (file_size IS NULL OR file_size >= 0)
);

CREATE INDEX IF NOT EXISTS idx_supplier_quotations_material_request
    ON quotation.supplier_quotations(material_request_id);

CREATE INDEX IF NOT EXISTS idx_supplier_quotations_supplier_name
    ON quotation.supplier_quotations(LOWER(supplier_name));

CREATE INDEX IF NOT EXISTS idx_supplier_quotations_status
    ON quotation.supplier_quotations(status);

CREATE INDEX IF NOT EXISTS idx_supplier_quotations_archived
    ON quotation.supplier_quotations(is_archived);

CREATE INDEX IF NOT EXISTS idx_supplier_quotation_files_quotation
    ON quotation.supplier_quotation_files(supplier_quotation_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_supplier_quotation_files_stored_name
    ON quotation.supplier_quotation_files(
        supplier_quotation_id,
        stored_filename
    );

COMMIT;

SELECT
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_schema = 'quotation'
  AND table_name IN (
      'supplier_quotations',
      'supplier_quotation_files'
  )
ORDER BY table_name;

SELECT
    tc.table_name,
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
  AND tc.table_name IN (
      'supplier_quotations',
      'supplier_quotation_files'
  )
ORDER BY tc.table_name, kcu.column_name;

SELECT
    (SELECT COUNT(*) FROM quotation.supplier_quotations)
        AS supplier_quotation_count,
    (SELECT COUNT(*) FROM quotation.supplier_quotation_files)
        AS supplier_quotation_file_count;