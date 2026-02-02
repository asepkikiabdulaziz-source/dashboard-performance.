
-- Populate initial Price Zone data
INSERT INTO master.ref_lookup (company_id, category, code, name, description)
VALUES 
('ID001', 'PRICE_ZONE', 'Z1', 'Zona 1 (Sumatera)', 'Harga Zona 1'),
('ID001', 'PRICE_ZONE', 'Z2', 'Zona 2 (Jawa)', 'Harga Zona 2'),
('ID001', 'PRICE_ZONE', 'Z3', 'Zona 3 (Timur)', 'Harga Zona 3')
ON CONFLICT (category, code) DO NOTHING;
