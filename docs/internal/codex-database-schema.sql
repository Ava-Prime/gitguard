-- migrations/001_create_codex_schema.sql
-- GitGuard Codex Knowledge Graph Schema
-- Extends existing GitGuard database with knowledge graph capabilities

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Core repository tracking (extends existing repos if present)
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    owner VARCHAR(100) NOT NULL,
    description TEXT,
    language VARCHAR(50),
    risk_profile JSONB DEFAULT '{}',
    health_score FLOAT DEFAULT 0,
    last_analyzed TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Code symbols and structure
CREATE TABLE symbols (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- function, class, module, variable, etc.
    file_path VARCHAR(500) NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    complexity_score INTEGER DEFAULT 0,
    test_coverage FLOAT DEFAULT 0,
    signature_hash VARCHAR(64), -- For change detection
    embedding vector(1536), -- OpenAI embeddings for semantic search
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_id, name, file_path)
);

-- Files and their metadata
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL,
    language VARCHAR(50),
    size_bytes INTEGER DEFAULT 0,
    lines_of_code INTEGER DEFAULT 0,
    test_coverage FLOAT DEFAULT 0,
    complexity_score FLOAT DEFAULT 0,
    last_modified TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    UNIQUE(repo_id, path)
);

-- Pull requests (may extend existing table)
CREATE TABLE IF NOT EXISTS pull_requests (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL, -- open, closed, merged
    base_sha VARCHAR(40),
    head_sha VARCHAR(40),
    risk_score FLOAT DEFAULT 0,
    size_category VARCHAR(20), -- small, medium, large, xlarge
    draft BOOLEAN DEFAULT FALSE,
    mergeable BOOLEAN,
    changed_files INTEGER DEFAULT 0,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    labels TEXT[], -- Array of label names
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    merged_at TIMESTAMP,
    closed_at TIMESTAMP,
    UNIQUE(repo_name, number)
);

-- Issues and bug tracking
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author VARCHAR(100) NOT NULL,
    state VARCHAR(20) NOT NULL, -- open, closed
    labels TEXT[],
    assignees TEXT[],
    milestone VARCHAR(255),
    closed_by_pr_id INTEGER REFERENCES pull_requests(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    UNIQUE(repo_name, number)
);

-- Releases and deployments
CREATE TABLE releases (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    tag_name VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    body TEXT,
    draft BOOLEAN DEFAULT FALSE,
    prerelease BOOLEAN DEFAULT FALSE,
    target_commitish VARCHAR(40),
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(repo_name, tag_name)
);

-- Architecture Decision Records
CREATE TABLE adrs (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    status VARCHAR(20) NOT NULL, -- proposed, accepted, deprecated, superseded
    decision_date DATE,
    content TEXT,
    impact_areas TEXT[], -- Array of impacted system areas
    superseded_by INTEGER REFERENCES adrs(id),
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_name, number)
);

-- Policies (OPA rules)
CREATE TABLE policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    rego_path VARCHAR(500),
    description TEXT,
    enforcement_level VARCHAR(20) DEFAULT 'warn', -- block, warn, monitor
    success_rate FLOAT DEFAULT 0,
    category VARCHAR(50), -- security, quality, compliance, release
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Incidents and post-mortems
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL, -- critical, high, medium, low
    status VARCHAR(20) NOT NULL, -- investigating, identified, monitoring, resolved
    root_cause_pr_id INTEGER REFERENCES pull_requests(id),
    mitigation_pr_id INTEGER REFERENCES pull_requests(id),
    started_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    mttr_minutes INTEGER, -- Mean Time To Resolution
    impact_areas TEXT[],
    lessons_learned TEXT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Relationship tables for many-to-many connections

-- PR to file changes relationship
CREATE TABLE pr_file_changes (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER REFERENCES pull_requests(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- added, modified, removed, renamed
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    status VARCHAR(20), -- GitHub file status
    previous_filename VARCHAR(500), -- For renames
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pr_id, file_path)
);

