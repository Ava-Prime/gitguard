from __future__ import annotations
import asyncio
from datetime import timedelta
from typing import Dict, Any
from temporalio import workflow
from activities import cleanup_database

@workflow.defn
class MaintenanceWorkflow:
    """Scheduled workflow for database maintenance and cleanup tasks."""
    
    @workflow.run
    async def run(self) -> Dict[str, Any]:
        """Run periodic maintenance tasks."""
        
        # Run database cleanup
        cleanup_result = await workflow.execute_activity(
            cleanup_database,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        return {
            "maintenance_completed": True,
            "cleanup_result": cleanup_result,
            "timestamp": workflow.now()
        }