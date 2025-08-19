from __future__ import annotations

from datetime import timedelta
from typing import Any

from activities import cleanup_database
from temporalio import workflow


@workflow.defn
class MaintenanceWorkflow:
    """Scheduled workflow for database maintenance and cleanup tasks."""

    @workflow.run
    async def run(self) -> dict[str, Any]:
        """Run periodic maintenance tasks."""

        # Run database cleanup
        cleanup_result = await workflow.execute_activity(
            cleanup_database, start_to_close_timeout=timedelta(minutes=10)
        )

        return {
            "maintenance_completed": True,
            "cleanup_result": cleanup_result,
            "timestamp": workflow.now(),
        }
