-- ============================================================
-- JCAP Construction Suite
-- Phase 1 - Project Master
-- File: database/migrations/phase_1/create_master_projects.sql
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS master;

CREATE TABLE IF NOT EXISTS master.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project_code VARCHAR(50) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    client_id UUID NOT NULL,

    remarks TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,

    CONSTRAINT fk_master_projects_client
        FOREIGN KEY (client_id)
        REFERENCES master.clients (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_master_projects_created_by
        FOREIGN KEY (created_by)
        REFERENCES core.users (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_master_projects_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES core.users (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_master_projects_code_not_blank
        CHECK (BTRIM(project_code) <> ''),

    CONSTRAINT chk_master_projects_name_not_blank
        CHECK (BTRIM(project_name) <> '')
);

-- Project codes are permanent identifiers and must remain globally unique.
CREATE UNIQUE INDEX IF NOT EXISTS uq_master_projects_project_code
    ON master.projects (LOWER(project_code));

-- Only one active project with the same name may exist for the same client.
-- An archived project may retain its historical name.
CREATE UNIQUE INDEX IF NOT EXISTS uq_master_projects_active_client_name
    ON master.projects (
        client_id,
        LOWER(BTRIM(project_name))
    )
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_master_projects_client_id
    ON master.projects (client_id);

CREATE INDEX IF NOT EXISTS ix_master_projects_is_active
    ON master.projects (is_active);

CREATE INDEX IF NOT EXISTS ix_master_projects_project_name
    ON master.projects (LOWER(project_name));

CREATE INDEX IF NOT EXISTS ix_master_projects_created_at
    ON master.projects (created_at DESC);

COMMENT ON TABLE master.projects IS
    'Project Master records used by Material Requests and Phase 1 quotation workflows.';

COMMENT ON COLUMN master.projects.project_code IS
    'System-generated project code such as PRJ-000001.';

COMMENT ON COLUMN master.projects.client_id IS
    'Owning active or historical Client Master record.';

COMMENT ON COLUMN master.projects.is_active IS
    'Soft-delete flag. FALSE means the project is archived.';

COMMIT;