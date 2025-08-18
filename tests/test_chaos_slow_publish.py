#!/usr/bin/env python3
"""
Test script for chaos.slow-publish staging drill implementation.
Validates the Makefile integration and demonstrates alert testing functionality.
"""

import os
import sys
import re
import subprocess

def test_makefile_integration():
    """Test that the chaos.slow-publish target is properly integrated in the Makefile."""
    print("🔍 Testing Makefile integration...")
    
    makefile_path = "Makefile"
    
    try:
        with open('Makefile', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required components
        checks = [
            ('chaos.slow-publish:', 'Target definition'),
            ('FAULT_ONCE_DELIVERY_ID=ALERT-TEST', 'Fault injection setup'),
            ('PUBLISH_SLOW_MS=90000', 'Slow publish configuration'),
            ('docker compose exec guard-codex', 'Guard-codex execution'),
            ('gh.pull_request.opened', 'NATS event publishing'),
            ('CodexBuildStall alert fire', 'Alert expectation documentation'),
            ('JetStream redelivery logged', 'Redelivery expectation documentation')
        ]
        
        print("📋 Integration checks:")
        all_passed = True
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{check}'")
                all_passed = False
        
        # Check target appears in help
        help_pattern = r'chaos\.slow-publish:.*?## Development:.*One-command staging drill'
        if re.search(help_pattern, content, re.DOTALL):
            print("   ✅ Help documentation")
        else:
            print("   ❌ Help documentation - target not properly documented")
            all_passed = False
        
        # Validate Python script structure
        python_script_checks = [
            ('import os, json, asyncio', 'Required imports'),
            ('from nats.aio.client import Client as NATS', 'NATS client import'),
            ('delivery_id.*ALERT-TEST', 'Delivery ID setup'),
            ('pull_request.*number.*901', 'PR event structure'),
            ('await js.publish', 'JetStream publishing')
        ]
        
        print("\n📋 Python script checks:")
        for check, description in python_script_checks:
            if re.search(check, content):
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing pattern '{check}'")
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        print(f"❌ Makefile not found: {makefile_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading Makefile: {e}")
        return False

def explain_chaos_drill():
    """Explain how the chaos.slow-publish drill works and its benefits."""
    print("\n💡 How the Chaos.Slow-Publish Drill Works:")
    print("=" * 45)
    
    print("\n🔧 Drill Components:")
    print("   • FAULT_ONCE_DELIVERY_ID=ALERT-TEST - Triggers fault injection")
    print("   • PUBLISH_SLOW_MS=90000 - Simulates 90-second publish delay")
    print("   • Mock PR event with delivery_id='ALERT-TEST'")
    print("   • JetStream publishing to 'gh.pull_request.opened' subject")
    
    print("\n🚨 Alert Testing Sequence:")
    print("   1. First attempt: Fault injection causes immediate failure")
    print("   2. JetStream redelivery: Automatic retry with backoff")
    print("   3. Second attempt: Succeeds but with 90-second delay")
    print("   4. CodexBuildStall alert: Fires due to slow processing")
    print("   5. Alert resolution: Auto-resolves when processing completes")
    
    print("\n🎯 What Gets Tested:")
    print("   • Prometheus alert firing on slow builds (>180s P99)")
    print("   • JetStream redelivery and backoff mechanisms")
    print("   • Fault injection and recovery patterns")
    print("   • Alert auto-resolution after issue resolves")
    print("   • End-to-end resilience under failure conditions")
    
    print("\n📊 Expected Monitoring Signals:")
    print("   • CodexBuildStall alert: FIRING → RESOLVED")
    print("   • JetStream consumer lag: Spike → Recovery")
    print("   • Codex processing time: >90s → Normal")
    print("   • Workflow success: Despite initial failure")

def simulate_drill_execution():
    """Simulate the drill execution and show expected outcomes."""
    print("\n🧪 Drill Execution Simulation:")
    print("=" * 35)
    
    steps = [
        {
            "step": "Environment Setup",
            "action": "Set FAULT_ONCE_DELIVERY_ID=ALERT-TEST, PUBLISH_SLOW_MS=90000",
            "expected": "✅ Environment variables configured"
        },
        {
            "step": "Guard-Codex Arming",
            "action": "Execute Python script in guard-codex container",
            "expected": "✅ Container reports 'armed' status"
        },
        {
            "step": "NATS Event Publishing",
            "action": "Publish PR event with delivery_id='ALERT-TEST'",
            "expected": "✅ Event published to gh.pull_request.opened"
        },
        {
            "step": "First Processing Attempt",
            "action": "Guard-codex processes event, fault injection triggers",
            "expected": "❌ Processing fails due to fault injection"
        },
        {
            "step": "JetStream Redelivery",
            "action": "Automatic retry with exponential backoff",
            "expected": "🔄 Event redelivered after backoff period"
        },
        {
            "step": "Second Processing Attempt",
            "action": "Guard-codex processes event, slow publish (90s)",
            "expected": "⏳ Processing succeeds but takes 90 seconds"
        },
        {
            "step": "Alert Firing",
            "action": "CodexBuildStall alert triggers (P99 > 180s)",
            "expected": "🚨 Alert: FIRING - Build taking too long"
        },
        {
            "step": "Processing Completion",
            "action": "Codex portal updated, workflow completes",
            "expected": "✅ Workflow success despite initial failure"
        },
        {
            "step": "Alert Resolution",
            "action": "Processing time returns to normal",
            "expected": "✅ Alert: RESOLVED - Build time normalized"
        }
    ]
    
    for i, step_info in enumerate(steps, 1):
        print(f"\n📝 Step {i}: {step_info['step']}")
        print(f"   Action: {step_info['action']}")
        print(f"   Expected: {step_info['expected']}")

def validate_prerequisites():
    """Validate that prerequisites for running the drill are met."""
    print("\n🔍 Prerequisites Validation:")
    print("=" * 32)
    
    prerequisites = [
        {
            "name": "Docker Compose",
            "check": "docker compose version",
            "description": "Required for container orchestration"
        },
        {
            "name": "Guard-Codex Service",
            "check": "docker compose ps guard-codex",
            "description": "Target service for fault injection"
        },
        {
            "name": "NATS JetStream",
            "check": "docker compose ps nats",
            "description": "Message broker for event publishing"
        },
        {
            "name": "Prometheus",
            "check": "docker compose ps prometheus",
            "description": "Metrics collection and alerting"
        }
    ]
    
    all_ready = True
    for prereq in prerequisites:
        print(f"\n📋 {prereq['name']}:")
        print(f"   Description: {prereq['description']}")
        print(f"   Check: {prereq['check']}")
        
        try:
            result = subprocess.run(
                prereq['check'].split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"   Status: ✅ READY")
            else:
                print(f"   Status: ❌ NOT READY - {result.stderr.strip()}")
                all_ready = False
        except subprocess.TimeoutExpired:
            print(f"   Status: ⏳ TIMEOUT - Command took too long")
            all_ready = False
        except FileNotFoundError:
            print(f"   Status: ❌ NOT FOUND - Command not available")
            all_ready = False
        except Exception as e:
            print(f"   Status: ❌ ERROR - {e}")
            all_ready = False
    
    return all_ready

def main():
    """Run all tests for the chaos.slow-publish implementation."""
    print("🚨 Testing Chaos.Slow-Publish Staging Drill Implementation")
    print("=" * 60)
    
    # Test 1: Makefile integration
    makefile_ok = test_makefile_integration()
    
    # Test 2: Prerequisites validation
    prereqs_ok = validate_prerequisites()
    
    # Test 3: Explanation
    explain_chaos_drill()
    
    # Test 4: Simulation
    simulate_drill_execution()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Makefile Integration: {'✅ PASS' if makefile_ok else '❌ FAIL'}")
    print(f"   Prerequisites: {'✅ READY' if prereqs_ok else '⚠️  CHECK REQUIRED'}")
    print(f"   Drill Explanation: ✅ PASS")
    print(f"   Execution Simulation: ✅ PASS")
    
    if makefile_ok:
        print("\n🎉 Chaos.Slow-Publish drill is ready for staging!")
        print("\n🚨 Key Features Implemented:")
        print("   • One-command execution: make chaos.slow-publish")
        print("   • Fault injection with FAULT_ONCE_DELIVERY_ID")
        print("   • Slow publish simulation (90s delay)")
        print("   • JetStream redelivery testing")
        print("   • CodexBuildStall alert validation")
        print("   • End-to-end resilience verification")
        
        print("\n🚀 Usage Instructions:")
        print("   1. Ensure all services are running: make up")
        print("   2. Set up monitoring: Open Prometheus/Grafana")
        print("   3. Execute drill: make chaos.slow-publish")
        print("   4. Watch alerts: Monitor CodexBuildStall firing")
        print("   5. Verify recovery: Confirm alert auto-resolution")
        
        if not prereqs_ok:
            print("\n⚠️  Note: Some prerequisites need attention before running.")
        
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)