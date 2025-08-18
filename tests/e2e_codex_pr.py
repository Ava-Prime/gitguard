# tests/e2e_codex_pr.py
import os, json, asyncio, time, psycopg
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
DB_URL = os.getenv("DATABASE_URL")

PR = {
    "event": "pull_request",
    "delivery_id": "e2e-PR-0001",
    "repository": {"full_name": f"{os.environ.get('GITHUB_OWNER','org')}/{os.environ.get('GITHUB_REPO','repo')}"},
    "pull_request": {"number": 777, "title": "E2E Codex PR", "head": {"sha": "HEAD"}, "user": {"login": "phoenix"}, "labels": [{"name": "test"}]},
    "changed_files": ["apps/guard-codex/activities.py", "docs/adr/0001-foo.md"],
    "risk": {"score": 2.7}, "checks": {"all_passed": True},
    "coverage_delta": +0.4, "perf_delta": -0.2, "release_window_state": "open",
    "policies": ["repo.guard.automerge"], "adrs": ["0001-foo"]
}

async def emit(subject, payload):
    nc = NATS(); await nc.connect(servers=[NATS_URL]); js = nc.jetstream()
    await js.publish(subject, json.dumps(payload).encode()); await nc.drain()

def wait_for(predicate, timeout=30, step=0.5):
    start = time.time()
    while time.time() - start < timeout:
        if predicate(): return True
        time.sleep(step)
    return False

def test_pr_ingests_and_renders():
    asyncio.run(emit("gh.pull_request.opened", PR))

    def graph_ok():
        with psycopg.connect(DB_URL) as c, c.cursor() as cur:
            cur.execute("select count(*) from codex_nodes where ntype='PR' and nkey='pr:777'")
            pr = cur.fetchone()[0]
            cur.execute("select count(*) from codex_edges where rel='touches'")
            edges = cur.fetchone()[0]
            return pr == 1 and edges >= 1
    assert wait_for(graph_ok, 60), "Graph did not populate"

    # docs file present
    docs = os.path.join(os.environ.get("CODEX_DOCS_DIR", "docs"), "prs", "777.md")
    assert wait_for(lambda: os.path.exists(docs), 30), "PR page not rendered"