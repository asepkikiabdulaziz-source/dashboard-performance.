
-- ROBUST MIGRATION: Fix Multi-PK Error
-- This script dynamically finds the Primary Key of ref_pma and DROPS it, 
-- then adds the new 'id' PK.

DO $$
DECLARE
    r RECORD;
BEGIN
    -- 1. Find and Drop ANY existing Primary Key on ref_pma
    FOR r IN (
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_schema = 'master' 
        AND table_name = 'ref_pma'
        AND constraint_type = 'PRIMARY KEY'
    ) LOOP
        EXECUTE 'ALTER TABLE master.ref_pma DROP CONSTRAINT "' || r.constraint_name || '"';
        RAISE NOTICE 'Dropped existing PK: %', r.constraint_name;
    END LOOP;

    -- 2. Ensure 'id' column exists
    -- (If it failed halfway before, id might already exist)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'master' AND table_name = 'ref_pma' AND column_name = 'id'
    ) THEN
        ALTER TABLE master.ref_pma ADD COLUMN id uuid DEFAULT gen_random_uuid();
    END IF;

    -- 3. Add New Primary Key on 'id'
    ALTER TABLE master.ref_pma ADD CONSTRAINT ref_pma_pk_new PRIMARY KEY (id);

    -- 4. Add Unique Constraint on 'pma_name' (if not exists)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_pma_name'
    ) THEN
        ALTER TABLE master.ref_pma ADD CONSTRAINT unique_pma_name UNIQUE (pma_name);
    END IF;

END $$;
