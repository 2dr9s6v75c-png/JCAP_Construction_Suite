BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS master;

CREATE TABLE IF NOT EXISTS master.clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    client_code VARCHAR(30) NOT NULL,
    client_name VARCHAR(255) NOT NULL,

    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    remarks TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_by UUID,
    updated_at TIMESTAMPTZ,

    CONSTRAINT uq_master_clients_client_code
        UNIQUE (client_code),

    CONSTRAINT fk_master_clients_created_by
        FOREIGN KEY (created_by)
        REFERENCES core.users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_master_clients_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES core.users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_master_clients_client_code_not_blank
        CHECK (BTRIM(client_code) <> ''),

    CONSTRAINT ck_master_clients_client_name_not_blank
        CHECK (BTRIM(client_name) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_master_clients_active_name_ci
ON master.clients (
    LOWER(BTRIM(client_name))
)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS
    ix_master_clients_client_name_ci
ON master.clients (
    LOWER(client_name)
);

CREATE INDEX IF NOT EXISTS
    ix_master_clients_is_active
ON master.clients (
    is_active
);

CREATE INDEX IF NOT EXISTS
    ix_master_clients_created_at
ON master.clients (
    created_at DESC
);

COMMENT ON TABLE master.clients IS
    'Client master records used by projects, sites, material requests, and future operational modules.';

COMMENT ON COLUMN master.clients.client_code IS
    'System-generated client identifier such as CLI-000001.';

COMMENT ON COLUMN master.clients.is_active IS
    'Soft-deletion state. Inactive client records remain available for audit and restoration.';

COMMIT;