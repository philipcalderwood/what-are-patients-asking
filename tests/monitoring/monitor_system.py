#!/usr/bin/env python3
"""
MRPC System Resource Monitor
Monitor RAM, CPU, disk usage, and service health
"""

import subprocess
import sys
import time
import json
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


def get_memory_usage():
    """Get detailed memory usage information"""
    print("🧠 Memory Usage")
    print("-" * 40)

    # Get memory info from /proc/meminfo
    result = run_ssh_command("cat /proc/meminfo | head -10")
    if result["returncode"] == 0:
        lines = result["stdout"].split("\n")
        memory_info = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                memory_info[key.strip()] = value.strip()

        # Parse key memory metrics
        total_mem = int(memory_info.get("MemTotal", "0").split()[0])
        free_mem = int(memory_info.get("MemFree", "0").split()[0])
        available_mem = int(memory_info.get("MemAvailable", "0").split()[0])
        buffers = int(memory_info.get("Buffers", "0").split()[0])
        cached = int(memory_info.get("Cached", "0").split()[0])

        used_mem = total_mem - free_mem
        used_percentage = (used_mem / total_mem) * 100
        available_percentage = (available_mem / total_mem) * 100

        print(f"  Total RAM:     {total_mem / 1024:.1f} MB")
        print(f"  Used RAM:      {used_mem / 1024:.1f} MB ({used_percentage:.1f}%)")
        print(
            f"  Available RAM: {available_mem / 1024:.1f} MB ({available_percentage:.1f}%)"
        )
        print(f"  Free RAM:      {free_mem / 1024:.1f} MB")
        print(f"  Buffers:       {buffers / 1024:.1f} MB")
        print(f"  Cached:        {cached / 1024:.1f} MB")

        # Memory usage warning
        if used_percentage > 85:
            print("  ⚠️  HIGH MEMORY USAGE WARNING!")
        elif used_percentage > 70:
            print("  🟡 Moderate memory usage")
        else:
            print("   Memory usage is healthy")

        return {
            "total_mb": total_mem / 1024,
            "used_mb": used_mem / 1024,
            "available_mb": available_mem / 1024,
            "used_percentage": used_percentage,
        }
    else:
        print("  ❌ Failed to get memory information")
        return None


def get_mrpc_process_memory():
    """Get memory usage specifically for MRPC processes"""
    print("\n🎯 MRPC Process Memory")
    print("-" * 40)

    # Get memory usage for gunicorn processes
    result = run_ssh_command(
        "ps aux | grep '[g]unicorn.*app:server' | awk '{print $6, $11}' | sort -nr"
    )

    if result["returncode"] == 0 and result["stdout"]:
        lines = result["stdout"].split("\n")
        total_mrpc_memory = 0
        process_count = 0

        print("  Process Memory Usage:")
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    memory_kb = int(parts[0])
                    memory_mb = memory_kb / 1024
                    total_mrpc_memory += memory_mb
                    process_count += 1
                    print(f"    Process {process_count}: {memory_mb:.1f} MB")

        print(f"\n  Total MRPC Memory: {total_mrpc_memory:.1f} MB")
        print(f"  Process Count: {process_count}")

        # Check systemctl memory reporting
        systemctl_result = run_ssh_command(
            "sudo systemctl status mrpc --no-pager | grep Memory"
        )
        if systemctl_result["returncode"] == 0 and systemctl_result["stdout"]:
            print(f"  Systemd Reports: {systemctl_result['stdout'].strip()}")

        return {"total_mb": total_mrpc_memory, "process_count": process_count}
    else:
        print("  ❌ No MRPC processes found or failed to get process info")
        return None


def get_cpu_usage():
    """Get CPU usage information"""
    print("\n💻 CPU Usage")
    print("-" * 40)

    # Get load average
    result = run_ssh_command("uptime")
    if result["returncode"] == 0:
        print(f"  {result['stdout']}")

    # Get CPU info
    cpu_result = run_ssh_command("nproc && cat /proc/loadavg")
    if cpu_result["returncode"] == 0:
        lines = cpu_result["stdout"].split("\n")
        if len(lines) >= 2:
            cpu_cores = int(lines[0])
            load_avg = lines[1].split()[:3]

            print(f"  CPU Cores: {cpu_cores}")
            print(f"  Load Average: {' '.join(load_avg)} (1m, 5m, 15m)")

            # Calculate load percentage for 1-minute average
            load_1m = float(load_avg[0])
            load_percentage = (load_1m / cpu_cores) * 100

            if load_percentage > 80:
                print("  ⚠️  HIGH CPU LOAD WARNING!")
            elif load_percentage > 60:
                print("  🟡 Moderate CPU load")
            else:
                print("   CPU load is healthy")


