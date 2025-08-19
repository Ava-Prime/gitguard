-- GitGuard Demo Database Initialization
-- This script sets up demo data for the GitGuard platform

-- Create demo organizations
INSERT INTO organizations (id, name, slug, description, created_at, updated_at) VALUES
('org-demo-1', 'Acme Corporation', 'acme-corp', 'Demo organization for GitGuard showcase', NOW(), NOW()),
('org-demo-2', 'TechStart Inc', 'techstart', 'Startup demo organization', NOW(), NOW()),
('org-demo-3', 'Enterprise Solutions', 'enterprise-sol', 'Enterprise demo organization', NOW(), NOW());

-- Create demo repositories
INSERT INTO repositories (id, organization_id, name, full_name, description, private, default_branch, created_at, updated_at) VALUES
('repo-demo-1', 'org-demo-1', 'web-app', 'acme-corp/web-app', 'Main web application with React frontend', false, 'main', NOW(), NOW()),
('repo-demo-2', 'org-demo-1', 'api-service', 'acme-corp/api-service', 'Backend API service in Python', true, 'main', NOW(), NOW()),
('repo-demo-3', 'org-demo-2', 'mobile-app', 'techstart/mobile-app', 'React Native mobile application', false, 'develop', NOW(), NOW()),
('repo-demo-4', 'org-demo-3', 'infrastructure', 'enterprise-sol/infrastructure', 'Terraform infrastructure as code', true, 'main', NOW(), NOW());

-- Create demo users
INSERT INTO users (id, github_id, username, email, name, avatar_url, created_at, updated_at) VALUES
('user-demo-1', 12345, 'alice-dev', 'alice@acme-corp.com', 'Alice Johnson', 'https://avatars.githubusercontent.com/u/12345', NOW(), NOW()),
('user-demo-2', 23456, 'bob-security', 'bob@acme-corp.com', 'Bob Smith', 'https://avatars.githubusercontent.com/u/23456', NOW(), NOW()),
('user-demo-3', 34567, 'charlie-ops', 'charlie@techstart.com', 'Charlie Brown', 'https://avatars.githubusercontent.com/u/34567', NOW(), NOW()),
('user-demo-4', 45678, 'diana-admin', 'diana@enterprise-sol.com', 'Diana Prince', 'https://avatars.githubusercontent.com/u/45678', NOW(), NOW());

-- Create demo policies
INSERT INTO policies (id, organization_id, name, description, type, rules, enabled, created_at, updated_at) VALUES
('policy-demo-1', 'org-demo-1', 'Secret Detection', 'Prevent secrets from being committed', 'secret_detection', '{"patterns": ["api_key", "password", "token"], "entropy_threshold": 4.5}', true, NOW(), NOW()),
('policy-demo-2', 'org-demo-1', 'Vulnerability Scanning', 'Check for known vulnerabilities', 'vulnerability_scan', '{"severity_threshold": "medium", "block_high": true}', true, NOW(), NOW()),
('policy-demo-3', 'org-demo-2', 'License Compliance', 'Ensure license compatibility', 'license_check', '{"allowed_licenses": ["MIT", "Apache-2.0", "BSD-3-Clause"]}', true, NOW(), NOW()),
('policy-demo-4', 'org-demo-3', 'Code Quality', 'Maintain code quality standards', 'code_quality', '{"min_coverage": 80, "max_complexity": 10}', true, NOW(), NOW());

-- Create demo security findings
INSERT INTO security_findings (id, repository_id, commit_sha, type, severity, title, description, file_path, line_number, status, created_at, updated_at) VALUES
('finding-demo-1', 'repo-demo-1', 'abc123def456', 'secret', 'high', 'API Key Detected', 'Hardcoded API key found in configuration file', 'src/config/api.js', 15, 'open', NOW(), NOW()),
('finding-demo-2', 'repo-demo-2', 'def456ghi789', 'vulnerability', 'critical', 'SQL Injection Risk', 'Potential SQL injection vulnerability in user input handling', 'app/models/user.py', 42, 'resolved', NOW(), NOW()),
('finding-demo-3', 'repo-demo-3', 'ghi789jkl012', 'license', 'medium', 'GPL License Detected', 'GPL-licensed dependency conflicts with project license', 'package.json', 1, 'open', NOW(), NOW()),
('finding-demo-4', 'repo-demo-4', 'jkl012mno345', 'secret', 'high', 'AWS Access Key', 'AWS access key found in Terraform configuration', 'terraform/main.tf', 23, 'investigating', NOW(), NOW());

