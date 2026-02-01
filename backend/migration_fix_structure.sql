
-- FIX STRUCTURE: Link Distributors to Branches (Areas)
-- This ensures the hierarchy: Region -> Branch (Area) -> Distributor

ALTER TABLE master.ref_distributors
ADD COLUMN IF NOT EXISTS branch_id text;

-- Add Foreign Key for safety (Optional but good)
-- We assume ref_branches.id matches the branch_id used here.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_distributors_branch'
    ) THEN
        ALTER TABLE master.ref_distributors
        ADD CONSTRAINT fk_distributors_branch
        FOREIGN KEY (branch_id)
        REFERENCES master.ref_branches(id);
    END IF;
END $$;
