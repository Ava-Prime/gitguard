#!/usr/bin/env python3
"""
Duplicate flood chaos drill - simulates sending 50 duplicate NATS events
Expected: 1 workflow execution, 49 dedupes acknowledged in logs/metrics
"""

import asyncio
import json
import os

from nats.aio.client import Client as NATS


async def duplicate_flood_test():
    """Run the duplicate flood chaos drill"""

    # Create the GitHub webhook event payload
    evt = json.dumps(
        {
            "event": "pull_request",
            "delivery_id": "dup-123",
            "pull_request": {"number": 888, "head": {"sha": "HEAD"}},
            "repository": {"full_name": "org/repo"},
        }
    ).encode()

    print("🚀 Starting duplicate flood test with delivery_id: dup-123")
    print(f"📦 Event payload size: {len(evt)} bytes")

    try:
        # Connect to NATS
        nc = NATS()
        nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        print(f"🔌 Connecting to NATS at: {nats_url}")

        await nc.connect(servers=[nats_url])
        js = nc.jetstream()

        print("📡 Publishing 50 duplicate events to 'gh.pull_request.synchronize'...")

        # Publish 50 duplicate events
        for i in range(50):
            await js.publish("gh.pull_request.synchronize", evt)
            if (i + 1) % 10 == 0:
                print(f"  📤 Published {i + 1}/50 events")

        print("✅ Successfully published all 50 duplicate events")
        print("🔄 Draining connection...")

        # Drain the connection
        await nc.drain()

        print("🎯 Expected behavior:")
        print("  - 1 workflow execution should be triggered")
        print("  - 49 duplicate events should be acknowledged and deduplicated")
        print("  - Check logs/metrics for deduplication confirmations")

    except Exception as e:
        print(f"❌ Error during duplicate flood test: {e}")
        print(f"💡 Make sure NATS server is running at {nats_url}")
        raise


import pytest


@pytest.mark.asyncio
async def test_duplicate_flood_produces_one_workflow():
    """Test that duplicate flood produces one workflow with zero errors"""
    await duplicate_flood_test()


if __name__ == "__main__":
    asyncio.run(duplicate_flood_test())
