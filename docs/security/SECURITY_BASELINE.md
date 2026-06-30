# Security Baseline and Deployment Guidelines

**Version:** 1.0  
**Date:** 2026-06-20  
**Status:** Active

## Overview

This document establishes the security baseline for SkyMeshX deployments and provides guidelines for secure configuration and operation. It implements fixes from the security audit (SECURITY_AUDIT_FULL_2026-06-20.md).

---

## Critical Security Requirements

### 1. Pi Server Deployment (SEC-01, SEC-02, SEC-04)

#### Default Configuration (Secure)
```bash
# Bind to localhost only (default)
python3 pi/server.py --port /dev/ttyUSB0 --baud 57600 --http 8080

# Server will:
# - Bind to 127.0.0.1 (localhost only)
# - Generate random API token
# - Disable CORS
# - Enforce 8KB request size limit
```

#### Remote Access Configuration (Use with Caution)
```bash
# Set persistent API token
export SKYMESHX_PI_TOKEN="your-secure-random-token-here"

# Bind to all interfaces (requires explicit flag)
python3 pi/server.py \
  --port /dev/ttyUSB0 \
  --baud 57600 \
  --http 8080 \
  --host 0.0.0.0 \
  --api-token "$SKYMESHX_PI_TOKEN"
```

**Security Warnings:**
- ⚠️ Binding to `0.0.0.0` exposes the server to the network
- ⚠️ Always use a strong API token (32+ characters, random)
- ⚠️ Configure firewall rules to restrict access
- ⚠️ Use HTTPS reverse proxy (nginx/caddy) for production
- ⚠️ Never enable CORS unless absolutely necessary

#### API Authentication

All `/api/*` endpoints require Bearer token authentication:

```bash
# Example authenticated request
curl -H "Authorization: Bearer your-token-here" \
  http://localhost:8080/api/telemetry
```

```bash
# Example command with authentication
curl -X POST \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"ARM","params":{}}' \
  http://localhost:8080/api/command
```

**Token Management:**
- Generate tokens using: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- Store tokens securely (environment variables, not in code)
- Rotate tokens periodically
- Use different tokens for different deployments

---

### 2. License Secret Management (UI-13)

#### Development Builds
```bash
# Development builds use default secret (allowed)
SKIP_LICENSE_CHECK=1 pip install -e .
```

#### Production Builds
```bash
# Set production secret before building
export SKYMESHX_LICENSE_SECRET="your-production-secret-min-32-chars"

# Build will fail if dev secret is detected
pip install .
python setup.py bdist_wheel
```

**Secret Requirements:**
- Minimum 32 characters
- Cryptographically random
- Never commit to repository
- Rotate before each major release
- Store in secure secret management system

**Secret Generation:**
```bash
# Generate a secure secret
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

### 3. UI Script Execution (UI-02)

#### Path Validation

All script operations validate filenames to prevent path traversal:

```python
# ✅ Safe - simple filename
context.saveAndRunScript("my_mission.py", code)

# ❌ Blocked - path traversal attempt
context.saveAndRunScript("../../../etc/passwd", code)

# ❌ Blocked - absolute path
context.saveAndRunScript("/tmp/malicious.py", code)

# ❌ Blocked - hidden file
context.saveAndRunScript(".hidden.py", code)
```

**Validation Rules:**
- Only basename is used (directory components stripped)
- Absolute paths rejected
- Parent directory references (`..`) rejected
- Hidden files (starting with `.`) rejected
- All paths resolved and validated within `experiments/uploads/`

---

## Deployment Scenarios

### Scenario 1: Local Development

**Configuration:**
- Pi server: localhost only, auto-generated token
- UI: local execution, trusted scripts only
- No remote access

**Commands:**
```bash
# Pi server
python3 pi/server.py --port tcp:127.0.0.1:5762 --http 8080

# GCS UI
python3 -m tools.ui
```

**Security Level:** ✅ High (default secure configuration)

---

### Scenario 2: Lab/Field Testing

**Configuration:**
- Pi server: network accessible, persistent token
- Firewall: restrict to known IPs
- HTTPS: reverse proxy with TLS

**Commands:**
```bash
# Generate and store token
export SKYMESHX_PI_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "$SKYMESHX_PI_TOKEN" > ~/.skymeshx_token
chmod 600 ~/.skymeshx_token

# Pi server with network access
python3 pi/server.py \
  --port /dev/ttyUSB0 \
  --baud 57600 \
  --http 8080 \
  --host 0.0.0.0 \
  --api-token "$SKYMESHX_PI_TOKEN"

