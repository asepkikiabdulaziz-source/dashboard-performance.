-- =================================================================
-- Migration: Enhanced Master Slot (Hierarchy & Scope)
-- Description: Updates sales_slots to support unified hierarchy and flexible scoping
-- =================================================================

-- 1. Create Enum for Scope Type
DO $$ BEGIN
    CREATE TYPE master.slot_scope_type AS ENUM ('DEPO', 'BRANCH', 'REGION', 'NATIONAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Update master.sales_slots (The "Chair")
-- Allow depo_id to be NULL (Since Managers cover larger areas)
ALTER TABLE master.sales_slots 
ALTER COLUMN depo_id DROP NOT NULL;

-- Add Hierarchy Column (Who is my boss?)
ALTER TABLE master.sales_slots 
ADD COLUMN IF NOT EXISTS parent_slot_code text REFERENCES master.sales_slots(slot_code);

-- Add Scope Columns (What do I cover?)
ALTER TABLE master.sales_slots 
ADD COLUMN IF NOT EXISTS scope master.slot_scope_type DEFAULT 'DEPO',
ADD COLUMN IF NOT EXISTS scope_id text; -- E.g., 'BRANCH-01', 'REGION-A'

-- Add Level (Optional, for easier querying)
ALTER TABLE master.sales_slots 
ADD COLUMN IF NOT EXISTS level int DEFAULT 99; -- 1=RM, 2=BM, 3=SPV, 4=SLS

-- Index for speed
CREATE INDEX IF NOT EXISTS idx_slot_parent ON master.sales_slots(parent_slot_code);
CREATE INDEX IF NOT EXISTS idx_slot_scope ON master.sales_slots(scope, scope_id);
