-- ============================================================
-- JCAP Construction Suite
-- Phase 1 - Site Master
-- File: database/migrations/phase_1/create_master_sites.sql
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS master;

CREATE TABLE IF NOT EXISTS master.sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    site_code VARCHAR(50) NOT NULL,
    site_name VARCHAR(255) NOT NULL,
    project_id UUID NOT NULL,

    remarks TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,

    CONSTRAINT fk_master_sites_project
        FOREIGN KEY (project_id)
        REFERENCES master.projects (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_master_sites_created_by
        FOREIGN KEY (created_by)
        REFERENCES core.users (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_master_sites_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES core.users (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_master_sites_code_not_blank
        CHECK (BTRIM(site_code) <> ''),

    CONSTRAINT chk_master_sites_name_not_blank
        CHECK (BTRIM(site_name) <> '')
);

-- Site codes are permanent identifiers and must remain globally unique.
CREATE UNIQUE INDEX IF NOT EXISTS uq_master_sites_site_code
    ON master.sites (LOWER(site_code));

-- Only one active site with the same name may exist for the same project.
-- An archived site may retain its historical name.
CREATE UNIQUE INDEX IF NOT EXISTS uq_master_sites_active_project_name
    ON master.sites (
        project_id,
        LOWER(BTRIM(site_name))
    )
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_master_sites_project_id
    ON master.sites (project_id);

CREATE INDEX IF NOT EXISTS ix_master_sites_is_active
    ON master.sites (is_active);

CREATE INDEX IF NOT EXISTS ix_master_sites_site_name
    ON master.sites (LOWER(site_name));

CREATE INDEX IF NOT EXISTS ix_master_sites_created_at
    ON master.sites (created_at DESC);

COMMENT ON TABLE master.sites IS
    'Site Master records linked to Project Master records for Phase 1 material request and quotation workflows.';

COMMENT ON COLUMN master.sites.site_code IS
    'System-generated site code such as SIT-000001.';

COMMENT ON COLUMN master.sites.project_id IS
    'Owning active or historical Project Master record.';

COMMENT ON COLUMN master.sites.is_active IS
    'Soft-delete flag. FALSE means the site is archived.';

COMMIT;