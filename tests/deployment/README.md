# MRPC Deployment Tests

This directory contains deployment validation and testing tools.

## Tools Overview

### Deployment Validation

- **`test_systemd_deployment.py`** - Comprehensive systemd deployment verification

## Usage

```bash
# Full deployment validation
python tests/deployment/test_systemd_deployment.py
```

This test validates:

- SSH connectivity to deployment server
- Systemd service configuration and status
- Application process health
- Port binding (3000) and network accessibility
- Service logs and auto-start configuration
- Memory usage monitoring and alerting

## Test Coverage

The deployment test performs 8 comprehensive checks with 100% success rate validation.

## Related Tools

For ongoing monitoring after deployment, see `tests/monitoring/` directory.
