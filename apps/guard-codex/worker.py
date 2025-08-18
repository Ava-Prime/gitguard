import asyncio, os
from datetime import timedelta
from temporalio.worker import Worker
from temporalio.client import Client
from activities import extract_event_facts, analyze_repo_state, update_graph, render_docs, publish_portal, cleanup_database
from workflow import CodexWorkflow
from maintenance_workflow import MaintenanceWorkflow
from metrics import start_metrics_server

async def main():
    client = await Client.connect(
        os.getenv("TEMPORAL_HOST", "temporal:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default")
    )
    
    # Temporal hardening: concurrency limits, timeouts, and heartbeats
    worker = Worker(
        client,
        task_queue="codex-task-queue",
        workflows=[CodexWorkflow, MaintenanceWorkflow],
        activities=[extract_event_facts, analyze_repo_state, update_graph, render_docs, publish_portal, cleanup_database],
        # Production hardening configurations
        max_concurrent_activities=64,
        max_concurrent_workflow_tasks=256,
        max_concurrent_local_activities=32,
        # Activity timeouts and heartbeats
        activity_heartbeat_timeout=timedelta(seconds=30),
        activity_start_to_close_timeout=timedelta(minutes=10),
        activity_schedule_to_close_timeout=timedelta(minutes=15),
        # Workflow timeouts
        workflow_task_timeout=timedelta(seconds=10),
        # Graceful shutdown timeout
        graceful_shutdown_timeout=timedelta(seconds=30),
    )
    
    print("[codex-worker] Starting with hardened configuration:")
    print(f"  - Max concurrent activities: 64")
    print(f"  - Max concurrent workflow tasks: 256")
    print(f"  - Activity heartbeat timeout: 30s")
    print(f"  - Activity execution timeout: 10m")
    
    # Start Prometheus metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "8090"))
    start_metrics_server(metrics_port)
    print(f"  - Metrics server: http://localhost:{metrics_port}/metrics")
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())