-- 1. Create Permissions Catalog
CREATE TABLE IF NOT EXISTS master.ref_permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create Role-Permissions Junction Table
CREATE TABLE IF NOT EXISTS master.trx_role_permissions (
    role_id VARCHAR(50) NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_code),
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES master.ref_role(role_id) ON DELETE CASCADE,
    CONSTRAINT fk_permission FOREIGN KEY (permission_code) REFERENCES master.ref_permissions(code) ON DELETE CASCADE
);

-- 3. Seed Roles (Ensure they exist to prevent FK errors)
INSERT INTO master.ref_role (role_id, role_name, level) VALUES
('super_admin', 'Super Administrator', 99),
('admin', 'Administrator', 50),
('viewer', 'Viewer', 10),
('salesman', 'Salesman', 10)
ON CONFLICT (role_id) DO NOTHING;

-- 4. Seed Permissions
INSERT INTO master.ref_permissions (code, category, description) VALUES
-- System
('system.super_admin', 'System', 'Full System Access (God Mode)'),

-- Dashboard & Reports
('dashboard.view', 'Reports', 'View Sales Dashboard'),
('leaderboard.view', 'Reports', 'View Logic Leaderboard'),

-- Auth / User Management
('auth.user.manage', 'Auth', 'Create, Update, Delete Employees'),
('auth.user.assign_role', 'Auth', 'Change Employee Roles'),

-- Master Data
('master.data.view', 'Master Data', 'View Master Data Tables'),
('master.data.manage', 'Master Data', 'Add/Edit/Delete Master Data'),
('master.company.manage', 'Master Data', 'Manage Multi-Company Data (Super Admin)'),

-- Product Management
('product.manage', 'Products', 'Add/Edit/Delete Products')
ON CONFLICT (code) DO NOTHING;

-- 4. Seed Role Permissions
-- Super Admin (Get Everything)
INSERT INTO master.trx_role_permissions (role_id, permission_code)
SELECT 'super_admin', code FROM master.ref_permissions
ON CONFLICT DO NOTHING;

-- Admin (Everything EXCEPT system.super_admin and master.company.manage)
INSERT INTO master.trx_role_permissions (role_id, permission_code)
SELECT 'admin', code FROM master.ref_permissions 
WHERE code NOT IN ('system.super_admin', 'master.company.manage')
ON CONFLICT DO NOTHING;

-- Viewer / Salesman (Only View Reports)
INSERT INTO master.trx_role_permissions (role_id, permission_code)
SELECT 'viewer', code FROM master.ref_permissions 
WHERE code IN ('dashboard.view', 'leaderboard.view')
ON CONFLICT DO NOTHING;

INSERT INTO master.trx_role_permissions (role_id, permission_code)
SELECT 'salesman', code FROM master.ref_permissions 
WHERE code IN ('dashboard.view', 'leaderboard.view')
ON CONFLICT DO NOTHING;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'RBAC Schema and Seeds Initialized Successfully';
END $$;
