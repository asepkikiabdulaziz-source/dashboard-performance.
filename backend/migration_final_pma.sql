
-- FINAL PMA FIX: Add ID (PK) and Unique Name
-- 1. Add 'id' column (Surrogate Key)
ALTER TABLE master.ref_pma
ADD COLUMN id uuid DEFAULT gen_random_uuid();

-- 2. Make 'id' the Primary Key
ALTER TABLE master.ref_pma DROP CONSTRAINT IF EXISTS ref_pma_pkey;
ALTER TABLE master.ref_pma
ADD CONSTRAINT ref_pma_pkey PRIMARY KEY (id);

-- 3. Make 'pma_name' Unique (User Request)
-- Note: If duplicates exist in 'pma_name', this will fail. 
-- The user said "yang pasti unik itu nama pma", so we assume data is clean or they want to enforce it.
ALTER TABLE master.ref_pma
ADD CONSTRAINT unique_pma_name UNIQUE (pma_name);
