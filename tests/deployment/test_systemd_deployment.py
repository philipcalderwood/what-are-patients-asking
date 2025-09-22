#!/usr/bin/env python3
"""
Test script to verify MRPC systemd service deployment
"""

import subprocess
import sys
from datetime import datetime


def run_ssh_command(command, timeout=30):
    """Run a command via SSH and return the result"""
    ssh_command = ["ssh", "data-explorer", command]
    try:
        result = subprocess.run(
            ssh_command, capture_output=True, text=True, timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": 124,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }
    except Exception as e:
        return {"returncode": 1, "stdout": "", "stderr": str(e)}


def test_ssh_connectivity():
    """Test if SSH connection to data-explorer works"""
    print("=== Testing SSH Connectivity ===")

    result = run_ssh_command("echo 'SSH connection successful'", timeout=10)

    if result["returncode"] == 0:
        print("✓ SSH connection working")
        return True
    else:
        print(f"✗ SSH connection failed: {result['stderr']}")
        return False


def test_systemd_service_exists():
    """Test if MRPC systemd service is configured"""
    print("\n=== Testing Systemd Service Configuration ===")

    # Check if service file exists
    result = run_ssh_command(
        "test -f /etc/systemd/system/mrpc.service && echo 'exists' || echo 'missing'"
    )

    if result["returncode"] == 0 and "exists" in result["stdout"]:
        print("✓ Systemd service file exists")
        return True
    else:
        print("✗ Systemd service file not found")
        return False


def test_systemd_service_status():
    """Test systemd service status and health"""
    print("\n=== Testing Systemd Service Status ===")

    # Get service status
    result = run_ssh_command("sudo systemctl is-active mrpc")

    if result["returncode"] == 0:
        status = result["stdout"]
        print(f"✓ Service status: {status}")

        if status == "active":
            print("✓ Service is running")
            return True
        else:
            print(f"✗ Service is not active (status: {status})")
            return False
    else:
        print(f"✗ Failed to get service status: {result['stderr']}")
        return False


def test_systemd_service_details():
    """Get detailed service information"""
    print("\n=== Testing Systemd Service Details ===")

    # Get detailed status
    result = run_ssh_command("sudo systemctl status mrpc --no-pager -l")

    if result["returncode"] == 0:
        print("✓ Service status retrieved successfully")

        # Parse key information
        lines = result["stdout"].split("\n")
        for line in lines:
            if "Active:" in line:
                print(f"  {line.strip()}")
            elif "Main PID:" in line:
                print(f"  {line.strip()}")
            elif "Memory:" in line:
                print(f"  {line.strip()}")
            elif "Tasks:" in line:
                print(f"  {line.strip()}")

        return True
    else:
        print(f"✗ Failed to get service details: {result['stderr']}")
        return False


def test_application_process():
    """Test if gunicorn processes are running"""
    print("\n=== Testing Application Processes ===")

    # Check for gunicorn processes
    result = run_ssh_command("pgrep -f 'gunicorn.*app:server' | wc -l")

    if result["returncode"] == 0:
        process_count = int(result["stdout"])
        print(f"✓ Found {process_count} gunicorn processes")

        if process_count > 0:
            print("✓ Application processes are running")
            return True
        else:
            print("✗ No gunicorn processes found")
            return False
    else:
        print(f"✗ Failed to check processes: {result['stderr']}")
        return False


def test_port_listening():
    """Test if the application is listening on port 3000"""
    print("\n=== Testing Port Binding ===")

    # Check if port 3000 is in use
    result = run_ssh_command(
        "sudo lsof -i :3000 | grep -q LISTEN && echo 'listening' || echo 'not_listening'"
    )

    if result["returncode"] == 0 and "listening" in result["stdout"]:
        print("✓ Application is listening on port 3000")
        return True
    else:
        print("✗ Application is not listening on port 3000")
        return False


def test_service_logs():
    """Get recent service logs"""
    print("\n=== Testing Service Logs ===")

    # Get recent logs
    result = run_ssh_command("sudo journalctl -u mrpc --no-pager -n 10")

    if result["returncode"] == 0:
        print("✓ Service logs retrieved successfully")

        # Look for key indicators
        logs = result["stdout"]
        if "Starting gunicorn" in logs:
            print("  ✓ Gunicorn startup found in logs")
        if "Listening at:" in logs:
            print("  ✓ Server binding found in logs")
        if "ERROR" in logs:
            print("  ⚠ Errors found in logs")

        return True
    else:
        print(f"✗ Failed to get service logs: {result['stderr']}")
        return False


def test_service_enable_status():
    """Test if service is enabled for auto-start"""
    print("\n=== Testing Service Auto-Start Configuration ===")

    result = run_ssh_command("sudo systemctl is-enabled mrpc")

    if result["returncode"] == 0:
        status = result["stdout"]
        print(f"✓ Service enable status: {status}")

        if status == "enabled":
            print("✓ Service will start automatically on boot")
            return True
        else:
            print(f"⚠ Service auto-start status: {status}")
            return True  # Not necessarily a failure
    else:
        print(f"✗ Failed to check enable status: {result['stderr']}")
        return False


def run_all_tests():
    """Run all systemd deployment tests"""
    print("🚀 MRPC Systemd Deployment Tests")
    print("=" * 50)
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("SSH Connectivity", test_ssh_connectivity),
        ("Service Configuration", test_systemd_service_exists),
        ("Service Status", test_systemd_service_status),
        ("Service Details", test_systemd_service_details),
        ("Application Processes", test_application_process),
        ("Port Binding", test_port_listening),
        ("Service Logs", test_service_logs),
        ("Auto-Start Config", test_service_enable_status),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All systemd deployment tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
