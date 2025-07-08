-- BioIntel.AI Database Initialization Script

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS biointel_db;

-- Connect to the database
\c biointel_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create user roles
CREATE ROLE biointel_user;
CREATE ROLE biointel_admin;

-- Grant permissions
GRANT CONNECT ON DATABASE biointel_db TO biointel_user;
GRANT CONNECT ON DATABASE biointel_db TO biointel_admin;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS data;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS reports;

-- Grant schema permissions
GRANT USAGE ON SCHEMA auth TO biointel_user;
GRANT USAGE ON SCHEMA data TO biointel_user;
GRANT USAGE ON SCHEMA analytics TO biointel_user;
GRANT USAGE ON SCHEMA reports TO biointel_user;

GRANT ALL ON SCHEMA auth TO biointel_admin;
GRANT ALL ON SCHEMA data TO biointel_admin;
GRANT ALL ON SCHEMA analytics TO biointel_admin;
GRANT ALL ON SCHEMA reports TO biointel_admin;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON data.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_dataset_id ON analytics.analysis_jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports.reports(user_id);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_literature_content_search ON data.literature_summaries USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_datasets_name_search ON data.datasets USING gin(to_tsvector('english', name));

-- Insert initial data
INSERT INTO auth.users (id, email, full_name, is_active, created_at) 
VALUES (uuid_generate_v4(), 'admin@biointel.ai', 'BioIntel Admin', true, NOW())
ON CONFLICT (email) DO NOTHING;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON data.datasets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analysis_jobs_updated_at BEFORE UPDATE ON analytics.analysis_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports.reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit logging function
CREATE OR REPLACE FUNCTION audit_log()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO analytics.audit_log (table_name, operation, old_data, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), NOW());
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO analytics.audit_log (table_name, operation, old_data, new_data, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO analytics.audit_log (table_name, operation, new_data, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), NOW());
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Enable audit logging on critical tables
-- CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON auth.users FOR EACH ROW EXECUTE FUNCTION audit_log();
-- CREATE TRIGGER audit_datasets AFTER INSERT OR UPDATE OR DELETE ON data.datasets FOR EACH ROW EXECUTE FUNCTION audit_log();

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.user_activity_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT d.id) as total_datasets,
    COUNT(DISTINCT aj.id) as total_analyses,
    COUNT(DISTINCT r.id) as total_reports,
    MAX(d.created_at) as last_dataset_upload,
    MAX(aj.created_at) as last_analysis,
    MAX(r.created_at) as last_report
FROM auth.users u
LEFT JOIN data.datasets d ON u.id = d.user_id
LEFT JOIN analytics.analysis_jobs aj ON d.id = aj.dataset_id
LEFT JOIN reports.reports r ON u.id = r.user_id
GROUP BY u.id, u.email;

-- Create refresh function for materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW analytics.user_activity_summary;
END;
$$ language 'plpgsql';

-- Create scheduled job to refresh views (requires pg_cron extension)
-- SELECT cron.schedule('refresh-analytics', '0 2 * * *', 'SELECT refresh_analytics_views();');

-- Performance optimizations
SET shared_preload_libraries = 'pg_stat_statements';
SET track_activity_query_size = 2048;
SET log_min_duration_statement = 1000;

-- Connection pooling settings
SET max_connections = 200;
SET shared_buffers = '256MB';
SET effective_cache_size = '1GB';
SET maintenance_work_mem = '64MB';
SET checkpoint_completion_target = 0.9;
SET wal_buffers = '16MB';
SET default_statistics_target = 100;

-- Print completion message
\echo 'BioIntel.AI database initialization completed successfully!'