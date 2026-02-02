
-- Sync missing Price Zones from Distributors to Master Table
INSERT INTO master.price_zones (company_id, id, description)
SELECT DISTINCT 
    'ID001', 
    price_zone_id, 
    'Auto-generated from Distributor: ' || price_zone_id
FROM master.ref_distributors
WHERE price_zone_id IS NOT NULL
  AND price_zone_id NOT IN (SELECT id FROM master.price_zones)
ON CONFLICT (id) DO NOTHING;
