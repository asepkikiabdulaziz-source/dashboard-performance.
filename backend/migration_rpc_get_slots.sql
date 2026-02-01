-- Function to get Master Slots with Filter/Slicers
-- Returns JSON with count and data

CREATE OR REPLACE FUNCTION master.get_admin_slots_v2(
    p_page integer DEFAULT 1,
    p_page_size integer DEFAULT 20,
    p_search text DEFAULT NULL,
    p_role_filter text DEFAULT NULL,
    p_region_id text DEFAULT NULL,
    p_branch_id text DEFAULT NULL,
    p_depo_id text DEFAULT NULL,
    p_division_id text DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_offset integer;
    v_total bigint;
    v_result json;
BEGIN
    v_offset := (p_page - 1) * p_page_size;

    -- 1. Create a CTE for the base filtered data (Complex Hierarchy Logic)
    -- We need to resolve permissions/hierarchy for each slot type (RM, BM, Salesman)
    
    WITH filtered_slots AS (
        SELECT 
            s.*,
            -- Resolve Depo Name & Branch/Region links for Salesmen
            d.name as dist_name,
            d.branch_id as dist_branch_id,
            d.division_id as dist_division_id,
            
            -- Resolve Branch Name & Region for BMs (or via Dist)
            b.name as branch_name,
            b.region_code as branch_region_code,
            
            -- Resolve Region Name for RMs
            r.name as region_name,
            
            -- Current Assignment (Joined from HR)
            emp.full_name as current_emp_name,
            ass.nik as current_emp_nik,
            ass.start_date as assigned_since
            
        FROM master.sales_slots s
        -- Join Distributor (For Salesmen/slots with depo_id)
        LEFT JOIN master.ref_distributors d ON s.depo_id = d.kd_dist
        
        -- Join Branch:
        -- 1. Via Distributor (for Salesmen)
        -- 2. OR Direct Scope (for BMs)
        LEFT JOIN master.ref_branches b ON 
            (s.scope = 'BRANCH' AND s.scope_id = b.id) OR
            (s.depo_id IS NOT NULL AND d.branch_id = b.id)
            
        -- Join Region lookup:
        -- 1. Via Branch (for BMs/Salesmen)
        -- 2. OR Direct Scope (for RMs)
        LEFT JOIN master.ref_lookup r ON
            r.category = 'REGION' AND (
                (s.scope = 'REGION' AND s.scope_id = r.code) OR
                ((s.scope = 'BRANCH' OR s.depo_id IS NOT NULL) AND b.region_code = r.code)
            )

        -- Join Assignments (Active)
        LEFT JOIN hr.assignments ass ON s.slot_code = ass.slot_code AND ass.end_date IS NULL
        LEFT JOIN hr.employees emp ON ass.nik = emp.nik

        WHERE 
            -- SEARCH
            (p_search IS NULL OR 
             s.slot_code ILIKE '%' || p_search || '%' OR 
             s.sales_code ILIKE '%' || p_search || '%' OR
             emp.full_name ILIKE '%' || p_search || '%')
             
            -- ROLE FILTER (Heuristics)
            AND (p_role_filter IS NULL OR 
                 (p_role_filter ILIKE 'sales%' AND s.sales_code ILIKE 'S%') OR
                 (p_role_filter ILIKE 'super%' AND s.sales_code ILIKE 'M%') OR
                 (p_role_filter ILIKE 'branch%' AND s.sales_code ILIKE 'BM%') OR
                 (p_role_filter ILIKE 'region%' AND s.sales_code ILIKE 'RM%') OR
                 (s.role ILIKE '%' || p_role_filter || '%') -- Fallback if column exists
            )
            
            -- HIERARCHY FILTERS (The Core logic)
            -- Region Filter: Must match either direct scope, or parent branch's region
            AND (p_region_id IS NULL OR 
                 (s.scope = 'REGION' AND s.scope_id = p_region_id) OR
                 (b.region_code = p_region_id)
            )
            
            -- Branch Filter
            AND (p_branch_id IS NULL OR
                 (s.scope = 'BRANCH' AND s.scope_id = p_branch_id) OR
                 (d.branch_id = p_branch_id)
            )
            
            -- Depo/Location Filter
            AND (p_depo_id IS NULL OR
                 s.depo_id = p_depo_id
            )
            
            -- Division Filter
            AND (p_division_id IS NULL OR
                 d.division_id = p_division_id OR 
                 s.division_id = p_division_id -- If it exists
            )
    )
    SELECT json_build_object(
        'data', (
            SELECT coalesce(json_agg(row_to_json(t)), '[]')
            FROM (
                SELECT 
                    slot_code,
                    sales_code,
                    role,
                    level,
                    scope,
                    
                    -- Normalizing Output for Frontend
                    CASE 
                        WHEN scope = 'REGION' THEN r.name
                        WHEN scope = 'BRANCH' THEN b.name
                        ELSE d.name
                    END as location_name,
                    
                    -- Depo Name specifically (for Location col)
                    d.name as depo_name,
                    s.depo_id,
                    
                    -- Hierarchy info
                    r.name as region_name,
                    b.name as branch_name,
                    
                    -- Assignment
                    current_emp_name as current_name,
                    current_emp_nik as current_nik,
                    assigned_since
                    
                FROM filtered_slots s
                LEFT JOIN master.ref_branches b ON 
                    (s.scope = 'BRANCH' AND s.scope_id = b.id) OR (s.dist_branch_id = b.id)
                LEFT JOIN master.ref_lookup r ON 
                     r.category = 'REGION' AND (s.scope = 'REGION' AND s.scope_id = r.code) OR (b.region_code = r.code)
                LEFT JOIN master.ref_distributors d ON s.depo_id = d.kd_dist
                
                ORDER BY slot_code ASC
                LIMIT p_page_size
                OFFSET v_offset
            ) t
        ),
        'total', (SELECT count(*) FROM filtered_slots)
    ) INTO v_result;

    RETURN v_result;
END;
$$;