def get_disk_usage():
    """Get disk usage information"""
    print("\n💾 Disk Usage")
    print("-" * 40)

    result = run_ssh_command("df -h /home/ec2-user")
    if result["returncode"] == 0:
        lines = result["stdout"].split("\n")
        if len(lines) >= 2:
            print(f"  {lines[1]}")

            # Parse disk usage percentage
            parts = lines[1].split()
            if len(parts) >= 5:
                usage_percent = parts[4].rstrip("%")
                if usage_percent.isdigit():
                    usage = int(usage_percent)
                    if usage > 85:
                        print("  ⚠️  HIGH DISK USAGE WARNING!")
                    elif usage > 70:
                        print("  🟡 Moderate disk usage")
                    else:
                        print("   Disk usage is healthy")


def get_network_connections():
    """Get network connection information"""
    print("\n🌐 Network Connections")
    print("-" * 40)

    # Check active connections on port 3000
    result = run_ssh_command("sudo netstat -tlnp | grep :3000")
    if result["returncode"] == 0:
        print(f"  Port 3000 Status: {result['stdout']}")

    # Count active connections
    conn_result = run_ssh_command(
        "sudo netstat -an | grep :3000 | grep ESTABLISHED | wc -l"
    )
    if conn_result["returncode"] == 0:
        active_connections = conn_result["stdout"].strip()
        print(f"  Active Connections: {active_connections}")


def get_service_logs_with_memory():
    """Get recent service logs and extract memory-related information"""
    print("\n📋 Recent Service Logs")
    print("-" * 40)

    result = run_ssh_command(
        "sudo journalctl -u mrpc --no-pager -n 20 --since '10 minutes ago'"
    )
    if result["returncode"] == 0:
        logs = result["stdout"]

        # Look for memory-related patterns
        memory_keywords = [
            "memory",
            "Memory",
            "RAM",
            "OOM",
            "killed",
            "malloc",
            "out of memory",
        ]
        warning_found = False

        for line in logs.split("\n"):
            for keyword in memory_keywords:
                if keyword in line:
                    print(f"  🔍 {line.strip()}")
                    if any(
                        warn in line.lower()
                        for warn in ["oom", "killed", "out of memory"]
                    ):
                        warning_found = True

        if warning_found:
            print("  ⚠️  Memory-related warnings found in logs!")
        else:
            print("   No memory warnings in recent logs")


def monitor_continuous(interval=60, duration=300):
    """Continuous monitoring mode"""
    print(f"🔄 Starting continuous monitoring (every {interval}s for {duration}s)")
    print("=" * 60)

    start_time = time.time()
    iteration = 0

    try:
        while time.time() - start_time < duration:
            iteration += 1
            print(
                f"\nMonitoring Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}"
            )
            print("=" * 60)

            # Quick health check
            memory_info = get_memory_usage()
            mrpc_info = get_mrpc_process_memory()

            # Log critical metrics
            if memory_info and mrpc_info:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = {
                    "timestamp": timestamp,
                    "system_memory_used_percent": memory_info["used_percentage"],
                    "system_memory_available_mb": memory_info["available_mb"],
                    "mrpc_memory_total_mb": mrpc_info["total_mb"],
                    "mrpc_process_count": mrpc_info["process_count"],
                }

                # Append to monitoring log file
                log_result = run_ssh_command(
                    f"echo '{json.dumps(log_entry)}' >> ~/mrpc-monitoring.log"
                )
                if log_result["returncode"] == 0:
                    print("  📝 Logged metrics to ~/mrpc-monitoring.log")

            if iteration < duration // interval:
                print(f"\n⏱️  Waiting {interval} seconds until next check...")
                time.sleep(interval)
            else:
                break

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")


def show_monitoring_commands():
    """Show useful monitoring commands"""
    print("\n📋 Useful Monitoring Commands:")
    print("  System Memory:    ssh data-explorer 'free -h'")
    print("  Process Memory:   ssh data-explorer 'ps aux | grep gunicorn'")
    print("  Top Processes:    ssh data-explorer 'top -n 1 -b | head -20'")
    print("  Service Memory:   ssh data-explorer 'sudo systemctl status mrpc'")
    print("  Monitoring Log:   ssh data-explorer 'tail -f ~/mrpc-monitoring.log'")
    print("  Disk Usage:       ssh data-explorer 'df -h'")
    print(
        "  Memory History:   ssh data-explorer 'grep memory /var/log/messages | tail'"
    )


def main():
    """Main monitoring function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
            monitor_continuous(interval, duration)
            return
        elif sys.argv[1] == "help":
            print("MRPC System Monitor Usage:")
            print("  python monitor_system.py           # Single snapshot")
            print("  python monitor_system.py continuous [interval] [duration]")
            print("  python monitor_system.py help      # This help")
            return

    print("🔍 MRPC System Resource Monitor")
    print("=" * 50)
    print(f"Monitor run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all monitoring checks
    get_memory_usage()
    get_mrpc_process_memory()
    get_cpu_usage()
    get_disk_usage()
    get_network_connections()
    get_service_logs_with_memory()

    show_monitoring_commands()


if __name__ == "__main__":
    main()