# Configure nginx reverse proxy
# See: docs/deployment/nginx-example.conf
```

**Security Level:** ⚠️ Medium (requires proper firewall and TLS)

---

### Scenario 3: Production Deployment

**Configuration:**
- Pi server: localhost only, systemd service
- Reverse proxy: nginx/caddy with TLS
- Firewall: strict IP allowlist
- Monitoring: log all API access
- Updates: signed releases only

**Setup:**
```bash
# 1. Install as systemd service
sudo cp pi/droneresearch.service /etc/systemd/system/
sudo systemctl enable droneresearch
sudo systemctl start droneresearch

# 2. Configure nginx with TLS
# See: docs/deployment/nginx-production.conf

# 3. Set up firewall
sudo ufw allow from 192.168.1.0/24 to any port 443
sudo ufw enable

# 4. Configure log monitoring
# See: docs/deployment/log-monitoring.md
```

**Security Level:** ✅ High (defense in depth)

---

## Security Checklist

### Pre-Deployment

- [ ] Pi server binds to localhost by default
- [ ] API token is set and stored securely
- [ ] CORS is disabled (or explicitly configured)
- [ ] License secret is rotated for production builds
- [ ] All dependencies are up to date
- [ ] Security tests pass (`pytest tests/security/`)

### Network Configuration

- [ ] Firewall rules configured
- [ ] TLS/HTTPS enabled for remote access
- [ ] IP allowlist configured
- [ ] Rate limiting enabled (if using reverse proxy)
- [ ] DDoS protection configured (if public-facing)

### Operational Security

- [ ] API tokens rotated periodically
- [ ] Access logs monitored
- [ ] Security updates applied promptly
- [ ] Incident response plan documented
- [ ] Backup and recovery procedures tested

### Code Security

- [ ] Script execution limited to trusted sources
- [ ] File operations validate paths
- [ ] Input validation on all user-provided data
- [ ] No hardcoded credentials in code
- [ ] Security audit findings addressed

---

## Security Monitoring

### Log Files

**Pi Server Logs:**
```bash
# View server logs
journalctl -u droneresearch -f

# Check for authentication failures
journalctl -u droneresearch | grep "Unauthorized"

# Monitor command execution
journalctl -u droneresearch | grep "CMD"
```

**Security Events to Monitor:**
- Failed authentication attempts
- Unusual command patterns
- High request rates
- Path traversal attempts
- Large request bodies

### Alerting

Set up alerts for:
- Multiple failed auth attempts (>5 in 1 minute)
- Commands from unexpected IPs
- Server restarts/crashes
- Disk space low (<10%)
- High CPU/memory usage

---

## Incident Response

### Security Incident Procedure

1. **Detect:** Monitor logs for suspicious activity
2. **Contain:** Disable affected services immediately
3. **Investigate:** Review logs, identify attack vector
4. **Remediate:** Apply fixes, rotate credentials
5. **Document:** Record incident details and lessons learned
6. **Review:** Update security baseline and procedures

### Emergency Commands

```bash
# Stop Pi server immediately
sudo systemctl stop droneresearch

# Rotate API token
export SKYMESHX_PI_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sudo systemctl restart droneresearch

# Block IP address
sudo ufw deny from <attacker-ip>

# Review recent access
journalctl -u droneresearch --since "1 hour ago" | grep "api"
```

---

## Security Updates

### Update Procedure

1. Review security advisories
2. Test updates in development environment
3. Schedule maintenance window
4. Apply updates
5. Verify functionality
6. Monitor for issues

### Update Sources

- GitHub Security Advisories: https://github.com/joeldjio/skymeshx/security/advisories
- Dependency updates: `pip list --outdated`
- CVE databases: https://nvd.nist.gov/

---

## Compliance and Standards

### Applicable Standards

- **OWASP Top 10:** Web application security risks
- **CWE Top 25:** Most dangerous software weaknesses
- **NIST Cybersecurity Framework:** Risk management

### Security Controls Implemented

| Control | Implementation | Status |
|---------|---------------|--------|
| Authentication | Bearer token API auth | ✅ Implemented |
| Authorization | Command validation | ✅ Implemented |
| Input Validation | Path traversal prevention | ✅ Implemented |
| Cryptography | HMAC-SHA256 license signing | ✅ Implemented |
| Logging | Comprehensive audit logs | ✅ Implemented |
| Network Security | Localhost binding default | ✅ Implemented |
| Secure Configuration | Security-first defaults | ✅ Implemented |

---

## References

- [Security Audit Report](SECURITY_AUDIT_FULL_2026-06-20.md)
- [Remediation Plan](SECURITY_REMEDIATION_PLAN.md)
- [Security Policy](../../SECURITY.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)

---

## Contact

**Security Issues:** Report to djiojoel2@gmail.com  
**Security Team:** See SECURITY.md for contact information

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-20 | 1.0 | Initial security baseline established |
