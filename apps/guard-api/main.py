import hashlib
import hmac
import json
import os
import time

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response
from nats.aio.client import Client as NATS
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel
from temporalio.client import Client as Temporal

from apps.shared.config import settings
from apps.shared.logging import configure_logging, logger
from apps.shared.middleware import RequestIDMiddleware, add_health_routes

from .metrics import (
    MetricsMiddleware,
    record_codex_request,
    record_connection_status,
    record_nats_message,
    record_webhook_event,
    record_webhook_signature_validation,
    start_metrics_server,
)

# Constants
LOW_RISK_THRESHOLD = 0.30

app = FastAPI(title="GitGuard API", version="1.0.0")

# Configure shared infrastructure
configure_logging(settings.log_level)
app.add_middleware(RequestIDMiddleware)
add_health_routes(app)
logger.info("guard-api_boot", env=settings.environment, temporal_host=settings.temporal_host)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

CODEX_URL = os.getenv("CODEX_URL", "http://codex:8010")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")  # empty -> skip verify (demo)
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")

# Clients will be stored in app.state instead of global variables


class PRAudit(BaseModel):
    number: int
    title: str | None = None
    labels: list[str] = []
    risk_score: float = 0.0
    checks_passed: bool = False
    changed_paths: list[str] = []
    coverage_delta: float = 0.0
    perf_delta: float = 0.0
    policies: list[str] = []
    release_window_state: str = "open"
    summary: str = ""


def _verify_signature(secret: str, signature: str | None, body_bytes: bytes) -> bool:
    if not secret:
        return True  # demo mode
    if not signature or not signature.startswith("sha256="):
        return False
    mac = hmac.new(secret.encode(), msg=body_bytes, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={mac}", signature)


@app.on_event("startup")
async def startup_event():
    # Initialize clients in app.state instead of global variables
    app.state.nats_client = None
    app.state.temporal_client = None

    # Start Prometheus metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "8080"))
    start_metrics_server(metrics_port)
    print(f"[guard-api] Metrics server started on port {metrics_port}")

    try:
        # Initialize NATS client
        app.state.nats_client = NATS()
        await app.state.nats_client.connect(servers=[NATS_URL])
        print(f"[guard-api] Connected to NATS at {NATS_URL}")
        record_connection_status("nats", True)

        # Initialize Temporal client
        app.state.temporal_client = await Temporal.connect(TEMPORAL_ADDRESS)
        print(f"[guard-api] Connected to Temporal at {TEMPORAL_ADDRESS}")
        record_connection_status("temporal", True)
    except Exception as e:
        print(f"[guard-api] Warning: Failed to initialize clients: {e}")
        record_connection_status("nats", False)
        record_connection_status("temporal", False)
        # Continue without clients for demo purposes


@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "nats_client") and app.state.nats_client:
        await app.state.nats_client.close()
        record_connection_status("nats", False)
    if hasattr(app.state, "temporal_client") and app.state.temporal_client:
        record_connection_status("temporal", False)
        await app.state.temporal_client.close()


@app.post("/webhook/github")
async def github_webhook(
    req: Request,
    x_github_event: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
    x_hub_signature_256: str = Header(default=None),
):
    start_time = time.time()
    event_type = x_github_event or "unknown"
    action = "unknown"

    body_bytes = await req.body()

    # Record signature validation
    signature_valid = _verify_signature(WEBHOOK_SECRET, x_hub_signature_256, body_bytes)
    record_webhook_signature_validation(signature_valid)

    if not signature_valid:
        record_webhook_event(event_type, action, False, time.time() - start_time)
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        body = json.loads(body_bytes.decode("utf-8"))
        action = body.get("action", "unknown")
    except Exception as e:
        record_webhook_event(event_type, action, False, time.time() - start_time)
        raise HTTPException(status_code=400, detail="invalid json") from e

    pr = body.get("pull_request") or {}
    analysis = body.get("analysis") or {}
    changes = body.get("changes") or {}

    payload = PRAudit(
        number=int(pr.get("number") or 0),
        title=pr.get("title") or "",
        labels=(
            ["risk:low"]
            if float(analysis.get("risk_score") or 0.0) <= LOW_RISK_THRESHOLD
            else ["risk:med"]
        ),
        risk_score=round(float(analysis.get("risk_score") or 0.0), 3),
        checks_passed=bool(analysis.get("checks_passed", True)),  # demo default
        changed_paths=list(changes.get("files") or []),
        coverage_delta=float(analysis.get("coverage_delta") or 0.0),
        perf_delta=float(analysis.get("performance_delta") or 0.0),
        policies=["release-window"] if body.get("action") == "create_tag" else [],
        release_window_state="blocked" if body.get("action") == "create_tag" else "open",
        summary=f"Autogenerated digest for PR #{pr.get('number')}",
    ).model_dump()

    # Legacy HTTP call to Codex (for backward compatibility)
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            codex_start = time.time()
            response = await client.post(f"{CODEX_URL}/codex/pr-digest", json=payload)
            record_codex_request(
                "/codex/pr-digest", response.status_code, time.time() - codex_start
            )
        except Exception as e:
            # Non-fatal in demo: continue with NATS publishing
            record_codex_request("/codex/pr-digest", 0, time.time() - codex_start)
            print(f"[guard-api] Codex HTTP call failed: {e}")

    # Publish event to NATS for Temporal workflow processing
    subject = f"gh.{event_type}.{action}"

    if hasattr(app.state, "nats_client") and app.state.nats_client:
        try:
            # Create enriched event payload for Codex workflow
            event_payload = {
                "event": event_type,
                "action": body.get("action", "unknown"),
                "delivery_id": x_github_delivery,
                "repository": body.get("repository", {}),
                "pull_request": body.get("pull_request", {}),
                "release": body.get("release", {}),
                "sender": body.get("sender", {}),
                # Add processed analysis data
                "risk": {"score": payload["risk_score"]},
                "checks": {"all_passed": payload["checks_passed"]},
                "changed_files": payload["changed_paths"],
                "coverage_delta": payload["coverage_delta"],
                "perf_delta": payload["perf_delta"],
                "release_window_state": payload["release_window_state"],
                "summary": payload["summary"],
            }

            await app.state.nats_client.publish(subject, json.dumps(event_payload).encode())
            record_nats_message(subject, True)
            print(f"[guard-api] Published to NATS: {subject}")
        except Exception as e:
            record_nats_message(subject, False)
            print(f"[guard-api] NATS publish failed: {e}")

    # Record successful webhook processing
    record_webhook_event(event_type, action, True, time.time() - start_time)

    return {"status": "processed", "delivery_id": x_github_delivery}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
