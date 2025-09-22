#!/usr/bin/env python3
"""
MRPC Memory Monitoring Summary and Quick Commands
"""

import subprocess
from datetime import datetime


def show_current_status():
    """Show current memory and service status"""
    print("Current MRPC Status")
    print("=" * 40)

    # Service status
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "sudo systemctl is-active mrpc"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            status = result.stdout.strip()
            if status == "active":
                print(" Service: Running")
            else:
                print(f"⚠️ Service: {status}")
        else:
            print("❌ Service: Error checking status")
    except Exception:
        print("❌ Service: Cannot connect")

    # Memory status
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "free -m | grep '^Mem:'"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            parts = result.stdout.split()
            if len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                used_percent = (used / total) * 100
                print(f"💾 System Memory: {used}MB/{total}MB ({used_percent:.1f}%)")
    except Exception:
        print("❌ Memory: Cannot get status")

    # MRPC memory
    try:
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                "sudo systemctl status mrpc --no-pager | grep Memory",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout:
            print(f"🎯 MRPC Service: {result.stdout.strip()}")
    except Exception:
        pass


def show_monitoring_status():
    """Show monitoring timer status"""
    print("\n⏰ Monitoring Status")
    print("=" * 40)

    try:
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                "sudo systemctl is-active mrpc-memory-monitor.timer",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            status = result.stdout.strip()
            if status == "active":
                print(" Memory Monitoring: Active (every 5 minutes)")
            else:
                print(f"⚠️ Memory Monitoring: {status}")
        else:
            print("❌ Memory Monitoring: Not configured")
    except Exception:
        print("❌ Memory Monitoring: Cannot check status")

    # Show next run time
    try:
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                "sudo systemctl status mrpc-memory-monitor.timer --no-pager | grep Trigger",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout:
            print(f"🕐 Next Run: {result.stdout.strip()}")
    except Exception:
        pass


def show_recent_logs():
    """Show recent monitoring logs"""
    print("\n📋 Recent Memory Logs (Last 5 entries)")
    print("=" * 50)

    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "tail -5 ~/mrpc-memory.log"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"  {line}")
        else:
            print("  No logs found - monitoring may be starting up")
    except Exception:
        print("  Cannot access logs")


def show_quick_commands():
    """Show quick reference commands"""
    print("\n📋 Quick Commands")
    print("=" * 40)
    print("Health Check:")
    print("  python tests/monitoring/test_service_health.py")
    print("\nFull Monitor:")
    print("  python tests/monitoring/monitor_system.py")
    print("\nContinuous (5min for 1hour):")
    print("  python tests/monitoring/monitor_system.py continuous 300 3600")
    print("\nView Live Logs:")
    print("  ssh data-explorer 'tail -f ~/mrpc-memory.log'")
    print("\nMemory Alerts:")
    print("  ssh data-explorer 'grep WARNING ~/mrpc-memory.log'")
    print("\nService Management:")
    print("  ssh data-explorer 'sudo systemctl status mrpc'")
    print("  ssh data-explorer 'sudo systemctl restart mrpc'")


def main():
    """Main monitoring summary"""
    print("🔍 MRPC Memory Monitoring Summary")
    print("=" * 50)
    print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    show_current_status()
    show_monitoring_status()
    show_recent_logs()
    show_quick_commands()

    print("\n💡 Monitoring Tips:")
    print("  • Normal MRPC memory usage: 250-400MB")
    print("  • System memory alert threshold: 85%")
    print("  • Logs are kept in ~/mrpc-memory.log")
    print("  • Monitoring runs automatically every 5 minutes")


if __name__ == "__main__":
    main()
