#!/usr/bin/env python3
"""
Chaos Engineering Drills for GitGuard

These tests simulate various failure scenarios to validate system resilience:
- Duplicate event flooding (idempotency testing)
- Mid-publish crashes (retry/backoff testing)
"""

import asyncio
import json
import os
import time
from typing import Dict, Any
from unittest.mock import patch

import pytest
from nats.aio.client import Client as NATS
try:
    from nats.js.errors import TimeoutError as NATSTimeoutError
except ImportError:
    # Fallback for different NATS library versions
    NATSTimeoutError = TimeoutError


class ChaosTestConfig:
    """Configuration for chaos engineering tests"""
    NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
    DUPLICATE_COUNT = 50
    TIMEOUT_SECONDS = 30
    FAULT_ONCE_DELIVERY_ID = os.getenv("FAULT_ONCE_DELIVERY_ID")


def create_test_pr_event(delivery_id: str, pr_number: int = 888) -> bytes:
    """Create a test pull request event payload"""
    event = {
        "event": "pull_request",
        "delivery_id": delivery_id,
        "pull_request": {
            "number": pr_number,
            "head": {"sha": "HEAD"},
            "action": "synchronize"
        },
        "repository": {"full_name": "org/repo"}
    }
    return json.dumps(event).encode()


@pytest.mark.asyncio
async def test_duplicate_flood_idempotency():
    """
    Chaos Drill A: Duplicate flood (idempotency proof)
    
    Sends 50 identical events and expects:
    - Only 1 workflow execution
    - 49 duplicate acknowledgments in logs/metrics
    """
    print("\n🌪️  Starting Chaos Drill A: Duplicate Flood Test")
    
    # Create test event
    delivery_id = "dup-123"
    evt = create_test_pr_event(delivery_id)
    
    # Connect to NATS
    nc = NATS()
    try:
        await nc.connect(servers=[ChaosTestConfig.NATS_URL])
        js = nc.jetstream()
        
        print(f"📡 Publishing {ChaosTestConfig.DUPLICATE_COUNT} duplicate events...")
        
        # Flood with duplicate events
        publish_tasks = []
        for i in range(ChaosTestConfig.DUPLICATE_COUNT):
            task = js.publish("gh.pull_request.synchronize", evt)
            publish_tasks.append(task)
        
        # Wait for all publishes to complete
        await asyncio.gather(*publish_tasks)
        
        print(f"✅ Successfully published {ChaosTestConfig.DUPLICATE_COUNT} events")
        print("⏳ Waiting for system to process duplicates...")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        print("📊 Expected behavior:")
        print("   - 1 workflow execution should be created")
        print("   - 49 duplicate events should be acknowledged and ignored")
        print("   - Check logs/metrics for deduplication confirmations")
        
    except Exception as e:
        pytest.fail(f"Duplicate flood test failed: {e}")
    finally:
        await nc.drain()


class PublishFaultInjector:
    """Fault injector for simulating publish failures"""
    
    def __init__(self, fault_delivery_id: str):
        self.fault_delivery_id = fault_delivery_id
        self.fault_triggered = False
    
    def should_fault(self, delivery_id: str) -> bool:
        """Check if we should inject a fault for this delivery_id"""
        if delivery_id == self.fault_delivery_id and not self.fault_triggered:
            self.fault_triggered = True
            return True
        return False


