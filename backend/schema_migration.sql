-- Create Schemas
CREATE SCHEMA IF NOT EXISTS hr;
CREATE SCHEMA IF NOT EXISTS master;

-- Grant usage to Supabase API roles
GRANT USAGE ON SCHEMA hr, master TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA hr, master TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA hr, master GRANT ALL ON TABLES TO anon, authenticated, service_role;

-- Create Roles Table
CREATE TABLE IF NOT EXISTS master.ref_role (
    role_id text NOT NULL PRIMARY KEY,
    role_name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now()
);

-- Insert Default Roles
INSERT INTO master.ref_role (role_id, role_name, description) VALUES
('admin', 'Administrator', 'Full system access'),
('supervisor', 'Supervisor', 'Regional manager'),
('salesman', 'Salesman', 'Field sales representative')
ON CONFLICT (role_id) DO NOTHING;

-- Create Employees Table (User Provided)
CREATE TABLE IF NOT EXISTS hr.employees (
    nik text NOT NULL,
    full_name text NOT NULL,
    role_id text NOT NULL,
    email text NULL,
    auth_user_id uuid NULL,
    phone_number text NULL,
    is_active boolean NULL DEFAULT true,
    created_at timestamp with time zone NULL DEFAULT now(),
    updated_at timestamp with time zone NULL DEFAULT now(),
    CONSTRAINT employees_pkey PRIMARY KEY (nik),
    CONSTRAINT employees_auth_user_id_key UNIQUE (auth_user_id),
    CONSTRAINT employees_email_key UNIQUE (email),
    CONSTRAINT employees_role_id_fkey FOREIGN KEY (role_id) REFERENCES master.ref_role (role_id)
);

CREATE INDEX IF NOT EXISTS idx_emp_auth ON hr.employees USING btree (auth_user_id);
CREATE INDEX IF NOT EXISTS idx_emp_role ON hr.employees USING btree (role_id);
