# apps/guard-codex/src/activities/code_analysis.py
"""
GitGuard Codex - Temporal Activities for Code Intelligence
Integrates with existing GitGuard workflows for knowledge extraction
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import tree_sitter
from tree_sitter import Language, Parser
import git
import ast
import tempfile
import hashlib
import requests
from jinja2 import Template, Environment, FileSystemLoader
import asyncpg
import openai
from temporalio import activity

# GitHub App token from existing GitGuard infrastructure
from core.github_client import GitHubAppClient

@activity.defn
async def extract_github_facts(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured facts from GitHub webhook payload
    Reuses existing GitGuard GitHub App authentication
    """
    try:
        event_type = event.get("action", "unknown")
        repo_full_name = event["repository"]["full_name"]
        
        facts = {
            "event_type": event_type,
            "repo": repo_full_name,
            "timestamp": datetime.now().isoformat(),
            "delivery_id": event.get("delivery_id"),
        }
        
        # Extract PR-specific facts
        if "pull_request" in event:
            pr = event["pull_request"]
            facts["pr"] = {
                "number": pr["number"],
                "title": pr["title"],
                "body": pr["body"] or "",
                "author": pr["user"]["login"],
                "base_sha": pr["base"]["sha"],
                "head_sha": pr["head"]["sha"],
                "state": pr["state"],
                "draft": pr["draft"],
                "mergeable": pr.get("mergeable"),
                "changed_files": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "labels": [label["name"] for label in pr.get("labels", [])],
                "requested_reviewers": [r["login"] for r in pr.get("requested_reviewers", [])],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
            }
            
            # Get file changes using GitHub API
            github_client = GitHubAppClient()
            files_changed = await github_client.get_pr_files(repo_full_name, pr["number"])
            facts["files_changed"] = [
                {
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                    "changes": f["changes"],
                    "patch": f.get("patch", "")
                }
                for f in files_changed
            ]
        
        # Extract commit facts
        if "head_commit" in event:
            commit = event["head_commit"]
            facts["commit"] = {
                "sha": commit["id"],
                "message": commit["message"],
                "author": commit["author"]["name"],
                "timestamp": commit["timestamp"],
                "added": commit.get("added", []),
                "removed": commit.get("removed", []),
                "modified": commit.get("modified", []),
            }
        
        # Extract release facts
        if "release" in event:
            release = event["release"]
            facts["release"] = {
                "tag_name": release["tag_name"],
                "name": release["name"],
                "body": release["body"] or "",
                "draft": release["draft"],
                "prerelease": release["prerelease"],
                "created_at": release["created_at"],
                "published_at": release["published_at"],
            }
        
        return facts
        
    except Exception as e:
        activity.logger.error(f"Failed to extract GitHub facts: {e}")
        raise

@activity.defn  
async def analyze_code_impact(repo: str, sha: str, files_changed: List[Dict]) -> Dict[str, Any]:
    """
    Deep code analysis: symbols, complexity, coverage, security
    """
    analysis = {
        "repo": repo,
        "sha": sha,
        "symbols_changed": [],
        "complexity_metrics": {},
        "test_coverage": {},
        "security_findings": [],
        "performance_impact": {},
        "dependencies_changed": [],
    }
    
    try:
        # Clone repository for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "repo"
            
            # Use existing GitGuard GitHub App token
            github_client = GitHubAppClient()
            clone_url = await github_client.get_clone_url(repo)
            
            # Git clone with depth=1 for efficiency
            git.Repo.clone_from(clone_url, repo_path, depth=1)
            
            # Checkout specific SHA
            repo_obj = git.Repo(repo_path)
            repo_obj.git.checkout(sha)
            
            # Analyze each changed file
            for file_info in files_changed:
                file_path = repo_path / file_info["filename"]
                
                if file_path.exists() and file_path.is_file():
                    file_analysis = await analyze_single_file(file_path, file_info)
                    analysis["symbols_changed"].extend(file_analysis["symbols"])
                    
                    # Aggregate metrics
                    if file_analysis["complexity"]:
                        analysis["complexity_metrics"][file_info["filename"]] = file_analysis["complexity"]
            
            # Run test coverage analysis
            analysis["test_coverage"] = await run_coverage_analysis(repo_path)
            
            # Run security scans
            analysis["security_findings"] = await run_security_scan(repo_path, files_changed)
            
            # Check dependency changes
            analysis["dependencies_changed"] = await analyze_dependency_changes(repo_path, files_changed)
            
            # Performance benchmarks (if available)
            analysis["performance_impact"] = await run_performance_benchmarks(repo_path)
    
    except Exception as e:
        activity.logger.error(f"Code analysis failed for {repo}@{sha}: {e}")
        # Return partial analysis rather than failing completely
        analysis["analysis_error"] = str(e)
    
    return analysis