-- Policy evaluations for each PR
CREATE TABLE policy_evaluations (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER REFERENCES pull_requests(id) ON DELETE CASCADE,
    policy_id INTEGER REFERENCES policies(id) ON DELETE CASCADE,
    result VARCHAR(20) NOT NULL, -- pass, fail, error
    reason TEXT,
    details JSONB DEFAULT '{}',
    evaluated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(pr_id, policy_id)
);

-- Symbol relationships (function calls, class inheritance, etc.)
CREATE TABLE symbol_relationships (
    id SERIAL PRIMARY KEY,
    from_symbol_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
    to_symbol_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- calls, inherits, implements, uses
    strength FLOAT DEFAULT 1.0, -- Relationship strength (0-1)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_symbol_id, to_symbol_id, relationship_type)
);

-- ADR impact on files/symbols
CREATE TABLE adr_file_impacts (
    id SERIAL PRIMARY KEY,
    adr_id INTEGER REFERENCES adrs(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    impact_type VARCHAR(50) NOT NULL, -- creates, modifies, deprecates, removes
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(adr_id, file_path)
);

-- Knowledge embeddings for semantic search
CREATE TABLE knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- pr, symbol, adr, incident, policy
    entity_id INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

-- Performance benchmarks and metrics
CREATE TABLE performance_benchmarks (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER REFERENCES pull_requests(id) ON DELETE CASCADE,
    benchmark_name VARCHAR(255) NOT NULL,
    baseline_value FLOAT,
    current_value FLOAT,
    delta_percent FLOAT,
    unit VARCHAR(50), -- ms, requests/sec, mb, etc.
    status VARCHAR(20), -- improved, degraded, neutral
    created_at TIMESTAMP DEFAULT NOW()
);

-- Risk patterns and anti-patterns
CREATE TABLE risk_patterns (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER REFERENCES pull_requests(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Code ownership and expertise tracking
CREATE TABLE code_ownership (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    owner VARCHAR(100) NOT NULL, -- GitHub username
    ownership_type VARCHAR(20) NOT NULL, -- primary, secondary, contributor
    expertise_score FLOAT DEFAULT 0, -- Based on commit frequency and code quality
    last_contribution TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_name, file_path, owner)
);

-- Indexes for performance

-- Core entity lookups
CREATE INDEX idx_repositories_name ON repositories(name);
CREATE INDEX idx_symbols_repo_type ON symbols(repo_id, type);
CREATE INDEX idx_symbols_file_path ON symbols(repo_id, file_path);
CREATE INDEX idx_pull_requests_repo_state ON pull_requests(repo_name, state);
CREATE INDEX idx_pull_requests_author ON pull_requests(author);

-- Time-based queries
CREATE INDEX idx_pull_requests_created_at ON pull_requests(created_at);
CREATE INDEX idx_incidents_started_at ON incidents(started_at);
CREATE INDEX idx_policy_evaluations_evaluated_at ON policy_evaluations(evaluated_at);

-- Vector similarity search indexes
CREATE INDEX idx_symbols_embedding ON symbols USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_adrs_embedding ON adrs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_incidents_embedding ON incidents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_knowledge_embeddings_vector ON knowledge_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Relationship queries
CREATE INDEX idx_symbol_relationships_from ON symbol_relationships(from_symbol_id, relationship_type);
CREATE INDEX idx_symbol_relationships_to ON symbol_relationships(to_symbol_id, relationship_type);
CREATE INDEX idx_pr_file_changes_pr_id ON pr_file_changes(pr_id);
CREATE INDEX idx_pr_file_changes_file_path ON pr_file_changes(file_path);

-- Governance and compliance
CREATE INDEX idx_policy_evaluations_result ON policy_evaluations(result, evaluated_at);
CREATE INDEX idx_adr_file_impacts_file_path ON adr_file_impacts(file_path);

-- Performance and risk analysis
CREATE INDEX idx_performance_benchmarks_pr_id ON performance_benchmarks(pr_id);
CREATE INDEX idx_risk_patterns_pr_id ON risk_patterns(pr_id);
CREATE INDEX idx_risk_patterns_type ON risk_patterns(pattern_type, severity);

-- Code ownership
CREATE INDEX idx_code_ownership_repo_file ON code_ownership(repo_name, file_path);
CREATE INDEX idx_code_ownership_owner ON code_ownership(owner, expertise_score);

-- Functions for common queries

-- Calculate repository health score
CREATE OR REPLACE FUNCTION calculate_repo_health_score(repo_name_param VARCHAR)
RETURNS FLOAT AS $
DECLARE
    avg_risk FLOAT;
    compliance_rate FLOAT;
    coverage_trend FLOAT;
    health_score FLOAT;
BEGIN
    -- Average risk score (last 30 days)
    SELECT AVG(risk_score) INTO avg_risk
    FROM pull_requests
    WHERE repo_name = repo_name_param
    AND created_at > NOW() - INTERVAL '30 days';

    -- Policy compliance rate (last 30 days)
    SELECT
        COUNT(*) FILTER (WHERE result = 'pass')::FLOAT / NULLIF(COUNT(*), 0) * 100
    INTO compliance_rate
    FROM policy_evaluations pe
    JOIN pull_requests pr ON pe.pr_id = pr.id
    WHERE pr.repo_name = repo_name_param
    AND pe.evaluated_at > NOW() - INTERVAL '30 days';

    -- Test coverage trend (simplified)
    SELECT AVG(
        CASE WHEN (metadata->>'coverage_delta')::FLOAT > 0 THEN 1 ELSE 0 END
    ) * 100 INTO coverage_trend
    FROM pull_requests
    WHERE repo_name = repo_name_param
    AND state = 'merged'
    AND created_at > NOW() - INTERVAL '30 days';

    -- Calculate weighted health score
    health_score := (
        COALESCE(100 - avg_risk, 50) * 0.4 +  -- Risk (inverted)
        COALESCE(compliance_rate, 100) * 0.3 + -- Compliance
        COALESCE(coverage_trend, 50) * 0.3     -- Coverage trend
    );

    RETURN GREATEST(0, LEAST(100, health_score));
END;
$ LANGUAGE plpgsql;

-- Find semantically similar entities
CREATE OR REPLACE FUNCTION find_similar_entities(
    query_embedding vector(1536),
    entity_type_param VARCHAR DEFAULT NULL,
    limit_param INTEGER DEFAULT 10
)
RETURNS TABLE(
    entity_type VARCHAR,
    entity_id INTEGER,
    similarity_score FLOAT,
    content TEXT
) AS $
BEGIN
    RETURN QUERY
    SELECT
        'symbol' as entity_type,
        s.id as entity_id,
        (1 - (s.embedding <=> query_embedding)) as similarity_score,
        s.name || ' (' || s.type || ')' as content
    FROM symbols s
    WHERE s.embedding IS NOT NULL
    AND (entity_type_param IS NULL OR entity_type_param = 'symbol')

    UNION ALL

    SELECT
        'adr' as entity_type,
        a.id as entity_id,
        (1 - (a.embedding <=> query_embedding)) as similarity_score,
        'ADR-' || a.number || ': ' || a.title as content
    FROM adrs a
    WHERE a.embedding IS NOT NULL
    AND (entity_type_param IS NULL OR entity_type_param = 'adr')

    UNION ALL

    SELECT
        'incident' as entity_type,
        i.id as entity_id,
        (1 - (i.embedding <=> query_embedding)) as similarity_score,
        i.title as content
    FROM incidents i
    WHERE i.embedding IS NOT NULL
    AND (entity_type_param IS NULL OR entity_type_param = 'incident')

    ORDER BY similarity_score DESC
    LIMIT limit_param;
END;
$ LANGUAGE plpgsql;

-- Get expert reviewers for files
CREATE OR REPLACE FUNCTION get_expert_reviewers(
    file_paths_param TEXT[],
    limit_param INTEGER DEFAULT 5
)
RETURNS TABLE(
    username VARCHAR,
    expertise_score FLOAT,
    recent_contributions INTEGER,
    avg_pr_quality FLOAT
) AS $
BEGIN
    RETURN QUERY
    SELECT
        co.owner as username,
        AVG(co.expertise_score) as expertise_score,
        COUNT(DISTINCT pr.id)::INTEGER as recent_contributions,
        AVG(CASE WHEN pr.risk_score <= 30 THEN 1.0 ELSE 0.0 END) as avg_pr_quality
    FROM code_ownership co
    JOIN pr_file_changes pfc ON pfc.file_path = co.file_path
    JOIN pull_requests pr ON pr.id = pfc.pr_id
    WHERE co.file_path = ANY(file_paths_param)
    AND pr.created_at > NOW() - INTERVAL '90 days'
    AND pr.state = 'merged'
    GROUP BY co.owner
    ORDER BY expertise_score DESC, recent_contributions DESC
    LIMIT limit_param;
END;
$ LANGUAGE plpgsql;

-- Trigger to update repository health scores
CREATE OR REPLACE FUNCTION update_repo_health_trigger()
RETURNS TRIGGER AS $
BEGIN
    UPDATE repositories
    SET
        health_score = calculate_repo_health_score(NEW.repo_name),
        updated_at = NOW()
    WHERE name = NEW.repo_name;

    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Triggers for automatic updates
CREATE TRIGGER tr_update_repo_health_on_pr
    AFTER INSERT OR UPDATE ON pull_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_repo_health_trigger();

-- Views for common queries

-- Active PRs with risk analysis
CREATE OR REPLACE VIEW active_prs_with_risk AS
SELECT
    pr.*,
    r.health_score as repo_health,
    COUNT(pfc.id) as files_touched,
    COUNT(pe.id) FILTER (WHERE pe.result = 'fail') as policy_failures,
    COUNT(rp.id) as risk_patterns_detected,
    COALESCE(AVG(pb.delta_percent), 0) as avg_performance_impact
FROM pull_requests pr
LEFT JOIN repositories r ON r.name = pr.repo_name
LEFT JOIN pr_file_changes pfc ON pfc.pr_id = pr.id
LEFT JOIN policy_evaluations pe ON pe.pr_id = pr.id
LEFT JOIN risk_patterns rp ON rp.pr_id = pr.id
LEFT JOIN performance_benchmarks pb ON pb.pr_id = pr.id
WHERE pr.state = 'open'
GROUP BY pr.id, r.health_score;

-- Repository dashboard metrics
CREATE OR REPLACE VIEW repo_dashboard_metrics AS
SELECT
    r.name as repo_name,
    r.health_score,
    COUNT(DISTINCT pr.id) as total_prs,
    COUNT(DISTINCT pr.id) FILTER (WHERE pr.created_at > NOW() - INTERVAL '7 days') as recent_prs,
    AVG(pr.risk_score) as avg_risk_score,
    COUNT(DISTINCT s.id) as total_symbols,
    COUNT(DISTINCT f.id) as total_files,
    AVG(f.test_coverage) as avg_test_coverage,
    COUNT(DISTINCT i.id) FILTER (WHERE i.started_at > NOW() - INTERVAL '30 days') as recent_incidents,
    (
        SELECT COUNT(*) FILTER (WHERE result = 'pass')::FLOAT / NULLIF(COUNT(*), 0) * 100
        FROM policy_evaluations pe
        JOIN pull_requests pr2 ON pe.pr_id = pr2.id
        WHERE pr2.repo_name = r.name
        AND pe.evaluated_at > NOW() - INTERVAL '30 days'
    ) as compliance_rate
FROM repositories r
LEFT JOIN pull_requests pr ON pr.repo_name = r.name
LEFT JOIN symbols s ON s.repo_id = r.id
LEFT JOIN files f ON f.repo_id = r.id
LEFT JOIN incidents i ON i.repo_name = r.name
GROUP BY r.id, r.name, r.health_score;

-- Knowledge graph connections view
CREATE OR REPLACE VIEW knowledge_connections AS
SELECT
    'pr' as source_type,
    pr.id as source_id,
    pr.title as source_title,
    'symbol' as target_type,
    s.id as target_id,
    s.name as target_title,
    'modifies' as relationship_type,
    1.0 as strength
FROM pull_requests pr
JOIN pr_file_changes pfc ON pfc.pr_id = pr.id
JOIN symbols s ON s.file_path = pfc.file_path
WHERE pr.state IN ('open', 'merged')

UNION ALL

SELECT
    'adr' as source_type,
    a.id as source_id,
    a.title as source_title,
    'pr' as target_type,
    pr.id as target_id,
    pr.title as target_title,
    'implements' as relationship_type,
    1.0 as strength
FROM adrs a
JOIN adr_file_impacts afi ON afi.adr_id = a.id
JOIN pr_file_changes pfc ON pfc.file_path = afi.file_path
JOIN pull_requests pr ON pr.id = pfc.pr_id

UNION ALL

SELECT
    'incident' as source_type,
    i.id as source_id,
    i.title as source_title,
    'pr' as target_type,
    pr.id as target_id,
    pr.title as target_title,
    CASE WHEN i.root_cause_pr_id = pr.id THEN 'caused_by'
         WHEN i.mitigation_pr_id = pr.id THEN 'mitigated_by'
         ELSE 'related_to' END as relationship_type,
    1.0 as strength
FROM incidents i
JOIN pull_requests pr ON pr.id IN (i.root_cause_pr_id, i.mitigation_pr_id);

-- Sample data for testing (remove in production)
INSERT INTO repositories (name, owner, description, language) VALUES
('ava-prime/gitguard', 'ava-prime', 'AI-powered Git repository governance', 'python'),
('ava-prime/example-app', 'ava-prime', 'Example application for testing', 'typescript');

INSERT INTO policies (name, description, enforcement_level, category) VALUES
('weekend-freeze', 'Prevent deployments during weekend hours', 'block', 'release'),
('security-scan-required', 'Require security scan pass before merge', 'block', 'security'),
('test-coverage-threshold', 'Maintain minimum 80% test coverage', 'warn', 'quality'),
('large-pr-review', 'Require additional reviews for large PRs', 'warn', 'quality'),
('dependency-update-approval', 'Require approval for dependency updates', 'warn', 'security');

-- Materialized view for fast dashboard queries
CREATE MATERIALIZED VIEW dashboard_summary AS
SELECT
    (SELECT COUNT(*) FROM repositories) as total_repos,
    (SELECT COUNT(*) FROM pull_requests WHERE state = 'open') as open_prs,
    (SELECT COUNT(*) FROM pull_requests WHERE created_at > NOW() - INTERVAL '24 hours') as prs_today,
    (SELECT AVG(risk_score) FROM pull_requests WHERE created_at > NOW() - INTERVAL '7 days') as avg_weekly_risk,
    (SELECT COUNT(*) FROM incidents WHERE status != 'resolved') as active_incidents,
    (
        SELECT COUNT(*) FILTER (WHERE result = 'pass')::FLOAT / NULLIF(COUNT(*), 0) * 100
        FROM policy_evaluations
        WHERE evaluated_at > NOW() - INTERVAL '7 days'
    ) as weekly_compliance_rate,
    NOW() as last_updated;

-- Refresh materialized view function
CREATE OR REPLACE FUNCTION refresh_dashboard_summary()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW dashboard_summary;
END;
$ LANGUAGE plpgsql;

-- Schedule regular refresh (requires pg_cron extension)
-- SELECT cron.schedule('refresh-dashboard', '*/5 * * * *', 'SELECT refresh_dashboard_summary();');

COMMENT ON TABLE repositories IS 'Core repository metadata and health metrics';
COMMENT ON TABLE symbols IS 'Code symbols (functions, classes, modules) with complexity analysis';
COMMENT ON TABLE pull_requests IS 'Pull request tracking with risk scoring and metadata';
COMMENT ON TABLE adrs IS 'Architecture Decision Records with impact tracking';
COMMENT ON TABLE incidents IS 'Incident tracking with root cause analysis';
COMMENT ON TABLE policies IS 'OPA policy definitions and success rates';
COMMENT ON TABLE knowledge_embeddings IS 'Vector embeddings for semantic search across all entities';
COMMENT ON VIEW knowledge_connections IS 'Graph view of relationships between all entities';
COMMENT ON MATERIALIZED VIEW dashboard_summary IS 'Fast dashboard metrics updated every 5 minutes';
