#!/usr/bin/env python3
"""Scheduler for periodic maintenance tasks."""

import asyncio
import os
from datetime import timedelta

from maintenance_workflow import MaintenanceWorkflow
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)


async def setup_maintenance_schedule():
    """Set up periodic maintenance schedule."""
    client = await Client.connect(
        os.getenv("TEMPORAL_HOST", "temporal:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
    )

    # Create schedule for daily maintenance at 2 AM
    schedule_id = "codex-maintenance-schedule"

    try:
        # Try to create the schedule
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    MaintenanceWorkflow.run, id="codex-maintenance", task_queue="codex-task-queue"
                ),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(
                            every=timedelta(days=1),  # Run daily
                            offset=timedelta(hours=2),  # At 2 AM
                        )
                    ]
                ),
            ),
        )
        print(f"✓ Created maintenance schedule: {schedule_id}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"✓ Maintenance schedule already exists: {schedule_id}")
        else:
            print(f"✗ Failed to create maintenance schedule: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(setup_maintenance_schedule())
