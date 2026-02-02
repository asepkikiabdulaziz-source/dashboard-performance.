-- MIGRATION SCRIPT: UNIVERSAL LOOKUP & HIERARCHY FLATTENING
-- Run this in Supabase SQL Editor

-- 1. Create Universal Lookup Table
CREATE TABLE IF NOT EXISTS master.ref_lookup (
    company_id text NOT NULL, -- Multitenancy support
    category text NOT NULL,   -- 'REGION', 'GRBM', 'PRICE_ZONE'
    code text NOT NULL,       -- Original ID (e.g., 'R01', 'LP-1')
    name text NOT NULL,       -- Human readable name
    description text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT pk_ref_lookup PRIMARY KEY (company_id, category, code)
);

-- Index for fast validation
CREATE INDEX IF NOT EXISTS idx_ref_lookup_cat ON master.ref_lookup (category, code);

-- 2. Migrate Data: GRBM (Grand Region)
INSERT INTO master.ref_lookup (company_id, category, code, name)
SELECT DISTINCT company_id, 'GRBM', id, name 
FROM master.ref_grbm
ON CONFLICT DO NOTHING;

-- 3. Migrate Data: REGION
INSERT INTO master.ref_lookup (company_id, category, code, name)
SELECT DISTINCT company_id, 'REGION', id, name 
FROM master.ref_regions
ON CONFLICT DO NOTHING;

-- 4. Migrate Data: PRICE ZONES (Optional but recommended)
-- Remove comment wrapping if table 'price_zones' exists
/*
INSERT INTO master.ref_lookup (company_id, category, code, name)
SELECT DISTINCT company_id, 'PRICE_ZONE', id, description 
FROM master.price_zones
ON CONFLICT DO NOTHING;
*/

RAISE NOTICE 'Data migration to ref_lookup completed.';

-- 5. Flatten Branch Hierarchy
-- Add columns to ref_branches to store the Flattened Codes
ALTER TABLE master.ref_branches 
ADD COLUMN IF NOT EXISTS region_code text,
ADD COLUMN IF NOT EXISTS grbm_code text;

-- Populate region_code (Direct mapping)
UPDATE master.ref_branches b
SET region_code = b.region_id
WHERE b.region_code IS NULL;

-- Populate grbm_code (Derived from Region linkage)
-- We fetch the GRBM ID from the old ref_regions table
UPDATE master.ref_branches b
SET grbm_code = r.grbm_id
FROM master.ref_regions r
WHERE b.region_id = r.id 
  AND b.company_id = r.company_id 
  AND b.grbm_code IS NULL;

RAISE NOTICE 'Branch hierarchy flattened. Columns region_code and grbm_code populated.';

-- 6. (Optional) Validation Check
-- Verify that all region_codes in Branch actually exist in Lookup
DO $$
DECLARE
    orphan_count integer;
BEGIN
    SELECT count(*) INTO orphan_count
    FROM master.ref_branches b
    WHERE b.region_code IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM master.ref_lookup l 
          WHERE l.company_id = b.company_id 
            AND l.category = 'REGION' 
            AND l.code = b.region_code
      );
      
    IF orphan_count > 0 THEN
        RAISE NOTICE 'WARNING: Found % branches with invalid Region Codes (Not in Lookup).', orphan_count;
    ELSE
        RAISE NOTICE 'Validation Passed: All Branch Regions are valid.';
    END IF;
END $$;
