from __future__ import annotations

import logging
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Risk score thresholds
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.7

# API path parsing constants
MIN_API_PATH_PARTS = 4

# API-specific metrics
api_requests_total = Counter(
    "guard_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
)

api_request_duration_seconds = Histogram(
    "guard_api_request_duration_seconds", "API request duration in seconds", ["method", "endpoint"]
)

webhook_events_total = Counter(
    "guard_api_webhook_events_total",
    "Total number of GitHub webhook events received",
    ["event_type", "action", "status"],
)

webhook_processing_duration_seconds = Histogram(
    "guard_api_webhook_processing_duration_seconds",
    "Webhook processing duration in seconds",
    ["event_type", "action"],
)

webhook_signature_validations_total = Counter(
    "guard_api_webhook_signature_validations_total",
    "Total number of webhook signature validations",
    ["status"],
)

active_connections = Gauge(
    "guard_api_active_connections", "Number of active connections to external services", ["service"]
)

nats_messages_published_total = Counter(
    "guard_api_nats_messages_published_total",
    "Total number of messages published to NATS",
    ["subject", "status"],
)

temporal_workflow_starts_total = Counter(
    "guard_api_temporal_workflow_starts_total",
    "Total number of Temporal workflows started",
    ["workflow_type", "status"],
)

risk_score_calculations_total = Counter(
    "guard_api_risk_score_calculations_total",
    "Total number of risk score calculations",
    ["result_category"],
)

risk_score_distribution = Histogram(
    "guard_api_risk_score_distribution",
    "Distribution of calculated risk scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

codex_requests_total = Counter(
    "guard_api_codex_requests_total",
    "Total number of requests to Codex service",
    ["endpoint", "status_code"],
)

codex_request_duration_seconds = Histogram(
    "guard_api_codex_request_duration_seconds", "Codex request duration in seconds", ["endpoint"]
)

REQUEST_LATENCY = Histogram(
    "gitguard_request_latency_ms", "Latency per endpoint", ["path", "method"]
)

logger = logging.getLogger(__name__)


def start_metrics_server(port: int = 8080) -> None:
    """Start Prometheus metrics HTTP server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")


def record_api_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """Record API request metrics."""
    api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_webhook_event(
    event_type: str, action: str, success: bool = True, duration: float | None = None
) -> None:
    """Record webhook event processing metrics."""
    status = "success" if success else "failure"
    webhook_events_total.labels(event_type=event_type, action=action, status=status).inc()

    if duration is not None:
        webhook_processing_duration_seconds.labels(event_type=event_type, action=action).observe(
            duration
        )


def record_webhook_signature_validation(success: bool = True) -> None:
    """Record webhook signature validation metrics."""
    status = "success" if success else "failure"
    webhook_signature_validations_total.labels(status=status).inc()


def record_connection_status(service: str, connected: bool) -> None:
    """Record connection status to external services."""
    active_connections.labels(service=service).set(1 if connected else 0)


def record_nats_message(subject: str, success: bool = True) -> None:
    """Record NATS message publishing metrics."""
    status = "success" if success else "failure"
    nats_messages_published_total.labels(subject=subject, status=status).inc()


def record_temporal_workflow_start(workflow_type: str, success: bool = True) -> None:
    """Record Temporal workflow start metrics."""
    status = "success" if success else "failure"
    temporal_workflow_starts_total.labels(workflow_type=workflow_type, status=status).inc()


def record_risk_score_calculation(risk_score: float) -> None:
    """Record risk score calculation metrics."""
    # Categorize risk scores
    if risk_score <= LOW_RISK_THRESHOLD:
        category = "low"
    elif risk_score <= MEDIUM_RISK_THRESHOLD:
        category = "medium"
    else:
        category = "high"

    risk_score_calculations_total.labels(result_category=category).inc()
    risk_score_distribution.observe(risk_score)


def record_codex_request(endpoint: str, status_code: int, duration: float) -> None:
    """Record Codex service request metrics."""
    codex_requests_total.labels(endpoint=endpoint, status_code=status_code).inc()
    codex_request_duration_seconds.labels(endpoint=endpoint).observe(duration)


def observe_latency(path: str, method: str, dur_ms: float):
    """Record request latency in milliseconds."""
    REQUEST_LATENCY.labels(path=path, method=method).observe(dur_ms)


class MetricsMiddleware:
    """FastAPI middleware for automatic request metrics collection."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope["method"]
        path = scope["path"]

        # Normalize endpoint paths to avoid high cardinality
        endpoint = self._normalize_endpoint(path)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time
                record_api_request(method, endpoint, status_code, duration)
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint paths to reduce cardinality."""
        # Replace dynamic segments with placeholders
        if path.startswith("/webhook"):
            return "/webhook"
        elif path.startswith("/health"):
            return "/health"
        elif path.startswith("/metrics"):
            return "/metrics"
        elif path.startswith("/api/v1/"):
            # Extract the main API endpoint
            parts = path.split("/")
            if len(parts) >= MIN_API_PATH_PARTS:
                return f"/api/v1/{parts[3]}"

        return path
