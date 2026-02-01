
-- FIX DUPLICATES & ADD CONSTRAINT
-- 1. Deduplicate ref_pma (Keep the latest entry or arbitrary one)
DELETE FROM master.ref_pma a
USING master.ref_pma b
WHERE a.ctid < b.ctid
AND a.pma_code = b.pma_code;

-- 2. Add Primary Key (if not exists) to prevent future duplicates
-- This ensures 'pma_code' is unique.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ref_pma_pkey'
    ) THEN
        ALTER TABLE master.ref_pma
        ADD CONSTRAINT ref_pma_pkey PRIMARY KEY (pma_code);
    END IF;
END $$;
