
-- Drop the incorrectly created ref_products table
-- This table was created by mistake when master.products already existed

DROP TABLE IF EXISTS master.ref_products CASCADE;

-- Verification: Confirm master.products still exists
-- (This is just a comment - the table should remain intact)
