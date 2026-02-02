
-- DROP LEVEL FROM REF_ROLE
-- Goal: Remove redundant 'level' column. Level is now exclusively managed via 'ref_lookup' on Slot/Employee tables.

ALTER TABLE master.ref_role 
DROP COLUMN IF EXISTS level;
