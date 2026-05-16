-- 34_security_incident.sql
-- Dependencies: 33_incident_ai_narrative.sql
-- Idempotent: YES
-- Issue: #68 — [M6-F] Suricata IDS Integration

BEGIN;

-- Add security_alert_id FK to fire_incidents
ALTER TABLE wims.fire_incidents
    ADD COLUMN IF NOT EXISTS security_alert_id BIGINT
        REFERENCES wims.security_threat_logs(log_id)
        ON DELETE SET NULL;

COMMENT ON COLUMN wims.fire_incidents.security_alert_id IS
    'FK to security_threat_logs.log_id. Non-null for auto-created security incidents.';

CREATE INDEX IF NOT EXISTS idx_fire_incidents_security_alert
    ON wims.fire_incidents (security_alert_id)
    WHERE security_alert_id IS NOT NULL;

COMMIT;