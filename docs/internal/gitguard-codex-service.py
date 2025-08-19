# apps/guard-codex/src/main.py
"""
GitGuard Codex Service - Knowledge Graph and Documentation Engine
Integrates with existing GitGuard infrastructure (Temporal, NATS, OPA)
"""

import asyncio
import json
import logging
from datetime import datetime

import asyncpg
import nats
from activities.code_analysis import (
    analyze_code_impact,
    extract_github_facts,
    publish_docs_portal,
    render_documentation,
    update_knowledge_graph,
)
from fastapi import FastAPI, HTTPException
from temporalio.client import Client as TemporalClient
from temporalio.worker import Worker

# Temporal workflow imports
from workflows.codex_flow import CodexWorkflow

app = FastAPI(title="GitGuard Codex", version="1.0.0")

# Global connections
temporal_client: TemporalClient | None = None
nats_client: nats.NATS | None = None
db_pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup():
    global temporal_client, nats_client, db_pool

    # Connect to Temporal (reuse existing connection)
    temporal_client = await TemporalClient.connect("localhost:7233")

    # Connect to NATS (reuse existing subjects)
    nats_client = await nats.connect("nats://localhost:4222")

    # Connect to Postgres (reuse existing database)
    db_pool = await asyncpg.create_pool("postgresql://gitguard:password@localhost:5432/gitguard")

    # Start background workers
    asyncio.create_task(start_codex_worker())
    asyncio.create_task(start_nats_listeners())


async def start_codex_worker():
    """Start Temporal worker for Codex workflows"""
    worker = Worker(
        temporal_client,
        task_queue="codex-tasks",
        workflows=[CodexWorkflow],
        activities=[
            extract_github_facts,
            analyze_code_impact,
            update_knowledge_graph,
            render_documentation,
            publish_docs_portal,
        ],
    )
    await worker.run()


async def start_nats_listeners():
    """Listen to GitHub events from existing GitGuard NATS subjects"""

    async def handle_github_event(msg):
        """Process GitHub events for knowledge graph updates"""
        try:
            event_data = json.loads(msg.data.decode())

            # Start Codex workflow via Temporal
            await temporal_client.execute_workflow(
                CodexWorkflow.run,
                event_data,
                id=f"codex-{event_data.get('delivery_id', datetime.now().isoformat())}",
                task_queue="codex-tasks",
            )

        except Exception as e:
            logging.error(f"Error processing GitHub event: {e}")

    # Subscribe to existing GitGuard NATS subjects
    await nats_client.subscribe("gh.push.*", cb=handle_github_event)
    await nats_client.subscribe("gh.pr.*", cb=handle_github_event)
    await nats_client.subscribe("gh.release.*", cb=handle_github_event)
    await nats_client.subscribe("gh.issue.*", cb=handle_github_event)


# API Endpoints for knowledge graph queries


@app.get("/api/knowledge/search")
async def search_knowledge(q: str, entity_type: str | None = None):
    """Semantic search across knowledge graph"""
    # Implementation would use pgvector similarity search
    query = """
    SELECT id, name, type, content,
           1 - (embedding <=> $1) as similarity
    FROM knowledge_entities
    WHERE ($2 IS NULL OR type = $2)
    ORDER BY embedding <=> $1
    LIMIT 20
    """

    # This would use actual embeddings in production
    async with db_pool.acquire() as conn:
        results = await conn.fetch(query, [], entity_type)

    return {"results": [dict(r) for r in results]}


