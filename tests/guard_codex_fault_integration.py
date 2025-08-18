#!/usr/bin/env python3
"""
Guard-Codex Fault Injection Integration Example

This file demonstrates how to integrate fault injection into the guard-codex service
for chaos engineering testing. This is an example of how the actual service code
would be modified to support fault injection.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from fault_injection import with_fault_injection, FaultInjectionError


logger = logging.getLogger(__name__)


class GuardCodexService:
    """
    Example Guard-Codex service with fault injection capabilities
    
    This demonstrates how the actual guard-codex service would integrate
    fault injection for chaos engineering tests.
    """
    
    def __init__(self, nats_client=None):
        self.nats_client = nats_client
        self.processed_events = set()
    
    @with_fault_injection
    async def publish_portal(self, delivery_id: str, event_data: Dict[str, Any]) -> None:
        """
        Publish event to portal with fault injection support
        
        This method will raise FaultInjectionError if:
        - FAULT_ONCE_DELIVERY_ID environment variable matches delivery_id
        - This is the first time processing this delivery_id
        
        Args:
            delivery_id: Unique identifier for the event
            event_data: The event payload to publish
        """
        logger.info(f"Processing publish_portal for delivery_id: {delivery_id}")
        
        # Check for idempotency (duplicate detection)
        if delivery_id in self.processed_events:
            logger.info(f"🔄 Duplicate event detected for delivery_id: {delivery_id}, skipping")
            return
        
        try:
            # Simulate actual publishing logic
            await self._publish_to_jetstream(event_data)
            
            # Mark as processed for idempotency
            self.processed_events.add(delivery_id)
            
            logger.info(f"✅ Successfully published event for delivery_id: {delivery_id}")
            
        except FaultInjectionError:
            # Re-raise fault injection errors for chaos testing
            logger.error(f"💥 Fault injection triggered for delivery_id: {delivery_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to publish event for delivery_id: {delivery_id}: {e}")
            raise
    
    async def _publish_to_jetstream(self, event_data: Dict[str, Any]) -> None:
        """
        Internal method to publish to NATS JetStream
        
        In the real implementation, this would use the actual NATS client
        """
        if self.nats_client:
            # Real implementation would publish to JetStream
            js = self.nats_client.jetstream()
            await js.publish("portal.events", json.dumps(event_data).encode())
        else:
            # Simulate publishing for testing
            logger.debug(f"Simulating JetStream publish: {json.dumps(event_data, indent=2)}")
    
    async def handle_github_webhook(self, delivery_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Handle incoming GitHub webhook with fault injection support
        
        This is the main entry point that would be called by the webhook handler
        """
        logger.info(f"Handling GitHub webhook: {event_type} (delivery_id: {delivery_id})")
        
        try:
            # Process the event through the portal
            await self.publish_portal(delivery_id, {
                "event_type": event_type,
                "delivery_id": delivery_id,
                "payload": payload,
                "timestamp": "2024-01-01T00:00:00Z"  # In real implementation, use actual timestamp
            })
            
        except FaultInjectionError as e:
            # Log fault injection for monitoring
            logger.warning(f"🔥 Chaos engineering fault injected: {e}")
            # In real implementation, this might trigger retry mechanisms
            raise
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            raise
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about event processing"""
        return {
            "total_processed_events": len(self.processed_events),
            "processed_delivery_ids": list(self.processed_events)
        }


class ChaosTestRunner:
    """
    Test runner for chaos engineering scenarios
    """
    
    def __init__(self, service: GuardCodexService):
        self.service = service
    
    async def run_duplicate_flood_test(self, base_delivery_id: str, count: int = 50) -> Dict[str, Any]:
        """
        Run duplicate flood test
        
        Args:
            base_delivery_id: Base delivery ID for the test
            count: Number of duplicate events to send
            
        Returns:
            Test results dictionary
        """
        logger.info(f"🌪️  Starting duplicate flood test with {count} events")
        
        successful_publishes = 0
        duplicate_skips = 0
        errors = 0
        
        test_payload = {
            "event": "pull_request",
            "action": "synchronize",
            "pull_request": {"number": 888},
            "repository": {"full_name": "org/repo"}
        }
        
        for i in range(count):
            try:
                await self.service.handle_github_webhook(
                    delivery_id=base_delivery_id,
                    event_type="pull_request",
                    payload=test_payload
                )
                if i == 0:
                    successful_publishes += 1
                else:
                    duplicate_skips += 1
            except Exception as e:
                errors += 1
                logger.error(f"Error in duplicate flood test iteration {i}: {e}")
        
        results = {
            "test_type": "duplicate_flood",
            "total_events": count,
            "successful_publishes": successful_publishes,
            "duplicate_skips": duplicate_skips,
            "errors": errors,
            "expected_publishes": 1,
            "expected_duplicates": count - 1,
            "test_passed": successful_publishes == 1 and duplicate_skips == (count - 1)
        }
        
        logger.info(f"📊 Duplicate flood test results: {results}")
        return results
    
    async def run_fault_injection_test(self, delivery_id: str) -> Dict[str, Any]:
        """
        Run fault injection test
        
        Args:
            delivery_id: Delivery ID to inject fault for
            
        Returns:
            Test results dictionary
        """
        logger.info(f"🌪️  Starting fault injection test for delivery_id: {delivery_id}")
        
        # Reset fault injector and set up fault injection
        from fault_injection import reset_fault_injector
        reset_fault_injector()
        os.environ["FAULT_ONCE_DELIVERY_ID"] = delivery_id
        
        # Create a fresh service instance for this test to avoid processed events cache
        test_service = GuardCodexService()
        
        test_payload = {
            "event": "pull_request",
            "action": "opened",
            "pull_request": {"number": 999},
            "repository": {"full_name": "org/repo"}
        }
        
        first_attempt_failed = False
        second_attempt_succeeded = False
        
        # First attempt - should fail
        try:
            await test_service.handle_github_webhook(
                delivery_id=delivery_id,
                event_type="pull_request",
                payload=test_payload
            )
            logger.warning("First attempt did not fail as expected")
        except FaultInjectionError:
            first_attempt_failed = True
            logger.info("✅ First attempt failed as expected (fault injection)")
        except Exception as e:
            logger.error(f"Unexpected error on first attempt: {e}")
        
        # Second attempt - should succeed
        try:
            await test_service.handle_github_webhook(
                delivery_id=delivery_id,
                event_type="pull_request",
                payload=test_payload
            )
            second_attempt_succeeded = True
            logger.info("✅ Second attempt succeeded as expected")
        except Exception as e:
            logger.error(f"Second attempt failed unexpectedly: {e}")
        
        results = {
            "test_type": "fault_injection",
            "delivery_id": delivery_id,
            "first_attempt_failed": first_attempt_failed,
            "second_attempt_succeeded": second_attempt_succeeded,
            "test_passed": first_attempt_failed and second_attempt_succeeded
        }
        
        logger.info(f"📊 Fault injection test results: {results}")
        return results


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("🧪 Guard-Codex Fault Injection Integration Test")
        print("===============================================\n")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Create service instance
        service = GuardCodexService()
        test_runner = ChaosTestRunner(service)
        
        # Run duplicate flood test
        print("\n🌪️  Running Duplicate Flood Test...")
        duplicate_results = await test_runner.run_duplicate_flood_test("dup-test-123", count=10)
        
        # Run fault injection test
        print("\n🌪️  Running Fault Injection Test...")
        fault_results = await test_runner.run_fault_injection_test("fault-test-456")
        
        # Print summary
        print("\n📋 Test Summary")
        print("===============")
        print(f"Duplicate Flood Test: {'✅ PASSED' if duplicate_results['test_passed'] else '❌ FAILED'}")
        print(f"Fault Injection Test: {'✅ PASSED' if fault_results['test_passed'] else '❌ FAILED'}")
        
        # Print service stats
        stats = service.get_processing_stats()
        print(f"\n📊 Service Stats: {stats}")
    
    asyncio.run(main())