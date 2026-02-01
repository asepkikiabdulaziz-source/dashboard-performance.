
-- 1. Add price_zone_code to ref_distributors
ALTER TABLE master.ref_distributors 
ADD COLUMN IF NOT EXISTS price_zone_code TEXT;

-- 2. Clean up: Remove price_zone_code from ref_lookup (since it was a mistake)
ALTER TABLE master.ref_lookup 
DROP COLUMN IF EXISTS price_zone_code;

-- 3. Verification
-- SELECT * FROM information_schema.columns WHERE table_name = 'ref_distributors' AND column_name = 'price_zone_code';
