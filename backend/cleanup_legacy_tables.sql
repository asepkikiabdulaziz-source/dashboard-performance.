-- CLEANUP SCRIPT: DROP LEGACY TABLES AND COLUMNS
-- WARNING: This will PERMANENTLY DELETE the old tables. 
-- Ensure you have run 'migration_lookup.sql' first!

-- 1. Drop Legacy Tables (Cascade will remove FK constraints in other tables automatically)
DROP TABLE IF EXISTS master.map_distributor_ori CASCADE;
DROP TABLE IF EXISTS master.ref_regions CASCADE;
DROP TABLE IF EXISTS master.ref_grbm CASCADE;

RAISE NOTICE 'Legacy tables (map_distributor_ori, ref_regions, ref_grbm) dropped.';

-- 2. Drop Legacy Columns in Ref Branches
-- We now use 'region_code' and 'grbm_code', so 'region_id' is obsolete.
ALTER TABLE master.ref_branches 
DROP COLUMN IF EXISTS region_id;

RAISE NOTICE 'Legacy column region_id removed from ref_branches.';

-- 3. Validation: Verify ref_lookup is still populated
DO $$
DECLARE
    cnt integer;
BEGIN
    SELECT count(*) INTO cnt FROM master.ref_lookup;
    RAISE NOTICE 'Remaining Master Data in ref_lookup: % records', cnt;
END $$;
