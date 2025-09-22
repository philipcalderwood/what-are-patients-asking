#!/usr/bin/env python3
"""
Quick systemd service health check for MRPC
"""

import subprocess
import sys


def quick_status_check():
    """Quick status check of MRPC service"""
    try:
        # Check service status
        result = subprocess.run(
            ["ssh", "data-explorer", "sudo systemctl is-active mrpc"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip() == "active":
            print(" MRPC service is active and running")

            # Quick port check
            port_result = subprocess.run(
                [
                    "ssh",
                    "data-explorer",
                    "sudo lsof -i :3000 | grep -q LISTEN && echo 'OK'",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if port_result.returncode == 0:
                print(" Service is listening on port 3000")

                # Get memory usage
                get_memory_status()

                return True
            else:
                print("⚠️ Service is active but not listening on port 3000")
                return False
        else:
            print(f"❌ MRPC service is not active (status: {result.stdout.strip()})")

            # Show brief status
            status_result = subprocess.run(
                ["ssh", "data-explorer", "sudo systemctl status mrpc --no-pager -l"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if status_result.returncode == 0:
                lines = status_result.stdout.split("\n")
                for line in lines[:5]:  # Show first few lines
                    if "Active:" in line or "Main PID:" in line:
                        print(f"  {line.strip()}")

            return False

    except subprocess.TimeoutExpired:
        print("❌ SSH connection timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False


def get_memory_status():
    """Get quick memory status"""
    try:
        # Get system memory
        mem_result = subprocess.run(
            ["ssh", "data-explorer", "free -m | grep '^Mem:'"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if mem_result.returncode == 0:
            parts = mem_result.stdout.split()
            if len(parts) >= 7:
                total = int(parts[1])
                used = int(parts[2])
                used_percent = (used / total) * 100

                print(
                    f"💾 System Memory: {used}MB/{total}MB ({used_percent:.1f}% used)"
                )

                if used_percent > 85:
                    print("   ⚠️ HIGH memory usage!")
                elif used_percent > 70:
                    print("   🟡 Moderate memory usage")

        # Get MRPC process memory
        mrpc_result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                "sudo systemctl status mrpc --no-pager | grep Memory",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if mrpc_result.returncode == 0 and mrpc_result.stdout:
            print(f"🎯 MRPC Service: {mrpc_result.stdout.strip()}")

    except Exception as e:
        print(f"⚠️ Could not get memory status: {e}")


def show_management_commands():
    """Show useful systemd management commands"""
    print("\n📋 Useful Commands:")
    print("  Status:  ssh data-explorer 'sudo systemctl status mrpc'")
    print("  Start:   ssh data-explorer 'sudo systemctl start mrpc'")
    print("  Stop:    ssh data-explorer 'sudo systemctl stop mrpc'")
    print("  Restart: ssh data-explorer 'sudo systemctl restart mrpc'")
    print("  Logs:    ssh data-explorer 'sudo journalctl -u mrpc -f'")
    print("\n💾 Memory Monitoring:")
    print("  System Memory:  ssh data-explorer 'free -h'")
    print("  Process Memory: ssh data-explorer 'ps aux | grep gunicorn'")
    print("  Full Monitor:   python tests/monitor_system.py")
    print("  Continuous:     python tests/monitor_system.py continuous 60 300")


if __name__ == "__main__":
    print("🔍 MRPC Service Quick Check")
    print("=" * 30)

    if quick_status_check():
        sys.exit(0)
    else:
        show_management_commands()
        sys.exit(1)
