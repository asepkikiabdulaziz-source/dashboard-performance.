
-- 1. Add 'parent_code' column to ref_lookup if it doesn't exist
ALTER TABLE master.ref_lookup 
ADD COLUMN IF NOT EXISTS parent_code TEXT;

-- 2. Populate 'parent_code' for REGIONs based on existing Branch data (One-time sync)
-- This takes the implied relationship from branches and saves it permanently to the Region.
UPDATE master.ref_lookup r
SET parent_code = b.grbm_code
FROM (
    SELECT DISTINCT region_code, grbm_code 
    FROM master.ref_branches 
    WHERE region_code IS NOT NULL AND grbm_code IS NOT NULL
) b
WHERE r.code = b.region_code 
  AND r.category = 'REGION'
  AND r.parent_code IS NULL;

-- 3. Validation (Optional)
-- SELECT * FROM master.ref_lookup WHERE category = 'REGION';
