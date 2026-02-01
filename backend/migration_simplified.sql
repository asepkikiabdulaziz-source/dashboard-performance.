-- MIGRATION SCRIPT: FLATTEN PMA HIERARCHY (SIMPLIFIED)
-- Run this in Supabase SQL Editor

-- 1. Add 'distributor_id' column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'master' AND table_name = 'ref_pma' AND column_name = 'distributor_id') THEN
        ALTER TABLE master.ref_pma ADD COLUMN distributor_id text;
        RAISE NOTICE 'Column distributor_id added to master.ref_pma';
    END IF;
END $$;

-- 2. Migrate Data: Copy 'parent_kd_dist' from Mapping Table to 'distributor_id'
UPDATE master.ref_pma p
SET distributor_id = m.parent_kd_dist
FROM master.map_distributor_ori m
WHERE p.company_id = m.company_id 
  AND p.kd_dist_ori = m.kd_dist_ori;

RAISE NOTICE 'Data migration completed. Distributor IDs populated.';

-- 3. Add Foreign Key Constraint (Robust)
-- We assume ref_distributors PK is 'kd_dist' (based on user info).
-- If 'kd_dist' doesn't exist or isn't unique, this block will catch the error but keep the data.
DO $$
BEGIN
    BEGIN
        ALTER TABLE master.ref_pma 
        ADD CONSTRAINT fk_pma_distributor 
        FOREIGN KEY (distributor_id) 
        REFERENCES master.ref_distributors (kd_dist);
        
        RAISE NOTICE 'Foreign Key constraint fk_pma_distributor added successfully.';
    EXCEPTION 
        WHEN undefined_column THEN
            RAISE NOTICE 'WARNING: Could not add Foreign Key. Column kd_dist does not exist in ref_distributors.';
        WHEN invalid_foreign_key THEN
            RAISE NOTICE 'WARNING: Could not add Foreign Key. Values in distributor_id do not match ref_distributors.';
        WHEN duplicate_object THEN
            RAISE NOTICE 'Constraint already exists.';
        WHEN others THEN
             RAISE NOTICE 'WARNING: Failed to add constraint: %', SQLERRM;
    END;
END $$;
