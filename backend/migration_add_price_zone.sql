
-- Add price_zone_code to ref_lookup for Regions
ALTER TABLE master.ref_lookup 
ADD COLUMN IF NOT EXISTS price_zone_code TEXT;

-- Verify
-- SELECT * FROM information_schema.columns WHERE table_schema = 'master' AND table_name = 'ref_lookup';