-- Create demo pull requests
INSERT INTO pull_requests (id, repository_id, number, title, description, author_id, base_branch, head_branch, status, created_at, updated_at) VALUES
('pr-demo-1', 'repo-demo-1', 42, 'Add user authentication', 'Implement JWT-based user authentication system', 'user-demo-1', 'main', 'feature/auth', 'open', NOW(), NOW()),
('pr-demo-2', 'repo-demo-2', 15, 'Fix security vulnerability', 'Patch SQL injection vulnerability in user model', 'user-demo-2', 'main', 'security/sql-injection-fix', 'merged', NOW(), NOW()),
('pr-demo-3', 'repo-demo-3', 8, 'Update dependencies', 'Bump React Native to latest version', 'user-demo-3', 'develop', 'chore/update-deps', 'open', NOW(), NOW()),
('pr-demo-4', 'repo-demo-4', 3, 'Add monitoring stack', 'Deploy Prometheus and Grafana for monitoring', 'user-demo-4', 'main', 'feature/monitoring', 'draft', NOW(), NOW());

-- Create demo policy violations
INSERT INTO policy_violations (id, policy_id, repository_id, pull_request_id, commit_sha, severity, message, file_path, line_number, status, created_at, updated_at) VALUES
('violation-demo-1', 'policy-demo-1', 'repo-demo-1', 'pr-demo-1', 'abc123def456', 'high', 'Hardcoded API key detected', 'src/config/api.js', 15, 'blocking', NOW(), NOW()),
('violation-demo-2', 'policy-demo-2', 'repo-demo-2', 'pr-demo-2', 'def456ghi789', 'critical', 'Critical vulnerability found', 'app/models/user.py', 42, 'resolved', NOW(), NOW()),
('violation-demo-3', 'policy-demo-3', 'repo-demo-3', 'pr-demo-3', 'ghi789jkl012', 'medium', 'Incompatible license detected', 'package.json', 1, 'warning', NOW(), NOW()),
('violation-demo-4', 'policy-demo-4', 'repo-demo-4', 'pr-demo-4', 'jkl012mno345', 'low', 'Code coverage below threshold', 'tests/test_main.py', 1, 'warning', NOW(), NOW());

-- Create demo audit logs
INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at) VALUES
('audit-demo-1', 'user-demo-1', 'create', 'pull_request', 'pr-demo-1', '{"title": "Add user authentication"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NOW()),
('audit-demo-2', 'user-demo-2', 'resolve', 'security_finding', 'finding-demo-2', '{"resolution": "patched"}', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', NOW()),
('audit-demo-3', 'user-demo-3', 'update', 'repository', 'repo-demo-3', '{"branch": "develop"}', '192.168.1.102', 'Mozilla/5.0 (X11; Linux x86_64)', NOW()),
('audit-demo-4', 'user-demo-4', 'create', 'policy', 'policy-demo-4', '{"name": "Code Quality"}', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NOW());

-- Create demo metrics
INSERT INTO metrics (id, repository_id, metric_type, value, timestamp, metadata, created_at) VALUES
('metric-demo-1', 'repo-demo-1', 'security_score', 85.5, NOW() - INTERVAL '1 hour', '{"findings": 2, "resolved": 1}', NOW()),
('metric-demo-2', 'repo-demo-2', 'vulnerability_count', 3, NOW() - INTERVAL '2 hours', '{"critical": 1, "high": 1, "medium": 1}', NOW()),
('metric-demo-3', 'repo-demo-3', 'license_compliance', 95.0, NOW() - INTERVAL '3 hours', '{"compliant": 19, "total": 20}', NOW()),
('metric-demo-4', 'repo-demo-4', 'code_coverage', 78.2, NOW() - INTERVAL '4 hours', '{"lines_covered": 782, "total_lines": 1000}', NOW());

-- Grant demo permissions
INSERT INTO user_permissions (user_id, organization_id, role, granted_at) VALUES
('user-demo-1', 'org-demo-1', 'developer', NOW()),
('user-demo-2', 'org-demo-1', 'security_admin', NOW()),
('user-demo-3', 'org-demo-2', 'admin', NOW()),
('user-demo-4', 'org-demo-3', 'owner', NOW());

-- Create demo integrations
INSERT INTO integrations (id, organization_id, type, name, configuration, enabled, created_at, updated_at) VALUES
('integration-demo-1', 'org-demo-1', 'slack', 'Security Alerts', '{"webhook_url": "https://hooks.slack.com/demo", "channel": "#security"}', true, NOW(), NOW()),
('integration-demo-2', 'org-demo-2', 'jira', 'Issue Tracking', '{"server_url": "https://techstart.atlassian.net", "project_key": "SEC"}', true, NOW(), NOW()),
('integration-demo-3', 'org-demo-3', 'pagerduty', 'Critical Alerts', '{"service_key": "demo-service-key", "escalation_policy": "P1"}', true, NOW(), NOW());

COMMIT;
