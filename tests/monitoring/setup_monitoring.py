#!/usr/bin/env python3
"""
Setup automated memory monitoring for MRPC on the remote server
"""

import subprocess
import sys


def setup_memory_monitoring():
    """Set up automated memory monitoring on the remote server"""

    print("🔧 Setting up MRPC Memory Monitoring")
    print("=" * 50)

    # Create monitoring script on remote server
    monitoring_script = """#!/bin/bash
# MRPC Memory Monitor - Log memory usage every 5 minutes

LOG_FILE="$HOME/mrpc-memory.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Get system memory info
MEMORY_INFO=$(free -m | grep '^Mem:')
TOTAL_MEM=$(echo $MEMORY_INFO | awk '{print $2}')
USED_MEM=$(echo $MEMORY_INFO | awk '{print $3}')
AVAILABLE_MEM=$(echo $MEMORY_INFO | awk '{print $7}')
USED_PERCENT=$(echo "scale=1; $USED_MEM * 100 / $TOTAL_MEM" | bc)

# Get MRPC service memory
MRPC_MEMORY=$(sudo systemctl status mrpc --no-pager | grep Memory | awk '{print $2}' || echo "N/A")

# Get MRPC process count and total memory
MRPC_PROCESSES=$(pgrep -f 'gunicorn.*app:server' | wc -l)
MRPC_TOTAL_KB=$(ps aux | grep '[g]unicorn.*app:server' | awk '{sum+=$6} END {print sum+0}')
MRPC_TOTAL_MB=$(echo "scale=1; $MRPC_TOTAL_KB / 1024" | bc)

# Log the information
echo "[$TIMESTAMP] System: ${USED_MEM}MB/${TOTAL_MEM}MB (${USED_PERCENT}%) | MRPC: ${MRPC_TOTAL_MB}MB (${MRPC_PROCESSES} processes) | Systemd: $MRPC_MEMORY" >> $LOG_FILE

# Alert if memory usage is high
if (( $(echo "$USED_PERCENT > 85" | bc -l) )); then
    echo "[$TIMESTAMP] WARNING: High memory usage detected: ${USED_PERCENT}%" >> $LOG_FILE
    # Optionally send alert (uncomment and configure as needed)
    # echo "MRPC High Memory Alert: ${USED_PERCENT}% used" | mail -s "MRPC Memory Alert" admin@example.com
fi
"""

    print("📝 Creating monitoring script on remote server...")

    # Upload the monitoring script
    try:
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                f"cat > ~/mrpc-memory-monitor.sh << 'EOF'\n{monitoring_script}\nEOF",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Monitoring script created")
        else:
            print(f"❌ Failed to create monitoring script: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error creating monitoring script: {e}")
        return False

    # Make script executable
    print("🔧 Making script executable...")
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "chmod +x ~/mrpc-memory-monitor.sh"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(" Script made executable")
        else:
            print(f"❌ Failed to make script executable: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error making script executable: {e}")
        return False

    # Install bc calculator if not present
    print(" Installing bc calculator (required for percentage calculations)...")
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "sudo yum install -y bc"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print(" bc calculator installed")
        else:
            print(
                "⚠️ bc calculator installation may have failed (might already be installed)"
            )

    except Exception as e:
        print(f"⚠️ Error installing bc: {e}")

    # Set up cron job for automated monitoring
    print("⏰ Setting up automated monitoring (every 5 minutes)...")
    cron_entry = "*/5 * * * * /home/ec2-user/mrpc-memory-monitor.sh"

    try:
        # Add cron job
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                f"(crontab -l 2>/dev/null | grep -v 'mrpc-memory-monitor'; echo '{cron_entry}') | crontab -",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Automated monitoring set up (runs every 5 minutes)")
        else:
            print(f"❌ Failed to set up cron job: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

    # Test the monitoring script
    print("Testing monitoring script...")
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "~/mrpc-memory-monitor.sh"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Monitoring script test successful")
        else:
            print(f"⚠️ Monitoring script test failed: {result.stderr}")

    except Exception as e:
        print(f"⚠️ Error testing monitoring script: {e}")

    print("\n🎉 Memory monitoring setup complete!")
    print("\n📋 Monitoring Details:")
    print("  • Monitors system and MRPC memory every 5 minutes")
    print("  • Logs to ~/mrpc-memory.log on remote server")
    print("  • Alerts when memory usage exceeds 85%")
    print("  • Tracks MRPC process count and memory usage")

    print("\n📖 Usage Commands:")
    print("  View logs:     ssh data-explorer 'tail -f ~/mrpc-memory.log'")
    print("  Recent logs:   ssh data-explorer 'tail -20 ~/mrpc-memory.log'")
    print(
        "  Stop monitor:  ssh data-explorer 'crontab -l | grep -v mrpc-memory-monitor | crontab -'"
    )
    print("  Manual run:    ssh data-explorer '~/mrpc-memory-monitor.sh'")

    return True


def view_monitoring_logs():
    """View recent monitoring logs"""
    print("📋 Recent Memory Monitoring Logs")
    print("=" * 50)

    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "tail -20 ~/mrpc-memory.log"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ No monitoring logs found or error reading logs")
            print("💡 Run 'python setup_monitoring.py' to set up monitoring first")

    except Exception as e:
        print(f"❌ Error reading logs: {e}")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "logs":
            view_monitoring_logs()
            return
        elif sys.argv[1] == "help":
            print("MRPC Memory Monitoring Setup")
            print("Usage:")
            print("  python setup_monitoring.py        # Set up automated monitoring")
            print("  python setup_monitoring.py logs   # View recent logs")
            print("  python setup_monitoring.py help   # This help")
            return

    setup_memory_monitoring()


if __name__ == "__main__":
    main()