async def analyze_single_file(file_path: Path, file_info: Dict) -> Dict[str, Any]:
    """Analyze a single file for symbols, complexity, and patterns"""
    file_analysis = {
        "symbols": [],
        "complexity": None,
        "patterns": [],
        "language": detect_language(file_path)
    }
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Language-specific analysis
        if file_analysis["language"] == "python":
            file_analysis.update(await analyze_python_file(content, file_path))
        elif file_analysis["language"] in ["javascript", "typescript"]:
            file_analysis.update(await analyze_js_file(content, file_path))
        elif file_analysis["language"] in ["java", "kotlin"]:
            file_analysis.update(await analyze_java_file(content, file_path))
        
        # Generic complexity metrics
        file_analysis["complexity"] = {
            "lines_of_code": len([l for l in content.split('\n') if l.strip()]),
            "cyclomatic_complexity": calculate_cyclomatic_complexity(content),
            "maintainability_index": calculate_maintainability_index(content),
        }
        
    except Exception as e:
        activity.logger.warning(f"Failed to analyze {file_path}: {e}")
    
    return file_analysis

async def analyze_python_file(content: str, file_path: Path) -> Dict[str, Any]:
    """Python-specific analysis using AST"""
    symbols = []
    patterns = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    "type": "function",
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "args_count": len(node.args.args),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                })
            
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "type": "class", 
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    "base_classes": [b.id for b in node.bases if isinstance(b, ast.Name)],
                })
        
        # Detect common patterns
        if "import os" in content or "os.system" in content:
            patterns.append({"type": "os_command_execution", "risk": "medium"})
        
        if "eval(" in content or "exec(" in content:
            patterns.append({"type": "dynamic_code_execution", "risk": "high"})
            
    except SyntaxError:
        activity.logger.warning(f"Python syntax error in {file_path}")
    
    return {"symbols": symbols, "patterns": patterns}

