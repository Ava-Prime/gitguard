#!/usr/bin/env python3
"""
Test script to validate Prometheus alerts in staging by deliberately slowing publish_portal

This script temporarily modifies the publish_portal activity to add delays,
triggering the CodexBuildStall alert when P95 latency exceeds 60 seconds.
"""

import os
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict

# Add the apps directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "guard-codex"))

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def check_prometheus_connection():
    """Check if Prometheus is accessible"""
    try:
        response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is accessible at http://localhost:9090")
            return True
        else:
            print(f"❌ Prometheus returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Prometheus: {e}")
        return False

def check_codex_metrics():
    """Check if codex metrics are being collected"""
    try:
        # Check if codex activity metrics exist
        response = requests.get(
            "http://localhost:9090/api/v1/query?query=codex_activity_seconds_bucket",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('result'):
                print("✅ Codex activity metrics are being collected")
                return True
            else:
                print("⚠️  Codex activity metrics not found (service may not be running)")
                return False
        else:
            print(f"❌ Failed to query metrics: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot query Prometheus metrics: {e}")
        return False

def check_alert_rules():
    """Check if CodexBuildStall alert rule is loaded"""
    try:
        response = requests.get("http://localhost:9090/api/v1/rules", timeout=5)
        if response.status_code == 200:
            data = response.json()
            for group in data.get('data', {}).get('groups', []):
                if group.get('name') == 'codex':
                    for rule in group.get('rules', []):
                        if rule.get('name') == 'CodexBuildStall':
                            print("✅ CodexBuildStall alert rule is loaded")
                            print(f"   State: {rule.get('state', 'unknown')}")
                            print(f"   Query: {rule.get('query', 'unknown')}")
                            return True
            print("❌ CodexBuildStall alert rule not found")
            return False
        else:
            print(f"❌ Failed to get alert rules: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot get alert rules: {e}")
        return False

def monitor_alert_status(duration_minutes=15):
    """Monitor alert status for a specified duration"""
    print(f"\n🔍 Monitoring CodexBuildStall alert for {duration_minutes} minutes...")
    print("   (Alert should fire if P95 publish_portal latency > 60s for 10+ minutes)")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    alert_fired = False
    
    while time.time() < end_time:
        try:
            # Check current alert status
            response = requests.get("http://localhost:9090/api/v1/alerts", timeout=5)
            if response.status_code == 200:
                data = response.json()
                codex_alerts = [
                    alert for alert in data.get('data', [])
                    if alert.get('labels', {}).get('alertname', '').startswith('Codex')
                ]
                
                if codex_alerts:
                    for alert in codex_alerts:
                        alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                        state = alert.get('state', 'unknown')
                        print(f"🚨 Alert: {alert_name} - State: {state}")
                        if alert_name == 'CodexBuildStall' and state == 'firing':
                            alert_fired = True
                            print("✅ CodexBuildStall alert is FIRING! Test successful.")
                            return True
                else:
                    # Check current P95 latency
                    latency_response = requests.get(
                        "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(codex_activity_seconds_bucket{name=\"publish_portal\"}[5m])) by (le))",
                        timeout=5
                    )
                    if latency_response.status_code == 200:
                        latency_data = latency_response.json()
                        result = latency_data.get('data', {}).get('result', [])
                        if result:
                            p95_latency = float(result[0].get('value', [0, '0'])[1])
                            print(f"📊 Current P95 publish_portal latency: {p95_latency:.2f}s (threshold: 60s)")
                        else:
                            print("📊 No publish_portal metrics available yet")
            
            time.sleep(30)  # Check every 30 seconds
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Error checking alerts: {e}")
            time.sleep(30)
    
    if not alert_fired:
        print("⚠️  CodexBuildStall alert did not fire during monitoring period")
        print("   This could mean:")
        print("   - publish_portal is not being called frequently enough")
        print("   - Latency is not exceeding 60s threshold")
        print("   - Alert evaluation period (10m) hasn't been reached")
    
    return alert_fired

def create_slow_publish_portal_patch():
    """Create a patch file to slow down publish_portal for testing"""
    activities_file = Path("apps/guard-codex/activities.py")
    if not activities_file.exists():
        print(f"❌ Activities file not found: {activities_file}")
        return False
    
    # Read the original file
    with open(activities_file, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file = activities_file.with_suffix('.py.backup')
    with open(backup_file, 'w') as f:
        f.write(content)
    
    # Add delay to publish_portal function
    if 'async def publish_portal(' in content:
        # Find the function and add a delay
        lines = content.split('\n')
        new_lines = []
        in_publish_portal = False
        delay_added = False
        
        for line in lines:
            new_lines.append(line)
            if 'async def publish_portal(' in line:
                in_publish_portal = True
            elif in_publish_portal and not delay_added and line.strip() and not line.startswith(' ' * 4 + '#'):
                # Add delay after the function signature and docstring
                if not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                    new_lines.insert(-1, '    # TESTING: Add delay to trigger Prometheus alert')
                    new_lines.insert(-1, '    import time')
                    new_lines.insert(-1, '    time.sleep(65)  # Sleep for 65 seconds to exceed 60s threshold')
                    delay_added = True
                    in_publish_portal = False
        
        if delay_added:
            # Write the modified content
            with open(activities_file, 'w') as f:
                f.write('\n'.join(new_lines))
            print(f"✅ Added 65-second delay to publish_portal function")
            print(f"📁 Backup saved as: {backup_file}")
            return True
        else:
            print("❌ Could not find suitable location to add delay")
            return False
    else:
        print("❌ publish_portal function not found in activities.py")
        return False

def restore_original_activities():
    """Restore the original activities.py from backup"""
    activities_file = Path("apps/guard-codex/activities.py")
    backup_file = activities_file.with_suffix('.py.backup')
    
    if backup_file.exists():
        with open(backup_file, 'r') as f:
            content = f.read()
        with open(activities_file, 'w') as f:
            content.write(content)
        backup_file.unlink()  # Remove backup
        print("✅ Restored original activities.py")
        return True
    else:
        print("❌ Backup file not found")
        return False

def main():
    """Main test function"""
    print("🧪 GitGuard Prometheus Alert Testing")
    print("====================================\n")
    
    # Step 1: Check Prometheus connection
    print("1. Checking Prometheus connection...")
    if not check_prometheus_connection():
        print("\n❌ Cannot proceed without Prometheus. Please ensure GitGuard services are running.")
        print("   Run: docker compose -f ops/compose.yml up -d")
        return 1
    
    # Step 2: Check if codex metrics are available
    print("\n2. Checking codex metrics...")
    if not check_codex_metrics():
        print("\n⚠️  Codex metrics not available. Service may not be running or processing events.")
        print("   This test will still check alert rules but may not trigger alerts.")
    
    # Step 3: Check alert rules
    print("\n3. Checking alert rules...")
    if not check_alert_rules():
        print("\n❌ Alert rules not loaded. Please reload Prometheus configuration.")
        print("   Run: scripts/reload_prometheus.ps1 (Windows) or scripts/reload_prometheus.sh (Linux)")
        return 1
    
    # Step 4: Ask user if they want to proceed with the destructive test
    print("\n4. Alert Testing Options:")
    print("   a) Monitor existing alerts (non-destructive)")
    print("   b) Temporarily modify publish_portal to trigger alerts (destructive)")
    
    choice = input("\nChoose option (a/b): ").lower().strip()
    
    if choice == 'b':
        print("\n⚠️  WARNING: This will temporarily modify activities.py")
        confirm = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("Test cancelled.")
            return 0
        
        # Create the patch
        if create_slow_publish_portal_patch():
            print("\n🔄 Please restart the guard-codex service to apply changes:")
            print("   docker compose -f ops/compose.yml restart guard-codex")
            input("\nPress Enter after restarting the service...")
            
            try:
                # Monitor for alerts
                success = monitor_alert_status(15)
                return 0 if success else 1
            finally:
                # Always restore the original file
                print("\n🔄 Restoring original activities.py...")
                restore_original_activities()
                print("   Please restart guard-codex service again to restore normal operation.")
        else:
            return 1
    
    elif choice == 'a':
        # Just monitor existing alerts
        return 0 if monitor_alert_status(5) else 1
    
    else:
        print("Invalid choice. Exiting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())