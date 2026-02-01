
-- FIX STRUCTURE: Link PMA to Distributors
-- This ensures the hierarchy: Distributor -> PMA

-- 1. Ensure distributor_id exists (it was created in ref_pma before, but let's be safe)
-- It should already exist as text.

-- 2. Add Foreign Key Constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_pma_distributor'
    ) THEN
        ALTER TABLE master.ref_pma
        ADD CONSTRAINT fk_pma_distributor
        FOREIGN KEY (distributor_id)
        REFERENCES master.ref_distributors(kd_dist);
    END IF;
END $$;
