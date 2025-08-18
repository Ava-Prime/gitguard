#!/usr/bin/env python3
"""
Test script for docs freshness SLO implementation.
Validates the alert rule configuration and integration.
"""

import os
import sys

def test_activities_integration():
    """Test that the DOC_FRESH metric is properly integrated in activities.py."""
    print("🔍 Testing activities.py integration...")
    
    activities_file = "apps/guard-codex/activities.py"
    
    try:
        with open(activities_file, 'r') as f:
            content = f.read()
        
        # Check for required components
        checks = [
            ('from prometheus_client import Histogram', 'Prometheus client import'),
            ('DOC_FRESH = Histogram("codex_docs_freshness_seconds"', 'DOC_FRESH metric definition'),
            ('buckets=(1,3,5,10,30,60,180,300,600)', 'Custom buckets configuration'),
            ('start = time.time()', 'Timer start'),
            ('DOC_FRESH.observe(time.time() - start)', 'Latency observation')
        ]
        
        print("📋 Integration checks:")
        all_passed = True
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - missing '{check}'")
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        print(f"❌ Activities file not found: {activities_file}")
        return False
    except Exception as e:
        print(f"❌ Error reading activities file: {e}")
        return False

def test_alert_rule_syntax():
    """Test the alert rule syntax by reading the file."""
    print("\n🚨 Testing alert rule configuration...")
    
    alert_file = "ops/prometheus/alerts_codex.yml"
    
    try:
        with open(alert_file, 'r') as f:
            content = f.read()
        
        # Check for the alert rule
        if 'CodexFreshnessSLOBreached' in content:
            print("✅ Alert rule 'CodexFreshnessSLOBreached' found")
            
            # Extract the alert rule section
            lines = content.split('\n')
            alert_section = []
            in_alert = False
            
            for line in lines:
                if 'CodexFreshnessSLOBreached' in line:
                    in_alert = True
                if in_alert:
                    alert_section.append(line)
                    if line.strip() and not line.startswith(' ') and 'CodexFreshnessSLOBreached' not in line and line.strip().startswith('- alert:'):
                        break
                    elif line.strip() and not line.startswith(' ') and not line.startswith('#') and 'CodexFreshnessSLOBreached' not in line and not line.strip().startswith('- alert:'):
                        break
            
            print("📋 Alert rule configuration:")
            for line in alert_section:
                if line.strip():  # Only show non-empty lines
                    print(f"   {line}")
            
            # Validate key components
            alert_text = '\n'.join(alert_section)
            checks = [
                ('histogram_quantile(0.99', 'P99 quantile calculation'),
                ('codex_docs_freshness_seconds_bucket', 'Correct metric name'),
                ('> 180', 'Threshold of 180 seconds'),
                ('for: 15m', '15-minute duration'),
                ('severity: page', 'Page severity level'),
                ('summary: "Docs freshness P99 > 180s"', 'Alert summary')
            ]
            
            print("\n🔍 Validation checks:")
            all_passed = True
            for check, description in checks:
                if check in alert_text:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description} - missing '{check}'")
                    all_passed = False
            
            return all_passed
        else:
            print("❌ Alert rule 'CodexFreshnessSLOBreached' not found")
            return False
            
    except FileNotFoundError:
        print(f"❌ Alert file not found: {alert_file}")
        return False
    except Exception as e:
        print(f"❌ Error reading alert file: {e}")
        return False

def explain_slo_implementation():
    """Explain how the SLO implementation works."""
    print("\n💡 How the Docs Freshness SLO Works:")
    print("=" * 45)
    
    print("\n📊 Metric Collection:")
    print("   • DOC_FRESH histogram tracks event-to-doc write latency")
    print("   • Custom buckets: 1s, 3s, 5s, 10s, 30s, 60s, 180s, 300s, 600s")
    print("   • Timer starts at render_docs() entry")
    print("   • Observation recorded before function return")
    
    print("\n🚨 Alert Logic:")
    print("   • Monitors P99 latency over 15-minute windows")
    print("   • Triggers if P99 > 180 seconds for 15+ minutes")
    print("   • Page-level severity for immediate attention")
    print("   • Indicates docs generation performance issues")
    
    print("\n🎯 SLO Target:")
    print("   • 99% of docs should be generated within 180 seconds")
    print("   • Ensures timely PR documentation updates")
    print("   • Maintains developer experience quality")
    
    print("\n🔧 Operational Benefits:")
    print("   • Proactive detection of performance degradation")
    print("   • Quantified measurement of docs freshness")
    print("   • Integration with existing Prometheus alerting")
    print("   • Historical trend analysis capability")

def main():
    """Run all tests for the docs freshness SLO implementation."""
    print("🎯 Testing Docs Freshness SLO Implementation")
    print("=" * 50)
    
    # Test 1: Activities integration
    activities_ok = test_activities_integration()
    
    # Test 2: Alert rule
    alert_ok = test_alert_rule_syntax()
    
    # Test 3: Explanation
    explain_slo_implementation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Activities Integration: {'✅ PASS' if activities_ok else '❌ FAIL'}")
    print(f"   Alert Rule Config: {'✅ PASS' if alert_ok else '❌ FAIL'}")
    
    if activities_ok and alert_ok:
        print("\n🎉 All tests passed! Docs freshness SLO is ready for production.")
        print("\n📊 Key Features Implemented:")
        print("   • Prometheus histogram metric with custom buckets")
        print("   • Event-to-doc write latency tracking in render_docs()")
        print("   • P99 SLO breach detection (>180s threshold)")
        print("   • Page-level alerting for critical delays")
        print("   • Integration with existing Prometheus setup")
        print("   • CodexFreshnessSLOBreached alert rule")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)