@activity.defn
async def update_knowledge_graph(facts: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Update knowledge graph with new facts and relationships
    """
    async with asyncpg.create_pool(
        "postgresql://gitguard:password@localhost:5432/gitguard"
    ) as pool:
        async with pool.acquire() as conn:
            
            # Upsert repository
            await conn.execute("""
                INSERT INTO repositories (name, last_updated, metadata)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET
                    last_updated = $2,
                    metadata = $3
            """, facts["repo"], datetime.now(), json.dumps(analysis.get("complexity_metrics", {})))
            
            # Upsert PR if present
            if facts.get("pr"):
                pr = facts["pr"]
                pr_id = await conn.fetchval("""
                    INSERT INTO pull_requests (
                        repo_name, number, title, author, state, 
                        risk_score, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (repo_name, number) DO UPDATE SET
                        state = $5,
                        risk_score = $6,
                        metadata = $7
                    RETURNING id
                """, 
                facts["repo"], pr["number"], pr["title"], pr["author"], 
                pr["state"], analysis.get("risk_score", 50), 
                json.dumps(analysis), pr["created_at"]
                )
                
                # Link PR to changed files
                for file_info in facts.get("files_changed", []):
                    await conn.execute("""
                        INSERT INTO pr_file_changes (pr_id, file_path, change_type, additions, deletions)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (pr_id, file_path) DO UPDATE SET
                            change_type = $3, additions = $4, deletions = $5
                    """, pr_id, file_info["filename"], file_info["status"], 
                    file_info["additions"], file_info["deletions"])
            
            # Upsert symbols
            for symbol in analysis.get("symbols_changed", []):
                await conn.execute("""
                    INSERT INTO symbols (repo_name, name, type, file_path, complexity_score, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (repo_name, name, file_path) DO UPDATE SET
                        type = $3,
                        complexity_score = $5,
                        metadata = $6
                """, facts["repo"], symbol["name"], symbol["type"], 
                symbol.get("file_path", ""), symbol.get("complexity", 0), json.dumps(symbol))

@activity.defn
async def render_documentation(facts: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Generate markdown documentation from analysis
    """
    docs_base_path = Path("docs/generated")
    repo_slug = facts["repo"].replace("/", "_")
    repo_docs_path = docs_base_path / repo_slug
    
    # Ensure directories exist
    repo_docs_path.mkdir(parents=True, exist_ok=True)
    (repo_docs_path / "prs").mkdir(exist_ok=True)
    (repo_docs_path / "symbols").mkdir(exist_ok=True)
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("templates"))
    
    # Render PR documentation if this is a PR event
    if facts.get("pr"):
        await render_pr_documentation(env, repo_docs_path, facts, analysis)
    
    # Update repository overview
    await render_repository_overview(env, repo_docs_path, facts, analysis)
    
    # Update symbol documentation
    await render_symbol_documentation(env, repo_docs_path, analysis)
    
    # Update governance documentation
    await render_governance_documentation(env, repo_docs_path, facts, analysis)
    
    return str(repo_docs_path)

async def render_pr_documentation(env: Environment, docs_path: Path, facts: Dict, analysis: Dict):
    """Render comprehensive PR documentation page"""
    pr = facts["pr"]
    
    # Calculate risk breakdown
    risk_factors = analyze_risk_factors(pr, analysis)
    
    # Generate AI summary
    ai_summary = await generate_ai_summary(pr, analysis)
    
    template = env.get_template("pr_page.md.j2")
    content = template.render(
        pr=pr,
        analysis=analysis,
        risk_factors=risk_factors,
        ai_summary=ai_summary,
        files_changed=facts.get("files_changed", []),
        symbols_changed=analysis.get("symbols_changed", []),
        security_findings=analysis.get("security_findings", []),
        timestamp=datetime.now().isoformat()
    )
    
    pr_file = docs_path / "prs" / f"{pr['number']}.md"
    pr_file.write_text(content, encoding='utf-8')

async def render_repository_overview(env: Environment, docs_path: Path, facts: Dict, analysis: Dict):
    """Update repository overview with latest metrics"""
    
    # Fetch repository metrics from database
    async with asyncpg.create_pool(
        "postgresql://gitguard:password@localhost:5432/gitguard"
    ) as pool:
        async with pool.acquire() as conn:
            metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT pr.id) as total_prs,
                    AVG(pr.risk_score) as avg_risk_score,
                    COUNT(*) FILTER (WHERE pr.state = 'merged') as merged_prs,
                    COUNT(*) FILTER (WHERE pr.created_at > NOW() - INTERVAL '7 days') as recent_prs
                FROM pull_requests pr
                WHERE pr.repo_name = $1
            """, facts["repo"])
            
            recent_activity = await conn.fetch("""
                SELECT number, title, author, state, risk_score, created_at
                FROM pull_requests
                WHERE repo_name = $1
                ORDER BY created_at DESC
                LIMIT 10
            """, facts["repo"])
    
    template = env.get_template("repo_overview.md.j2")
    content = template.render(
        repo=facts["repo"],
        metrics=dict(metrics) if metrics else {},
        recent_activity=[dict(r) for r in recent_activity],
        analysis=analysis,
        last_updated=datetime.now().isoformat()
    )
    
    overview_file = docs_path / "index.md"
    overview_file.write_text(content, encoding='utf-8')

async def render_symbol_documentation(env: Environment, docs_path: Path, analysis: Dict):
    """Generate documentation for code symbols"""
    for symbol in analysis.get("symbols_changed", []):
        symbol_file = docs_path / "symbols" / f"{symbol['name']}.md"
        
        template = env.get_template("symbol_page.md.j2")
        content = template.render(
            symbol=symbol,
            timestamp=datetime.now().isoformat()
        )
        
        symbol_file.write_text(content, encoding='utf-8')

def analyze_risk_factors(pr: Dict, analysis: Dict) -> Dict[str, Any]:
    """Break down risk score into component factors"""
    factors = {
        "size_risk": min(50, pr.get("changed_files", 0) * 5),  # Files changed
        "complexity_risk": sum(m.get("cyclomatic_complexity", 0) for m in analysis.get("complexity_metrics", {}).values()) / 10,
        "security_risk": len(analysis.get("security_findings", [])) * 15,
        "coverage_risk": max(0, -analysis.get("test_coverage", {}).get("delta", 0)) * 2,
        "author_risk": 20 if is_new_contributor(pr["author"]) else 0,
        "weekend_risk": 10 if is_weekend_submission(pr.get("created_at")) else 0,
    }
    
    factors["total_risk"] = sum(factors.values())
    factors["risk_level"] = "high" if factors["total_risk"] > 70 else "medium" if factors["total_risk"] > 40 else "low"
    
    return factors

async def generate_ai_summary(pr: Dict, analysis: Dict) -> str:
    """Generate AI-powered summary of PR impact"""
    try:
        prompt = f"""
        Analyze this pull request and provide a concise technical summary:
        
        Title: {pr['title']}
        Description: {pr.get('body', '')[:500]}
        Files changed: {len(analysis.get('symbols_changed', []))} symbols across {pr.get('changed_files', 0)} files
        Risk factors: {json.dumps(analyze_risk_factors(pr, analysis), indent=2)}
        
        Provide a 2-3 sentence summary focusing on:
        1. What this change accomplishes
        2. Potential risks or areas of concern
        3. Impact on system architecture/dependencies
        """
        
        # In production, this would call OpenAI API
        # For demo, return structured summary
        return f"This PR modifies {pr.get('changed_files', 0)} files affecting {len(analysis.get('symbols_changed', []))} code symbols. The changes appear to be {get_change_category(pr, analysis)} with {analyze_risk_factors(pr, analysis)['risk_level']} risk level. Key areas of impact include {get_impact_areas(analysis)}."
        
    except Exception as e:
        return f"AI summary unavailable: {str(e)}"

def get_change_category(pr: Dict, analysis: Dict) -> str:
    """Categorize the type of change based on files and symbols"""
    changed_files = pr.get("changed_files", 0)
    
    if any("test" in f.get("filename", "").lower() for f in analysis.get("files_changed", [])):
        return "test-focused"
    elif any("doc" in f.get("filename", "").lower() for f in analysis.get("files_changed", [])):
        return "documentation updates"
    elif changed_files > 20:
        return "large-scale refactoring"
    elif any("config" in f.get("filename", "").lower() for f in analysis.get("files_changed", [])):
        return "configuration changes"
    else:
        return "feature development"

def get_impact_areas(analysis: Dict) -> str:
    """Identify key impact areas from analysis"""
    areas = []
    
    if analysis.get("security_findings"):
        areas.append("security")
    if analysis.get("dependencies_changed"):
        areas.append("dependencies")
    if analysis.get("test_coverage", {}).get("delta", 0) != 0:
        areas.append("test coverage")
    if analysis.get("performance_impact"):
        areas.append("performance")
    
    return ", ".join(areas) if areas else "core functionality"

@activity.defn
async def publish_docs_portal(docs_path: str) -> Dict[str, str]:
    """
    Build and publish documentation portal using MkDocs
    """
    try:
        docs_path_obj = Path(docs_path)
        site_path = docs_path_obj / "site"
        
        # Build MkDocs site
        build_result = await build_mkdocs_site(docs_path_obj)
        
        if not build_result["success"]:
            raise Exception(f"MkDocs build failed: {build_result['error']}")
        
        # Deploy to hosting (GitHub Pages, S3, etc.)
        deploy_urls = await deploy_to_hosting(site_path)
        
        # Generate preview links for PR
        preview_urls = await generate_preview_links(docs_path_obj, deploy_urls)
        
        return {
            "main_url": deploy_urls["main"],
            "preview_url": preview_urls.get("pr_preview"),
            "build_status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        activity.logger.error(f"Failed to publish docs portal: {e}")
        return {
            "build_status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def build_mkdocs_site(docs_path: Path) -> Dict[str, Any]:
    """Build MkDocs site from markdown files"""
    try:
        # Generate mkdocs.yml if it doesn't exist
        mkdocs_config = docs_path / "mkdocs.yml"
        if not mkdocs_config.exists():
            await generate_mkdocs_config(docs_path)
        
        # Run MkDocs build
        result = subprocess.run(
            ["mkdocs", "build", "--clean"],
            cwd=docs_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Build timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def generate_mkdocs_config(docs_path: Path):
    """Generate MkDocs configuration for repository"""
    config = {
        "site_name": f"GitGuard Codex - {docs_path.name.replace('_', '/')}",
        "site_description": "AI-Powered Engineering Intelligence",
        "nav": [
            {"Overview": "index.md"},
            {"Pull Requests": [
                {"Recent": "prs/index.md"},
                {"Risk Analysis": "prs/risk-analysis.md"}
            ]},
            {"Code Symbols": [
                {"Overview": "symbols/index.md"},
                {"Dependencies": "symbols/dependencies.md"}
            ]},
            {"Governance": [
                {"Policies": "governance/policies.md"},
                {"ADRs": "governance/adrs.md"},
                {"Compliance": "governance/compliance.md"}
            ]}
        ],
        "theme": {
            "name": "material",
            "palette": {"scheme": "slate", "primary": "indigo"},
            "features": [
                "navigation.tabs",
                "navigation.sections", 
                "search.highlight",
                "content.code.copy"
            ]
        },
        "plugins": ["search", "git-revision-date-localized"],
        "markdown_extensions": [
            "admonition",
            "pymdownx.details",
            "pymdownx.superfences",
            "tables",
            {"toc": {"permalink": True}}
        ]
    }
    
    mkdocs_file = docs_path / "mkdocs.yml"
    mkdocs_file.write_text(yaml.dump(config, default_flow_style=False))

async def deploy_to_hosting(site_path: Path) -> Dict[str, str]:
    """Deploy built site to hosting platform"""
    
    # Option 1: GitHub Pages (via API)
    if should_deploy_to_github_pages():
        github_url = await deploy_to_github_pages(site_path)
        return {"main": github_url}
    
    # Option 2: S3 + CloudFront
    elif should_deploy_to_s3():
        s3_url = await deploy_to_s3(site_path)
        return {"main": s3_url}
    
    # Option 3: Local development
    else:
        return {"main": f"file://{site_path.absolute()}/index.html"}

async def deploy_to_github_pages(site_path: Path) -> str:
    """Deploy to GitHub Pages using existing GitGuard GitHub App"""
    # This would integrate with your existing GitHub App
    # Create a commit to gh-pages branch with built site
    github_client = GitHubAppClient()
    
    # Read all files in site directory
    site_files = {}
    for file_path in site_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(site_path)
            site_files[str(relative_path)] = file_path.read_text(encoding='utf-8')
    
    # Commit to gh-pages branch
    commit_sha = await github_client.create_or_update_files(
        repo="your-org/gitguard-docs",  # Dedicated docs repo
        files=site_files,
        message=f"Update docs from GitGuard Codex - {datetime.now().isoformat()}",
        branch="gh-pages"
    )
    
    return f"https://your-org.github.io/gitguard-docs"

# Utility functions
async def run_coverage_analysis(repo_path: Path) -> Dict[str, Any]:
    """Run test coverage analysis"""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=.", "--cov-report=json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        coverage_file = repo_path / "coverage.json"
        if coverage_file.exists():
            coverage_data = json.loads(coverage_file.read_text())
            return {
                "total_coverage": coverage_data["totals"]["percent_covered"],
                "delta": calculate_coverage_delta(coverage_data),
                "files": coverage_data["files"]
            }
    except Exception as e:
        activity.logger.warning(f"Coverage analysis failed: {e}")
    
    return {"total_coverage": 0, "delta": 0, "files": {}}

async def run_security_scan(repo_path: Path, files_changed: List[Dict]) -> List[Dict]:
    """Run security analysis on changed files"""
    findings = []
    
    try:
        # Run bandit for Python files
        python_files = [f["filename"] for f in files_changed if f["filename"].endswith(".py")]
        
        if python_files:
            result = subprocess.run(
                ["bandit", "-f", "json"] + python_files,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                for issue in bandit_results.get("results", []):
                    findings.append({
                        "tool": "bandit",
                        "severity": issue["issue_severity"],
                        "confidence": issue["issue_confidence"],
                        "description": issue["issue_text"],
                        "file": issue["filename"],
                        "line": issue["line_number"]
                    })
        
        # Add other security tools (semgrep, etc.)
        
    except Exception as e:
        activity.logger.warning(f"Security scan failed: {e}")
    
    return findings

def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
    suffix = file_path.suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript", 
        ".ts": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".swift": "swift",
        ".scala": "scala",
        ".clj": "clojure",
        ".sh": "bash",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".sql": "sql",
        ".md": "markdown",
        ".dockerfile": "dockerfile"
    }
    return language_map.get(suffix, "unknown")

def calculate_cyclomatic_complexity(content: str) -> int:
    """Calculate cyclomatic complexity (simplified)"""
    # Count decision points: if, elif, while, for, try, except, and, or
    decision_keywords = ["if", "elif", "while", "for", "try", "except", "and", "or", "case", "switch"]
    complexity = 1  # Base complexity
    
    for keyword in decision_keywords:
        complexity += content.count(f" {keyword} ") + content.count(f"\t{keyword} ")
    
    return complexity

def calculate_maintainability_index(content: str) -> float:
    """Calculate maintainability index (simplified)"""
    lines = len([l for l in content.split('\n') if l.strip()])
    complexity = calculate_cyclomatic_complexity(content)
    
    # Simplified maintainability index formula
    if lines == 0:
        return 100.0
    
    mi = 171 - 5.2 * math.log(lines) - 0.23 * complexity - 16.2 * math.log(lines) / lines
    return max(0, min(100, mi))

def is_new_contributor(author: str) -> bool:
    """Check if author is a new contributor (simplified)"""
    # This would check against contributor history in production
    return False  # Placeholder

def is_weekend_submission(created_at: str) -> bool:
    """Check if PR was submitted during weekend"""
    if not created_at:
        return False
    
    try:
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        return dt.weekday() >= 5  # Saturday = 5, Sunday = 6
    except:
        return False

import math
import yaml