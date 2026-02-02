
-- CLEANUP REF_LOOKUP
-- Remove Region and GRBM data as they are now in dedicated tables.

DELETE FROM master.ref_lookup 
WHERE category IN ('REGION', 'GRBM');
