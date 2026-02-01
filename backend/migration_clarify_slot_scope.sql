-- Migration: Clarify Slot Scope Design
-- Purpose: Document and enforce scope_id vs depo_id rules

-- Add comments to clarify column purposes
COMMENT ON COLUMN master.sales_slots.depo_id IS 
'Physical work location (base depo). Required for scope=DEPO, optional for others. FK to ref_distributors.';

COMMENT ON COLUMN master.sales_slots.scope_id IS 
'Responsibility coverage identifier. Content depends on scope: DEPO=depo_id, BRANCH=branch_id, REGION=region_code, NATIONAL=null';

COMMENT ON COLUMN master.sales_slots.scope IS 
'Scope level: DEPO (single location), BRANCH (multiple depos), REGION (multiple branches), NATIONAL (all)';

-- Add check constraint to enforce consistency for DEPO scope
ALTER TABLE master.sales_slots
ADD CONSTRAINT check_depo_scope_consistency
CHECK (
    scope != 'DEPO' OR (depo_id IS NOT NULL AND scope_id = depo_id)
);

-- Add check constraint: scope_id required except for NATIONAL
ALTER TABLE master.sales_slots
ADD CONSTRAINT check_scope_id_required
CHECK (
    scope = 'NATIONAL' OR scope_id IS NOT NULL
);

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_slots_scope_id ON master.sales_slots(scope_id) WHERE scope_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_slots_depo_id ON master.sales_slots(depo_id) WHERE depo_id IS NOT NULL;

-- Example data for documentation
/*
EXAMPLES:

1. Salesman (DEPO scope):
   depo_id: 'D001', scope: 'DEPO', scope_id: 'D001'
   → Works at D001, responsible for D001

2. Branch Manager (BRANCH scope):
   depo_id: NULL, scope: 'BRANCH', scope_id: 'BR-JKT'
   → No fixed depo, responsible for entire Jakarta branch

3. Regional Manager (REGION scope):
   depo_id: NULL, scope: 'REGION', scope_id: 'REG-JB'
   → No fixed depo, responsible for Jawa Barat region

4. National Director (NATIONAL scope):
   depo_id: NULL, scope: 'NATIONAL', scope_id: NULL
   → No fixed location, national responsibility
*/
