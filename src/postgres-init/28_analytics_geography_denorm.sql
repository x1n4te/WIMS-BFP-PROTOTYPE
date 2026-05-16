-- 28_analytics_geography_denorm.sql
-- Dependencies: 11_analytics_facts.sql, 17_immutable_records.sql
-- Idempotent: YES
-- Adds analyst geography dimensions to the analytics read model.

BEGIN;

ALTER TABLE wims.analytics_incident_facts
    ADD COLUMN IF NOT EXISTS municipality_name TEXT,
    ADD COLUMN IF NOT EXISTS province_name TEXT;

CREATE INDEX IF NOT EXISTS idx_aif_municipality_name ON wims.analytics_incident_facts (municipality_name);
CREATE INDEX IF NOT EXISTS idx_aif_province_name ON wims.analytics_incident_facts (province_name);

ALTER TABLE wims.analytics_export_log
    ADD COLUMN IF NOT EXISTS columns_json JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS task_id TEXT,
    ADD COLUMN IF NOT EXISTS file_path TEXT,
    ADD COLUMN IF NOT EXISTS file_name TEXT,
    ADD COLUMN IF NOT EXISTS content_type TEXT,
    ADD COLUMN IF NOT EXISTS export_type TEXT NOT NULL DEFAULT 'analytics';

DROP POLICY IF EXISTS export_log_analyst_insert ON wims.analytics_export_log;
CREATE POLICY export_log_analyst_insert ON wims.analytics_export_log
    FOR INSERT
    WITH CHECK (
        user_id = wims.current_user_uuid()
        AND wims.current_user_role() IN ('SYSTEM_ADMIN', 'NATIONAL_ANALYST')
    );

DROP POLICY IF EXISTS export_log_self_or_admin_read ON wims.analytics_export_log;
CREATE POLICY export_log_self_or_admin_read ON wims.analytics_export_log
    FOR SELECT
    USING (
        wims.current_user_role() = 'SYSTEM_ADMIN'
        OR user_id = wims.current_user_uuid()
    );

GRANT INSERT, SELECT ON wims.analytics_export_log TO wims_app;
GRANT USAGE, SELECT ON SEQUENCE wims.analytics_export_log_export_id_seq TO wims_app;

COMMIT;
