-- =============================================================================
-- WF-006: Google Cloud SQL (PostgreSQL) Transactional Schema
-- Master Contact & Governance Tables with CDC Datastream Support
-- =============================================================================

-- Ensure UUID and crypto extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. Master Contacts Table (Operational Single Source of Truth)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    contact_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(32),
    email VARCHAR(255),
    source VARCHAR(64) NOT NULL,
    owner VARCHAR(128) NOT NULL,
    consent_status VARCHAR(32) DEFAULT 'PENDING',
    dnd_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Optimize search and lookup paths
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_source ON contacts(source);
CREATE INDEX IF NOT EXISTS idx_contacts_owner ON contacts(owner);
CREATE INDEX IF NOT EXISTS idx_contacts_updated_at ON contacts(updated_at DESC);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_contacts_updated_at ON contacts;
CREATE TRIGGER trigger_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- -----------------------------------------------------------------------------
-- 2. Contact Audit Log Table (Decision & Governance Traceability)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    contact_id VARCHAR(64) NOT NULL,
    decision VARCHAR(32) NOT NULL,        -- 'APPROVED', 'BLOCKED', 'VALIDATION_FAILED'
    reason TEXT NOT NULL,                -- Explanation (e.g. 'Phone in DND list')
    metadata JSONB,                      -- Complete payload snapshot / debug info
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_contact_id ON contact_audit_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON contact_audit_log(decision);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON contact_audit_log(created_at DESC);

-- -----------------------------------------------------------------------------
-- 3. Datastream (CDC) Replication Setup Commands
-- Note: Requires Cloud SQL database flag 'cloudsql.logical_decoding = on'
-- -----------------------------------------------------------------------------
-- Step 3a: Create replication publication for Datastream
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication WHERE pubname = 'wf006_publication'
    ) THEN
        CREATE PUBLICATION wf006_publication FOR TABLE contacts, contact_audit_log;
    END IF;
END
$$;

-- Step 3b: Dedicated user for Datastream CDC (run in Cloud SQL console)
-- CREATE USER datastream_user WITH REPLICATION ENCRYPTED PASSWORD 'replace_with_secure_password';
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO datastream_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO datastream_user;
