
-- ADD parent_kd_dist to Distributors
ALTER TABLE master.ref_distributors
ADD COLUMN parent_kd_dist text;

-- Optional: Index it if used for grouping
CREATE INDEX idx_dist_parent ON master.ref_distributors(parent_kd_dist);
