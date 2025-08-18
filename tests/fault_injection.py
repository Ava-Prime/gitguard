#!/usr/bin/env python3
"""
Fault Injection Module for Chaos Engineering

This module provides fault injection capabilities for testing system resilience.
It can be integrated into the guard-codex service to simulate failures.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps


logger = logging.getLogger(__name__)


class FaultInjector:
    """Fault injection manager for chaos engineering tests"""
    
    def __init__(self):
        self.faulted_delivery_ids: Dict[str, bool] = {}
        
    @property
    def fault_once_delivery_id(self) -> Optional[str]:
        """Get the current fault delivery ID from environment (dynamic check)"""
        return os.getenv("FAULT_ONCE_DELIVERY_ID")
        
    def should_inject_fault(self, delivery_id: str) -> bool:
        """
        Determine if a fault should be injected for the given delivery_id
        
        Args:
            delivery_id: The delivery ID to check
            
        Returns:
            True if fault should be injected, False otherwise
        """
        fault_target = self.fault_once_delivery_id
        if not fault_target:
            return False
            
        if delivery_id != fault_target:
            return False
            
        # Only fault once per delivery_id
        if delivery_id in self.faulted_delivery_ids:
            logger.info(f"Fault already injected for delivery_id: {delivery_id}, allowing through")
            return False
            
        # Mark as faulted and inject fault
        self.faulted_delivery_ids[delivery_id] = True
        logger.warning(f"🔥 FAULT INJECTION: Simulating failure for delivery_id: {delivery_id}")
        return True


# Global fault injector instance
_fault_injector = FaultInjector()


def with_fault_injection(func):
    """
    Decorator to add fault injection capability to functions
    
    Usage:
        @with_fault_injection
        async def publish_portal(delivery_id: str, event_data: dict):
            # Your publish logic here
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract delivery_id from args or kwargs
        delivery_id = None
        
        # Try to find delivery_id in kwargs first
        if 'delivery_id' in kwargs:
            delivery_id = kwargs['delivery_id']
        # Try to find it in the event data if passed as dict
        elif len(args) > 1 and isinstance(args[1], dict) and 'delivery_id' in args[1]:
            delivery_id = args[1]['delivery_id']
        # Try to extract from first string argument (common pattern)
        elif len(args) > 1 and isinstance(args[1], str):
            delivery_id = args[1]
        # For methods, skip 'self' and check second argument
        elif len(args) > 1:
            delivery_id = args[1] if isinstance(args[1], str) else None
            
        logger.debug(f"Fault injection check: delivery_id={delivery_id}, args={len(args)}, kwargs={list(kwargs.keys())}")
            
        if delivery_id and _fault_injector.should_inject_fault(delivery_id):
            raise FaultInjectionError(f"Simulated failure for delivery_id: {delivery_id}")
            
        return await func(*args, **kwargs)
    return wrapper


class FaultInjectionError(Exception):
    """Exception raised when fault injection is triggered"""
    pass


def inject_publish_fault(delivery_id: str) -> None:
    """
    Manually inject a fault for a specific delivery_id
    
    Args:
        delivery_id: The delivery ID to inject fault for
    """
    if _fault_injector.should_inject_fault(delivery_id):
        raise FaultInjectionError(f"Manual fault injection for delivery_id: {delivery_id}")


def reset_fault_injector() -> None:
    """Reset the fault injector state (useful for testing)"""
    global _fault_injector
    _fault_injector = FaultInjector()


def get_fault_stats() -> Dict[str, Any]:
    """Get statistics about fault injection"""
    return {
        "fault_once_delivery_id": _fault_injector.fault_once_delivery_id,
        "faulted_delivery_ids": list(_fault_injector.faulted_delivery_ids.keys()),
        "total_faults_injected": len(_fault_injector.faulted_delivery_ids)
    }


# Example integration code for guard-codex service
class ExampleGuardCodexIntegration:
    """
    Example of how to integrate fault injection into guard-codex service
    
    This shows how the actual guard-codex service could use fault injection
    """
    
    @with_fault_injection
    async def publish_portal(self, delivery_id: str, event_data: dict) -> None:
        """
        Example publish_portal method with fault injection
        
        In the real implementation, this would be in the guard-codex service
        """
        logger.info(f"Publishing event for delivery_id: {delivery_id}")
        
        # Simulate actual publish logic
        # In real implementation, this would publish to NATS JetStream
        await self._actual_publish_logic(event_data)
        
        logger.info(f"Successfully published event for delivery_id: {delivery_id}")
    
    async def _actual_publish_logic(self, event_data: dict) -> None:
        """Simulate actual publish logic"""
        # This would contain the real NATS publishing code
        pass


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    
    async def test_fault_injection():
        print("🧪 Testing Fault Injection Module")
        print("=================================\n")
        
        # Set up fault injection for specific delivery_id
        os.environ["FAULT_ONCE_DELIVERY_ID"] = "test-fault-123"
        reset_fault_injector()
        
        example_service = ExampleGuardCodexIntegration()
        
        # Test 1: First call should fail
        try:
            await example_service.publish_portal("test-fault-123", {"test": "data"})
            print("❌ Expected fault injection did not occur")
        except FaultInjectionError as e:
            print(f"✅ Fault injection worked: {e}")
        
        # Test 2: Second call should succeed
        try:
            await example_service.publish_portal("test-fault-123", {"test": "data"})
            print("✅ Second call succeeded (fault only injected once)")
        except FaultInjectionError as e:
            print(f"❌ Unexpected fault on second call: {e}")
        
        # Test 3: Different delivery_id should not fault
        try:
            await example_service.publish_portal("different-id", {"test": "data"})
            print("✅ Different delivery_id succeeded (no fault)")
        except FaultInjectionError as e:
            print(f"❌ Unexpected fault for different delivery_id: {e}")
        
        # Print stats
        stats = get_fault_stats()
        print(f"\n📊 Fault Injection Stats: {stats}")
    
    asyncio.run(test_fault_injection())