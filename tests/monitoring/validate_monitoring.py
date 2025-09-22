#!/usr/bin/env python3
"""
MRPC Monitoring Test Suite - Validates all monitoring tools
"""

import subprocess
import sys
from datetime import datetime


def run_test(test_name, command, timeout=30):
    """Run a test command and return results"""
    print(f"\nTesting: {test_name}")
    print("-" * 50)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/Users/philipcalderwood/Code/MRPC",
        )

        if result.returncode == 0:
            print(" PASSED")
            if result.stdout:
                # Show first few lines of output
                lines = result.stdout.split("\n")[:5]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("⏱️ TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False


def test_monitoring_suite():
    """Test all monitoring components"""
    print("🔍 MRPC Monitoring Suite Validation")
    print("=" * 60)
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Service Health Check", ["python", "tests/monitoring/test_service_health.py"]),
        ("System Resource Monitor", ["python", "tests/monitoring/monitor_system.py"]),
        ("Memory Summary", ["python", "tests/monitoring/memory_summary.py"]),
        (
            "Systemd Deployment Test",
            ["python", "tests/deployment/test_systemd_deployment.py"],
        ),
    ]

    passed = 0
    failed = 0

    for test_name, command in tests:
        if run_test(test_name, command):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All monitoring tools are working correctly!")
        print("\n📋 Available Monitoring Commands:")
        print("  • Quick health:     python tests/monitoring/test_service_health.py")
        print("  • Full monitor:     python tests/monitoring/monitor_system.py")
        print("  • Memory summary:   python tests/monitoring/memory_summary.py")
        print(
            "  • Deployment test:  python tests/deployment/test_systemd_deployment.py"
        )
        print(
            "  • Setup monitoring: python tests/monitoring/setup_systemd_monitoring.py"
        )
        print("\n🔧 Remote Monitoring:")
        print("  • View logs:        ssh data-explorer 'tail -f ~/mrpc-memory.log'")
        print(
            "  • Check alerts:     ssh data-explorer 'grep WARNING ~/mrpc-memory.log'"
        )
        print(
            "  • Timer status:     ssh data-explorer 'sudo systemctl status mrpc-memory-monitor.timer'"
        )
        return True
    else:
        print("⚠️ Some monitoring tools failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = test_monitoring_suite()
    sys.exit(0 if success else 1)
