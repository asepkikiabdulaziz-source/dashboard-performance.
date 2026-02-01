
-- FIX: Add Surrogate Key (UUID) to ref_pma to support duplicate pma_code
-- This is required because the user confirmed pma_code is NOT unique.

-- 1. Add 'id' column with default uuid generation
ALTER TABLE master.ref_pma
ADD COLUMN id uuid DEFAULT gen_random_uuid();

-- 2. Make it Primary Key
-- First, drop existing PK if any (likely pma_code was treated as PK implicitly or explicitly)
ALTER TABLE master.ref_pma DROP CONSTRAINT IF EXISTS ref_pma_pkey;

-- 3. Add new PK constraint on 'id'
ALTER TABLE master.ref_pma
ADD CONSTRAINT ref_pma_pkey PRIMARY KEY (id);

-- Optional: Index pma_code for faster lookups even if duplicates exist
CREATE INDEX IF NOT EXISTS idx_pma_code ON master.ref_pma (pma_code);
