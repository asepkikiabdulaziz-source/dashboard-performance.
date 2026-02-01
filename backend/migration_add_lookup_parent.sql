
-- ADD parent_code to ref_lookup to support hierarchies (e.g. Region -> GRBM)
BEGIN;

ALTER TABLE master.ref_lookup 
ADD COLUMN IF NOT EXISTS parent_code TEXT;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_ref_lookup_parent ON master.ref_lookup(parent_code);

COMMIT;
