from __future__ import annotations
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from temporalio import activity, workflow
import logging

# Prometheus metrics for Temporal workflows and activities
workflow_executions_total = Counter(
    'temporal_workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_type', 'status']
)

workflow_duration_seconds = Histogram(
    'temporal_workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type']
)

activity_executions_total = Counter(
    'temporal_activity_executions_total',
    'Total number of activity executions',
    ['activity_name', 'status']
)

activity_duration_seconds = Histogram(
    'temporal_activity_duration_seconds',
    'Activity execution duration in seconds',
    ['activity_name']
)

activity_failures_total = Counter(
    'temporal_activity_failures_total',
    'Total number of activity failures',
    ['activity_name', 'failure_type']
)

workflow_failures_total = Counter(
    'temporal_workflow_failures_total',
    'Total number of workflow failures',
    ['workflow_type', 'failure_type']
)

active_workflows = Gauge(
    'temporal_active_workflows',
    'Number of currently active workflows',
    ['workflow_type']
)

active_activities = Gauge(
    'temporal_active_activities',
    'Number of currently active activities',
    ['activity_name']
)

# Codex-specific metrics
codex_events_processed_total = Counter(
    'codex_events_processed_total',
    'Total number of events processed by Codex',
    ['event_type', 'status']
)

codex_docs_generated_total = Counter(
    'codex_docs_generated_total',
    'Total number of documentation pages generated',
    ['doc_type']
)

codex_graph_updates_total = Counter(
    'codex_graph_updates_total',
    'Total number of knowledge graph updates',
    ['update_type']
)

logger = logging.getLogger(__name__)

def start_metrics_server(port: int = 8090) -> None:
    """Start Prometheus metrics HTTP server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

def record_workflow_start(workflow_type: str) -> None:
    """Record workflow start."""
    active_workflows.labels(workflow_type=workflow_type).inc()

def record_workflow_completion(workflow_type: str, duration: float, success: bool = True) -> None:
    """Record workflow completion."""
    status = 'success' if success else 'failure'
    workflow_executions_total.labels(workflow_type=workflow_type, status=status).inc()
    workflow_duration_seconds.labels(workflow_type=workflow_type).observe(duration)
    active_workflows.labels(workflow_type=workflow_type).dec()

def record_workflow_failure(workflow_type: str, failure_type: str) -> None:
    """Record workflow failure."""
    workflow_failures_total.labels(workflow_type=workflow_type, failure_type=failure_type).inc()

def record_activity_start(activity_name: str) -> None:
    """Record activity start."""
    active_activities.labels(activity_name=activity_name).inc()

def record_activity_completion(activity_name: str, duration: float, success: bool = True) -> None:
    """Record activity completion."""
    status = 'success' if success else 'failure'
    activity_executions_total.labels(activity_name=activity_name, status=status).inc()
    activity_duration_seconds.labels(activity_name=activity_name).observe(duration)
    active_activities.labels(activity_name=activity_name).dec()

def record_activity_failure(activity_name: str, failure_type: str) -> None:
    """Record activity failure."""
    activity_failures_total.labels(activity_name=activity_name, failure_type=failure_type).inc()

def record_codex_event(event_type: str, success: bool = True) -> None:
    """Record Codex event processing."""
    status = 'success' if success else 'failure'
    codex_events_processed_total.labels(event_type=event_type, status=status).inc()

def record_docs_generation(doc_type: str) -> None:
    """Record documentation generation."""
    codex_docs_generated_total.labels(doc_type=doc_type).inc()

def record_graph_update(update_type: str) -> None:
    """Record knowledge graph update."""
    codex_graph_updates_total.labels(update_type=update_type).inc()

class MetricsActivityDecorator:
    """Decorator to add metrics to Temporal activities."""
    
    def __init__(self, activity_func):
        self.activity_func = activity_func
        self.activity_name = activity_func.__name__
    
    async def __call__(self, *args, **kwargs):
        start_time = time.time()
        record_activity_start(self.activity_name)
        
        try:
            result = await self.activity_func(*args, **kwargs)
            duration = time.time() - start_time
            record_activity_completion(self.activity_name, duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            record_activity_completion(self.activity_name, duration, success=False)
            record_activity_failure(self.activity_name, type(e).__name__)
            raise

def metrics_activity(func):
    """Decorator to add metrics to activities."""
    return MetricsActivityDecorator(func)