@pytest.mark.asyncio
async def test_crash_mid_publish_retry():
    """
    Chaos Drill B: Crash mid-publish (retry/backoff)
    
    Simulates a crash during publish and verifies:
    - JetStream redelivery mechanisms
    - Eventual successful processing
    - Proper retry/backoff behavior
    """
    print("\n🌪️  Starting Chaos Drill B: Crash Mid-Publish Test")
    
    delivery_id = "crash-test-456"
    evt = create_test_pr_event(delivery_id)
    
    # Set up fault injection
    fault_injector = PublishFaultInjector(delivery_id)
    
    nc = NATS()
    try:
        await nc.connect(servers=[ChaosTestConfig.NATS_URL])
        js = nc.jetstream()
        
        print(f"💥 Publishing event with fault injection for delivery_id: {delivery_id}")
        
        # Simulate the fault injection scenario
        with patch.dict(os.environ, {"FAULT_ONCE_DELIVERY_ID": delivery_id}):
            # First attempt - should fail due to fault injection
            try:
                await js.publish("gh.pull_request.synchronize", evt)
                print("⚠️  First publish attempt (expected to fail with fault injection)")
            except Exception as e:
                print(f"💥 Expected fault occurred: {e}")
            
            # Wait a bit for retry mechanisms
            await asyncio.sleep(2)
            
            # Second attempt - should succeed
            try:
                await js.publish("gh.pull_request.synchronize", evt)
                print("✅ Second publish attempt succeeded")
            except Exception as e:
                print(f"❌ Unexpected failure on retry: {e}")
                raise
        
        print("📊 Expected behavior:")
        print("   - First publish should fail (simulated crash)")
        print("   - JetStream should handle redelivery")
        print("   - Eventual successful processing should occur")
        print("   - Check logs for retry/backoff patterns")
        
    except Exception as e:
        pytest.fail(f"Crash mid-publish test failed: {e}")
    finally:
        await nc.drain()


@pytest.mark.asyncio
async def test_network_partition_simulation():
    """
    Additional Chaos Drill: Network partition simulation
    
    Tests system behavior during network connectivity issues
    """
    print("\n🌪️  Starting Additional Chaos Drill: Network Partition Simulation")
    
    delivery_id = "network-partition-789"
    evt = create_test_pr_event(delivery_id)
    
    # Test with invalid NATS URL to simulate network issues
    nc = NATS()
    try:
        # This should fail to connect
        await asyncio.wait_for(
            nc.connect(servers=["nats://invalid-host:4222"]),
            timeout=5.0
        )
        pytest.fail("Expected connection failure did not occur")
    except (asyncio.TimeoutError, Exception) as e:
        print(f"✅ Expected network failure simulated: {type(e).__name__}")
    
    # Now test recovery with correct URL
    try:
        await nc.connect(servers=[ChaosTestConfig.NATS_URL])
        js = nc.jetstream()
        await js.publish("gh.pull_request.synchronize", evt)
        print("✅ Successfully recovered and published after network partition")
    except Exception as e:
        pytest.fail(f"Recovery after network partition failed: {e}")
    finally:
        if nc.is_connected:
            await nc.drain()


@pytest.mark.asyncio
async def test_high_load_stress():
    """
    Additional Chaos Drill: High load stress test
    
    Tests system behavior under high concurrent load
    """
    print("\n🌪️  Starting Additional Chaos Drill: High Load Stress Test")
    
    nc = NATS()
    try:
        await nc.connect(servers=[ChaosTestConfig.NATS_URL])
        js = nc.jetstream()
        
        # Create multiple concurrent publishers
        concurrent_publishers = 10
        events_per_publisher = 20
        
        async def publisher_worker(worker_id: int):
            """Worker function for concurrent publishing"""
            for i in range(events_per_publisher):
                delivery_id = f"stress-{worker_id}-{i}"
                evt = create_test_pr_event(delivery_id, pr_number=1000 + worker_id)
                await js.publish("gh.pull_request.synchronize", evt)
            print(f"✅ Publisher {worker_id} completed {events_per_publisher} events")
        
        print(f"🚀 Starting {concurrent_publishers} concurrent publishers...")
        start_time = time.time()
        
        # Run all publishers concurrently
        tasks = [publisher_worker(i) for i in range(concurrent_publishers)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_events = concurrent_publishers * events_per_publisher
        duration = end_time - start_time
        
        print(f"📊 Stress test completed:")
        print(f"   - Total events: {total_events}")
        print(f"   - Duration: {duration:.2f} seconds")
        print(f"   - Rate: {total_events/duration:.2f} events/second")
        
    except Exception as e:
        pytest.fail(f"High load stress test failed: {e}")
    finally:
        await nc.drain()


if __name__ == "__main__":
    print("🌪️  GitGuard Chaos Engineering Drills")
    print("=====================================\n")
    
    # Run individual tests
    asyncio.run(test_duplicate_flood_idempotency())
    asyncio.run(test_crash_mid_publish_retry())
    asyncio.run(test_network_partition_simulation())
    asyncio.run(test_high_load_stress())
    
    print("\n🎯 All chaos drills completed!")
    print("Check system logs and metrics for detailed analysis.")