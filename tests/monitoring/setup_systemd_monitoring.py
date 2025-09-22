#!/usr/bin/env python3
"""
Create a systemd timer for memory monitoring (alternative to cron)
"""

import subprocess


def setup_systemd_monitoring():
    """Set up systemd timer for memory monitoring"""

    print("🔧 Setting up MRPC Memory Monitoring with Systemd Timer")
    print("=" * 60)

    # Get email for alerts
    email = input("📧 Enter email for memory alerts (or press Enter to skip): ").strip()
    email_enabled = bool(email)

    if email_enabled:
        print(f" Email notifications will be sent to: {email}")
    else:
        print("📝 Email notifications disabled")

    # Create the service file
    service_content = """[Unit]
Description=MRPC Memory Monitor
After=mrpc.service

[Service]
Type=oneshot
User=ec2-user
ExecStart=/home/ec2-user/mrpc-memory-monitor.sh
StandardOutput=journal
StandardError=journal
"""

    # Create the timer file
    timer_content = """[Unit]
Description=Run MRPC Memory Monitor every 5 minutes
Requires=mrpc-memory-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true
AccuracySec=1s

[Install]
WantedBy=timers.target
"""

    print("📝 Creating systemd service and timer files...")

    # Create the monitoring script with email support
    email_line = ""
    if email_enabled:
        email_line = f'    echo "MRPC High Memory Alert: ${{USED_PERCENT}}% used on $(hostname)" | mail -s "MRPC Memory Alert" {email}'
    else:
        email_line = "    # Email alerts disabled"

    monitoring_script = f"""#!/bin/bash
# MRPC Memory Monitor - Log memory usage every 5 minutes

LOG_FILE="$HOME/mrpc-memory.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Get system memory info
MEMORY_INFO=$(free -m | grep '^Mem:')
TOTAL_MEM=$(echo $MEMORY_INFO | awk '{{print $2}}')
USED_MEM=$(echo $MEMORY_INFO | awk '{{print $3}}')
AVAILABLE_MEM=$(echo $MEMORY_INFO | awk '{{print $7}}')
USED_PERCENT=$(echo "scale=1; $USED_MEM * 100 / $TOTAL_MEM" | bc)

# Get MRPC service memory
MRPC_MEMORY=$(sudo systemctl status mrpc --no-pager | grep Memory | awk '{{print $2}}' || echo "N/A")

# Get MRPC process count and total memory
MRPC_PROCESSES=$(pgrep -f 'gunicorn.*app:server' | wc -l)
MRPC_TOTAL_KB=$(ps aux | grep '[g]unicorn.*app:server' | awk '{{sum+=$6}} END {{print sum+0}}')
MRPC_TOTAL_MB=$(echo "scale=1; $MRPC_TOTAL_KB / 1024" | bc)

# Log the information
echo "[$TIMESTAMP] System: ${{USED_MEM}}MB/${{TOTAL_MEM}}MB (${{USED_PERCENT}}%) | MRPC: ${{MRPC_TOTAL_MB}}MB (${{MRPC_PROCESSES}} processes) | Systemd: $MRPC_MEMORY" >> $LOG_FILE

# Alert if memory usage is high
if (( $(echo "$USED_PERCENT > 85" | bc -l) )); then
    echo "[$TIMESTAMP] WARNING: High memory usage detected: ${{USED_PERCENT}}%" >> $LOG_FILE
{email_line}
fi
"""

    try:
        # Create monitoring script first
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

        # Make script executable
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

        # Install dependencies
        if email_enabled:
            print(" Installing email utilities...")
            result = subprocess.run(
                ["ssh", "data-explorer", "sudo yum install -y mailx bc"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(" Email utilities installed")
            else:
                print("⚠️ Email utilities installation may have failed")
        else:
            print(" Installing bc calculator...")
            result = subprocess.run(
                ["ssh", "data-explorer", "sudo yum install -y bc"],
                capture_output=True,
                text=True,
                timeout=60,
            )

        # Create service file
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                f"sudo tee /etc/systemd/system/mrpc-memory-monitor.service > /dev/null << 'EOF'\n{service_content}EOF",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Service file created")
        else:
            print(f"❌ Failed to create service file: {result.stderr}")
            return False

        # Create timer file
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                f"sudo tee /etc/systemd/system/mrpc-memory-monitor.timer > /dev/null << 'EOF'\n{timer_content}EOF",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Timer file created")
        else:
            print(f"❌ Failed to create timer file: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error creating systemd files: {e}")
        return False

    # Reload systemd and enable timer
    print("🔄 Reloading systemd and enabling timer...")
    try:
        commands = [
            "sudo systemctl daemon-reload",
            "sudo systemctl enable mrpc-memory-monitor.timer",
            "sudo systemctl start mrpc-memory-monitor.timer",
        ]

        for cmd in commands:
            result = subprocess.run(
                ["ssh", "data-explorer", cmd],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"⚠️ Warning with command '{cmd}': {result.stderr}")
            else:
                print(f" {cmd}")

    except Exception as e:
        print(f"⚠️ Error configuring systemd timer: {e}")

    # Check timer status
    print("Checking timer status...")
    try:
        result = subprocess.run(
            [
                "ssh",
                "data-explorer",
                "sudo systemctl status mrpc-memory-monitor.timer --no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Timer status:")
            print(result.stdout)
        else:
            print(f"⚠️ Could not get timer status: {result.stderr}")

    except Exception as e:
        print(f"⚠️ Error checking timer status: {e}")

    # Test the monitoring
    print("Running initial memory monitoring test...")
    try:
        result = subprocess.run(
            ["ssh", "data-explorer", "~/mrpc-memory-monitor.sh"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(" Monitoring script test successful")

            # Show the log entry
            log_result = subprocess.run(
                ["ssh", "data-explorer", "tail -1 ~/mrpc-memory.log"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if log_result.returncode == 0:
                print(f"📋 Latest log entry: {log_result.stdout.strip()}")
        else:
            print(f"⚠️ Monitoring script test failed: {result.stderr}")

    except Exception as e:
        print(f"⚠️ Error testing monitoring script: {e}")

    print("\n🎉 Systemd Memory Monitoring Setup Complete!")
    print("\n📋 Monitoring Details:")
    print("  • Systemd timer runs every 5 minutes")
    print("  • Logs to ~/mrpc-memory.log on remote server")
    print("  • Alerts when memory usage exceeds 85%")
    print("  • Tracks both system and MRPC memory usage")
    if email_enabled:
        print(f"  • Email alerts enabled: {email}")
    else:
        print("  • Email alerts disabled")

    print("\n📖 Management Commands:")
    print("  View logs:       ssh data-explorer 'tail -f ~/mrpc-memory.log'")
    print(
        "  Timer status:    ssh data-explorer 'sudo systemctl status mrpc-memory-monitor.timer'"
    )
    print(
        "  Stop monitor:    ssh data-explorer 'sudo systemctl stop mrpc-memory-monitor.timer'"
    )
    print(
        "  Start monitor:   ssh data-explorer 'sudo systemctl start mrpc-memory-monitor.timer'"
    )
    print(
        "  Manual run:      ssh data-explorer 'sudo systemctl start mrpc-memory-monitor.service'"
    )
    if email_enabled:
        print(
            f'  Test email:      ssh data-explorer \'echo "Test alert" | mail -s "MRPC Test" {email}\''
        )

    return True


if __name__ == "__main__":
    setup_systemd_monitoring()
