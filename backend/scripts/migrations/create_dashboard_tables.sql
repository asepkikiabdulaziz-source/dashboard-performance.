-- =================================================================
-- Migration: Create Dashboard Tables in Supabase
-- Description: Tables untuk store data dari BigQuery materialized tables
-- Note: BigQuery tables (FINAL_SCORECARD_RANKED, rank_ass, rank_bm, rank_rbm)
--       sudah materialized via stored procedure, jadi langsung sync saja
-- =================================================================

-- Create dashboard schema if not exists
CREATE SCHEMA IF NOT EXISTS dashboard;

-- =================================================================
-- 1. dashboard.leaderboard
-- Source: FINAL_SCORECARD_RANKED (BigQuery)
-- =================================================================
CREATE TABLE IF NOT EXISTS dashboard.leaderboard (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identity
    region TEXT,
    kd_dist TEXT,
    area TEXT,
    salesman_code TEXT,
    salesman_name TEXT,
    division TEXT,
    nik TEXT,
    
    -- Revenue Metrics
    omset_p1 DECIMAL(15,2),
    omset_p2 DECIMAL(15,2),
    omset_p3 DECIMAL(15,2),
    omset_p4 DECIMAL(15,2),
    target DECIMAL(15,2),
    achievement_rate DECIMAL(5,2),
    
    -- Scoring
    total_score INTEGER,
    month_score INTEGER,
    rank_regional INTEGER,
    
    -- ROA Metrics
    roa_p1 DECIMAL(10,2),
    roa_p2 DECIMAL(10,2),
    roa_p3 DECIMAL(10,2),
    roa_p4 DECIMAL(10,2),
    
    -- Customer & Call Metrics
    total_customer INTEGER,
    effective_calls INTEGER,
    points_balance INTEGER,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leaderboard_region ON dashboard.leaderboard(region);
CREATE INDEX IF NOT EXISTS idx_leaderboard_nik ON dashboard.leaderboard(nik);
CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON dashboard.leaderboard(rank_regional);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON dashboard.leaderboard(total_score DESC);

-- =================================================================
-- 2. dashboard.competition_ranks
-- Source: rank_ass, rank_bm, rank_rbm (BigQuery)
-- =================================================================
CREATE TABLE IF NOT EXISTS dashboard.competition_ranks (
    id BIGSERIAL PRIMARY KEY,
    
    -- Competition Info
    competition_id TEXT NOT NULL,
    level TEXT NOT NULL, -- 'ass', 'bm', 'rbm'
    
    -- Identity
    region TEXT,
    nik TEXT,
    name TEXT,
    rank INTEGER,
    cabang TEXT,
    zona_bm TEXT,
    zona_rbm TEXT,
    
    -- Metrics
    omset DECIMAL(15,2),
    target DECIMAL(15,2),
    total_point INTEGER,
    point_oms INTEGER,
    point_roa INTEGER,
    ach_oms DECIMAL(5,2),
    ach_roa DECIMAL(5,2),
    reward INTEGER,
    cb INTEGER,
    act_roa DECIMAL(10,2),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(competition_id, level, nik, region)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_comp_competition ON dashboard.competition_ranks(competition_id, level);
CREATE INDEX IF NOT EXISTS idx_comp_region ON dashboard.competition_ranks(region);
CREATE INDEX IF NOT EXISTS idx_comp_nik ON dashboard.competition_ranks(nik);
CREATE INDEX IF NOT EXISTS idx_comp_rank ON dashboard.competition_ranks(rank);
CREATE INDEX IF NOT EXISTS idx_comp_zona_bm ON dashboard.competition_ranks(zona_bm);
CREATE INDEX IF NOT EXISTS idx_comp_zona_rbm ON dashboard.competition_ranks(zona_rbm);

-- =================================================================
-- 3. dashboard.metadata
-- Untuk track sync status
-- =================================================================
CREATE TABLE IF NOT EXISTS dashboard.metadata (
    key TEXT PRIMARY KEY,
    last_sync_at TIMESTAMPTZ,
    sync_status TEXT,
    sync_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =================================================================
-- Enable RLS (Row-Level Security)
-- =================================================================
ALTER TABLE dashboard.leaderboard ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard.competition_ranks ENABLE ROW LEVEL SECURITY;

-- RLS Policies akan dibuat di migration terpisah setelah tables dibuat
-- (Lihat: create_dashboard_rls_policies.sql)

-- =================================================================
-- Comments
-- =================================================================
COMMENT ON TABLE dashboard.leaderboard IS 'Leaderboard data synced from FINAL_SCORECARD_RANKED (BigQuery)';
COMMENT ON TABLE dashboard.competition_ranks IS 'Competition ranking data synced from rank_ass, rank_bm, rank_rbm (BigQuery)';
COMMENT ON TABLE dashboard.metadata IS 'Metadata for tracking ETL sync status';
