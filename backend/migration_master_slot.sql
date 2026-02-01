-- =================================================================
-- Migration: Master Slot Management
-- Description: Separates Salesman Slot (Position) from Employee (Person)
-- =================================================================

-- 1. Create Master Slot Table (The "Chair" or "Territory")
CREATE TABLE IF NOT EXISTS master.ref_master_slot (
    slot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_code VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'SLS-JBO-01', 'SPV-JBO-01'
    role_id VARCHAR(50) NOT NULL REFERENCES master.ref_role(role_id),
    region VARCHAR(50) NOT NULL, -- 'JABODETABEK', 'WEST_JAVA', etc.
    branch_id VARCHAR(50), -- Optional branch specific
    
    -- Hierarchy
    supervisor_slot_id UUID REFERENCES master.ref_master_slot(slot_id),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create Slot Assignment History (Who sat in the chair and when)
CREATE TABLE IF NOT EXISTS hr.trx_slot_assignment (
    assignment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_id UUID NOT NULL REFERENCES master.ref_master_slot(slot_id),
    nik VARCHAR(50) NOT NULL REFERENCES hr.employees(nik),
    
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE, -- NULL means currently active
    
    is_active BOOLEAN DEFAULT TRUE, -- Redundant but useful for quick queries
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) -- Auth user ID
);

-- 3. Trigger/Constraint to ensure one active person per slot (Optional but recommended)
-- For simplicity, we manage this in application logic first.

-- 4. Initial Seed for Supervisors (Example)
-- INSERT INTO master.ref_master_slot (slot_code, role_id, region) VALUES ('SPV-01', 'supervisior', 'REGION_A');
