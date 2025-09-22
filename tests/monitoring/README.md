# MRPC Monitoring Tools

This directory contains all monitoring and system health checking tools for the MRPC deployment.

## Tools Overview

### Health & Status Checks

- **`test_service_health.py`** - Quick service health check with memory monitoring
- **`monitor_system.py`** - Comprehensive system resource monitoring
- **`memory_summary.py`** - Memory monitoring dashboard and overview

### Setup & Configuration

- **`setup_monitoring.py`** - Legacy cron-based monitoring setup
- **`setup_systemd_monitoring.py`** - Systemd timer-based monitoring setup (recommended)

### Validation

- **`validate_monitoring.py`** - Test suite to validate all monitoring tools

## Quick Start

```bash
# Quick health check
python tests/monitoring/test_service_health.py

# Full system analysis
python tests/monitoring/monitor_system.py

# Memory monitoring overview
python tests/monitoring/memory_summary.py

# Set up automated monitoring
python tests/monitoring/setup_systemd_monitoring.py

# Validate all tools
python tests/monitoring/validate_monitoring.py
```

## Remote Server Monitoring

```bash
# View live memory logs
ssh data-explorer 'tail -f ~/mrpc-memory.log'

# Check for alerts
ssh data-explorer 'grep WARNING ~/mrpc-memory.log'

# Check monitoring timer status
ssh data-explorer 'sudo systemctl status mrpc-memory-monitor.timer'
```

## Documentation

See `.docs/monitoring/MONITORING_GUIDE.md` for comprehensive documentation.

## File Permissions

All scripts should be executable:

```bash
chmod +x tests/monitoring/*.py
```
