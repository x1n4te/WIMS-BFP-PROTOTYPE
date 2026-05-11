-- 27_reference_sequence.sql
-- M4 P1 #2 Fix: Replace COUNT(*)-derived sequence with dedicated monotonic counter.
-- Prevents reference number reuse after archive/replace flows that would violate
-- the unique partial index on fire_incidents.reference_number.

BEGIN;

CREATE TABLE IF NOT EXISTS wims.reference_sequence (
    id          INTEGER PRIMARY KEY DEFAULT 0 CHECK (id = 0),
    current_value BIGINT NOT NULL DEFAULT 0
);

-- Initialize from MAX(suffix) of existing reference numbers to avoid a gap on deploy.
-- If no reference numbers exist yet, start at 0 (first incident gets 0001).
INSERT INTO wims.reference_sequence (id, current_value)
VALUES (0, COALESCE(
    (
        SELECT MAX(
            CAST(SUBSTRING(reference_number FROM 'AFOR-.*-(....)$') AS INTEGER)
        )
        FROM wims.fire_incidents
        WHERE reference_number IS NOT NULL
          AND reference_number ~ 'AFOR-.*-[0-9]{4}$'
    ),
    0
))
ON CONFLICT (id) DO UPDATE SET current_value = EXCLUDED.current_value;

COMMIT;

-- Verify
SELECT 'reference_sequence initialized' AS status, current_value
FROM wims.reference_sequence WHERE id = 0;