@app.get("/api/repos/{owner}/{repo}/health")
async def get_repo_health(owner: str, repo: str):
    """Get comprehensive repository health metrics"""
    repo_name = f"{owner}/{repo}"

    async with db_pool.acquire() as conn:
        # Risk trend over time
        risk_trend = await conn.fetch(
            """
            SELECT DATE(created_at) as date, AVG(risk_score) as avg_risk
            FROM pull_requests
            WHERE repo_name = $1 AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """,
            repo_name,
        )

        # Test coverage trend
        coverage_trend = await conn.fetch(
            """
            SELECT DATE(merged_at) as date, AVG(coverage_delta) as avg_coverage
            FROM pull_requests
            WHERE repo_name = $1 AND status = 'merged'
              AND merged_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(merged_at)
            ORDER BY date
        """,
            repo_name,
        )

        # Policy compliance rate
        compliance = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_evaluations,
                COUNT(*) FILTER (WHERE result = 'pass') as passed,
                ROUND(COUNT(*) FILTER (WHERE result = 'pass')::numeric / COUNT(*) * 100, 2) as compliance_rate
            FROM policy_evaluations pe
            JOIN pull_requests pr ON pe.pr_id = pr.id
            WHERE pr.repo_name = $1 AND pe.created_at > NOW() - INTERVAL '30 days'
        """,
            repo_name,
        )

    return {
        "repo": repo_name,
        "health_score": calculate_health_score(risk_trend, coverage_trend, compliance),
        "risk_trend": [dict(r) for r in risk_trend],
        "coverage_trend": [dict(r) for r in coverage_trend],
        "compliance_rate": compliance["compliance_rate"] if compliance else 0,
        "recommendations": await generate_health_recommendations(repo_name),
    }


@app.get("/api/prs/{pr_id}/knowledge")
async def get_pr_knowledge_context(pr_id: int):
    """Get knowledge context for a PR - related changes, experts, risks"""
    async with db_pool.acquire() as conn:
        # Get PR details
        pr = await conn.fetchrow("SELECT * FROM pull_requests WHERE id = $1", pr_id)
        if not pr:
            raise HTTPException(404, "PR not found")

        # Find related PRs (similar file changes)
        related_prs = await conn.fetch(
            """
            SELECT pr.*, COUNT(DISTINCT pfc1.file_id) as shared_files
            FROM pull_requests pr
            JOIN pr_file_changes pfc1 ON pr.id = pfc1.pr_id
            WHERE pfc1.file_id IN (
                SELECT file_id FROM pr_file_changes WHERE pr_id = $1
            ) AND pr.id != $1
            GROUP BY pr.id
            ORDER BY shared_files DESC, pr.created_at DESC
            LIMIT 10
        """,
            pr_id,
        )

        # Find experts (developers who frequently touch these files)
        experts = await conn.fetch(
            """
            SELECT pr.author, COUNT(*) as expertise_score
            FROM pull_requests pr
            JOIN pr_file_changes pfc ON pr.id = pfc.pr_id
            WHERE pfc.file_id IN (
                SELECT file_id FROM pr_file_changes WHERE pr_id = $1
            ) AND pr.status = 'merged'
            GROUP BY pr.author
            ORDER BY expertise_score DESC
            LIMIT 5
        """,
            pr_id,
        )

        # Get impacted ADRs and policies
        governance = await conn.fetch(
            """
            SELECT DISTINCT a.number, a.title, a.status, 'adr' as type
            FROM adrs a
            JOIN adr_file_impacts afi ON a.id = afi.adr_id
            WHERE afi.file_id IN (
                SELECT file_id FROM pr_file_changes WHERE pr_id = $1
            )
            UNION
            SELECT DISTINCT p.id::text, p.name, 'active', 'policy'
            FROM policies p
            JOIN policy_evaluations pe ON p.id = pe.policy_id
            WHERE pe.pr_id = $1
        """,
            pr_id,
        )

    return {
        "pr": dict(pr),
        "related_changes": [dict(r) for r in related_prs],
        "suggested_reviewers": [dict(e) for e in experts],
        "governance_context": [dict(g) for g in governance],
        "knowledge_links": await generate_knowledge_links(pr_id),
    }


def calculate_health_score(risk_trend, coverage_trend, compliance) -> float:
    """Calculate overall repository health score (0-100)"""
    # Risk score (lower is better)
    avg_risk = sum(r["avg_risk"] for r in risk_trend) / len(risk_trend) if risk_trend else 50
    risk_score = max(0, 100 - avg_risk)

    # Coverage score
    latest_coverage = coverage_trend[-1]["avg_coverage"] if coverage_trend else 0
    coverage_score = min(100, max(0, latest_coverage + 50))  # Normalize around 50% baseline

    # Compliance score
    compliance_score = compliance.get("compliance_rate", 0) if compliance else 0

    # Weighted average
    health_score = risk_score * 0.4 + coverage_score * 0.3 + compliance_score * 0.3
    return round(health_score, 1)


async def generate_health_recommendations(repo_name: str) -> list[str]:
    """Generate actionable recommendations for repository health"""
    recommendations = []

    async with db_pool.acquire() as conn:
        # Check test coverage
        low_coverage_files = await conn.fetch(
            """
            SELECT file_path FROM files
            WHERE repo_name = $1 AND test_coverage < 60
            ORDER BY test_coverage ASC
            LIMIT 5
        """,
            repo_name,
        )

        if low_coverage_files:
            recommendations.append(
                f"Improve test coverage for {len(low_coverage_files)} files with <60% coverage"
            )

        # Check high-risk patterns
        risky_patterns = await conn.fetch(
            """
            SELECT pattern_type, COUNT(*) as occurrences
            FROM risk_patterns rp
            JOIN pull_requests pr ON rp.pr_id = pr.id
            WHERE pr.repo_name = $1 AND pr.created_at > NOW() - INTERVAL '30 days'
            GROUP BY pattern_type
            HAVING COUNT(*) > 2
        """,
            repo_name,
        )

        for pattern in risky_patterns:
            recommendations.append(
                f"Address recurring {pattern['pattern_type']} pattern ({pattern['occurrences']} recent occurrences)"
            )

    return recommendations


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None,
        "nats_connected": nats_client is not None,
        "database_connected": db_pool is not None,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
