-- =============================================================================
-- WF-006: Google BigQuery Analytical Schemas & Curated Views
-- Consumes replicated CDC data from Cloud SQL via Datastream
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Create Analytics Dataset (US or regional multi-region)
-- -----------------------------------------------------------------------------
-- CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.wf006_analytics`
-- OPTIONS (
--   location = 'US',
--   description = 'WF-006 Contact Governance and Analytics Master Dataset'
-- );

-- -----------------------------------------------------------------------------
-- 2. Staging / Replicated Contacts Table (Target for Datastream CDC)
-- Datastream automatically creates or writes to this schema
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `wf006_analytics.contacts_raw` (
    contact_id STRING NOT NULL,
    name STRING,
    phone STRING,
    email STRING,
    source STRING NOT NULL,
    owner STRING NOT NULL,
    consent_status STRING,
    dnd_status BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    -- Datastream CDC Metadata Columns:
    _metadata_timestamp TIMESTAMP,
    _metadata_deleted BOOLEAN,
    _metadata_change_type STRING
)
PARTITION BY DATE(created_at)
CLUSTER BY source, owner;

-- -----------------------------------------------------------------------------
-- 3. Staging / Replicated Audit Log Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `wf006_analytics.contact_audit_log_raw` (
    log_id INT64,
    contact_id STRING,
    decision STRING,
    reason STRING,
    metadata JSON,
    created_at TIMESTAMP,
    _metadata_timestamp TIMESTAMP,
    _metadata_deleted BOOLEAN
)
PARTITION BY DATE(created_at)
CLUSTER BY decision, contact_id;

-- -----------------------------------------------------------------------------
-- 4. Curated View: Current Approved Operational Master Contacts
-- Deduplicates CDC updates and retains only the latest non-deleted record
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `wf006_analytics.v_active_approved_contacts` AS
WITH ranked_contacts AS (
    SELECT
        contact_id,
        name,
        phone,
        email,
        source,
        owner,
        consent_status,
        dnd_status,
        created_at,
        updated_at,
        _metadata_timestamp,
        _metadata_deleted,
        ROW_NUMBER() OVER (
            PARTITION BY contact_id 
            ORDER BY COALESCE(_metadata_timestamp, updated_at) DESC
        ) AS row_num
    FROM `wf006_analytics.contacts_raw`
)
SELECT
    contact_id,
    name,
    phone,
    email,
    source,
    owner,
    consent_status,
    dnd_status,
    created_at,
    updated_at
FROM ranked_contacts
WHERE row_num = 1
  AND COALESCE(_metadata_deleted, FALSE) = FALSE
  AND COALESCE(dnd_status, FALSE) = FALSE;

-- -----------------------------------------------------------------------------
-- 5. Curated View: Governance & DND Block Summary Report
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `wf006_analytics.v_governance_decision_summary` AS
SELECT
    DATE(a.created_at) AS decision_date,
    a.decision,
    a.reason,
    COUNT(DISTINCT a.contact_id) AS total_contacts,
    COUNT(a.log_id) AS total_events
FROM `wf006_analytics.contact_audit_log_raw` a
GROUP BY decision_date, a.decision, a.reason
ORDER BY decision_date DESC, total_events DESC;

-- -----------------------------------------------------------------------------
-- 6. Curated View: Source-wise Compliance Ratio
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `wf006_analytics.v_source_compliance_metrics` AS
SELECT
    c.source,
    COUNT(DISTINCT c.contact_id) AS total_ingested_contacts,
    COUNTIF(c.dnd_status = TRUE) AS dnd_blocked_count,
    COUNTIF(c.dnd_status = FALSE) AS approved_count,
    ROUND(SAFE_DIVIDE(COUNTIF(c.dnd_status = TRUE) * 100.0, COUNT(DISTINCT c.contact_id)), 2) AS dnd_blocked_percentage
FROM `wf006_analytics.contacts_raw` c
WHERE COALESCE(c._metadata_deleted, FALSE) = FALSE
GROUP BY c.source;
