# Security Remediation Plan

**Date:** 2026-06-20  
**Based on:** SECURITY_AUDIT_FULL_2026-06-20.md  
**Status:** In Progress

## Overview

This document tracks the implementation of security fixes identified in the full security audit. Fixes are prioritized by severity and impact, with release blockers addressed first.

## Priority Classification

- **P0 (Release Blocker):** Must be fixed before any production release
- **P1 (Critical):** High security risk, fix in current sprint
- **P2 (High):** Significant risk, fix within 2 sprints
- **P3 (Medium):** Moderate risk, schedule for next major release
- **P4 (Low):** Minor risk, address opportunistically

---

## Release Blockers (P0)

### SEC-01: Pi HTTP Server Unauthenticated Flight Commands
**Status:** 🔴 Not Started  
**Priority:** P0  
**Files:** [`pi/server.py:210`](../../pi/server.py:210), [`pi/server.py:502`](../../pi/server.py:502), [`pi/server.py:550`](../../pi/server.py:550)

**Issue:**  
`POST /api/command` accepts ARM, DISARM, TAKEOFF, LAND, RTL, MODE, and GOTO without authentication. Server binds to `0.0.0.0` by default.

**Implementation Plan:**
1. Add `--host` argument with default `127.0.0.1`
2. Add `--api-token` argument and `SKYMESHX_PI_TOKEN` environment variable
3. Implement `Authorization: Bearer <token>` validation for all `/api/*` endpoints
4. Add command allow/deny policy flags (`--allow-arm`, `--allow-takeoff`, etc.)
5. Return 401 Unauthorized for missing/invalid tokens
6. Return 403 Forbidden for denied commands

**Testing:**
- Verify localhost-only binding by default
- Verify token requirement for all API endpoints
- Verify command policy enforcement
- Add `tests/test_pi_server_security.py`

**Estimated Effort:** 4 hours

---

### UI-02: Path Traversal in Experiment Script Operations
**Status:** 🔴 Not Started  
**Priority:** P0  
**Files:** [`tools/ui/context/experiment_context.py:195`](../../tools/ui/context/experiment_context.py:195), [`tools/ui/context/experiment_context.py:300`](../../tools/ui/context/experiment_context.py:300), [`tools/ui/context/experiment_context.py:348`](../../tools/ui/context/experiment_context.py:348), [`tools/ui/context/experiment_context.py:359`](../../tools/ui/context/experiment_context.py:359)

**Issue:**  
`filename` is joined directly with `experiments/uploads` for save, read, and delete operations. Values like `../other.py` can escape the directory.

**Implementation Plan:**
1. Use `Path(filename).name` to extract basename only
2. Resolve final path and validate it stays within `_scripts_dir.resolve()`
3. Reject absolute paths and `..` segments explicitly
4. Add validation helper: `_validate_script_path(filename: str) -> Path`

**Code Changes:**
```python
def _validate_script_path(self, filename: str) -> Path:
    """Validate script filename and return safe path within uploads directory."""
    # Extract basename only - prevents directory traversal
    safe_name = Path(filename).name
    
    # Reject empty or suspicious names
    if not safe_name or safe_name.startswith('.') or '..' in safe_name:
        raise ValueError(f"Invalid script filename: {filename}")
    
    # Build and resolve full path
    filepath = (self._scripts_dir / safe_name).resolve()
    
    # Ensure path is within uploads directory
    if not filepath.is_relative_to(self._scripts_dir.resolve()):
        raise ValueError(f"Path traversal attempt: {filename}")
    
    return filepath
```

**Testing:**
- Test rejection of `../escape.py`
- Test rejection of `/absolute/path.py`
- Test rejection of `subdir/../../../etc/passwd`
- Add `tests/test_ui_path_security.py`

**Estimated Effort:** 2 hours

---

### UI-11: Updater Executes Downloaded Installer Without Mandatory Signature
**Status:** 🔴 Not Started  
**Priority:** P0  
**Files:** [`tools/ui/updater.py:120`](../../tools/ui/updater.py:120), [`tools/ui/updater.py:183`](../../tools/ui/updater.py:183), [`tools/ui/updater.py:399`](../../tools/ui/updater.py:399)

**Issue:**  
SHA256 verification is optional and the `.sha256` file comes from the same release channel. No cryptographic signature verification.

**Implementation Plan:**
1. Generate Ed25519 signing keypair (keep private key offline)
2. Embed public key in `tools/ui/_version.py`
3. Sign release assets with detached `.sig` files
4. Require signature verification before installation
5. Fail update if signature is missing or invalid
6. Document signing process in release workflow

**Code Changes:**
```python
# In _version.py
RELEASE_PUBLIC_KEY = "ed25519:AAAA..."  # Base64-encoded public key

# In updater.py
def _verify_signature(self, installer_path: Path, sig_url: str) -> bool:
    """Verify Ed25519 signature of installer."""
    import base64
    from cryptography.hazmat.primitives.asymmetric import ed25519
    
    # Download signature
    sig_data = self._download_signature(sig_url)
    
    # Load public key
    pub_key_bytes = base64.b64decode(RELEASE_PUBLIC_KEY.split(':')[1])
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    
    # Verify signature
    with open(installer_path, 'rb') as f:
        file_data = f.read()
    
    try:
        public_key.verify(sig_data, file_data)
        return True
    except Exception:
        return False
```

**Testing:**
- Test update rejection with missing signature
- Test update rejection with invalid signature
- Test successful update with valid signature
- Add `tests/test_updater_security.py`

**Estimated Effort:** 6 hours (includes release workflow updates)

---

### UI-13: Development License Secret Active in Source
**Status:** 🔴 Not Started  
**Priority:** P0  
**Files:** [`tools/ui/_version.py:50`](../../tools/ui/_version.py:50), [`tools/ui/license.py:26`](../../tools/ui/license.py:26)

**Issue:**  
`LICENSE_SECRET = "skymeshx-dev-secret-CHANGE-ME-before-shipping"` allows anyone with source access to mint valid license keys.

**Implementation Plan:**
1. Add build-time validation in `setup.py` or CI
2. Fail build if secret contains `skymeshx-dev-secret`
3. Document secret rotation process
4. Generate production secret (store securely, not in repo)
5. Use environment variable `SKYMESHX_LICENSE_SECRET` in build process

**Code Changes:**
```python
# In setup.py or build script
def validate_license_secret():
    """Ensure production secret is set before release builds."""
    from tools.ui._version import LICENSE_SECRET
    
    if LICENSE_SECRET.startswith("skymeshx-dev-secret"):
        raise ValueError(
            "RELEASE BLOCKER: Development license secret detected!\n"
            "Set SKYMESHX_LICENSE_SECRET environment variable before building."
        )
    
    if len(LICENSE_SECRET) < 32:
        raise ValueError("License secret must be at least 32 characters")

# In _version.py
LICENSE_SECRET: str = os.getenv(
    "SKYMESHX_LICENSE_SECRET",
    "skymeshx-dev-secret-CHANGE-ME-before-shipping"
)
```

**Testing:**
- Verify build fails with dev secret
- Verify build succeeds with production secret
- Document in CI/CD pipeline

**Estimated Effort:** 2 hours

---

### UI-05: WebEngine Loads External JavaScript Without Bundling
**Status:** 🔴 Not Started  
**Priority:** P0  
**Files:** [`tools/ui/qml/MapView.qml:86`](../../tools/ui/qml/MapView.qml:86), [`tools/ui/qml/MapView.qml:376-377`](../../tools/ui/qml/MapView.qml:376)

**Issue:**  
Leaflet CSS/JS loaded from `https://unpkg.com` without bundling or SRI. Supply-chain risk and offline fragility.

**Implementation Plan:**
1. Download Leaflet 1.9.4 assets locally
2. Place in `tools/ui/resources/leaflet/`
3. Update QML to load from `qrc://` resources
4. Add resource compilation to build process
5. Test offline map functionality

**Estimated Effort:** 3 hours

---

## Critical Fixes (P1)

### SEC-02: Pi Server Wildcard CORS
**Status:** 🔴 Not Started  
**Priority:** P1  
**Files:** [`pi/server.py:522`](../../pi/server.py:522), [`pi/server.py:526`](../../pi/server.py:526)

**Issue:**  
Every response includes `Access-Control-Allow-Origin: *`, enabling cross-origin telemetry/command access.

**Implementation Plan:**
1. Remove CORS headers by default
2. Add optional `--cors-origin` argument for specific origins
3. Only add CORS headers if explicitly configured
4. Enforce authentication before CORS responses

**Estimated Effort:** 1 hour

---

### SEC-03: XSS in Pi Dashboard Log Rendering
**Status:** 🔴 Not Started  
**Priority:** P1  
**Files:** [`pi/server.py:197`](../../pi/server.py:197), [`pi/server.py:381`](../../pi/server.py:381)

**Issue:**  
MAVLink `STATUSTEXT` rendered via `innerHTML` without sanitization.

**Implementation Plan:**
1. Replace `innerHTML` with `document.createElement()` and `textContent`
2. Whitelist log levels for CSS class names
3. Escape all user-controlled content

**Code Changes:**
```javascript
// Replace line 382
const el = document.getElementById('log');
el.innerHTML = '';  // Clear
lines.forEach(l => {
    const span = document.createElement('span');
    const level = ['D','I','W','E','C'].includes(l.l) ? l.l : 'I';
    span.className = `log-${level}`;
    const timestamp = new Date(l.t*1000).toISOString().substr(11,8);
    span.textContent = `[${timestamp}] ${l.m}`;
    el.appendChild(span);
    el.appendChild(document.createElement('br'));
});
el.scrollTop = el.scrollHeight;
```

**Testing:**
- Test with malicious `<script>alert(1)</script>` in STATUSTEXT
- Verify no script execution
- Add to `tests/test_pi_server_security.py`

**Estimated Effort:** 1 hour

---

### SEC-04: Pi Server Request Body Size and Blocking
**Status:** 🔴 Not Started  
**Priority:** P1  
**Files:** [`pi/server.py:504`](../../pi/server.py:504), [`pi/server.py:555`](../../pi/server.py:555)

**Issue:**  
Unbounded request body reading can block single-threaded server.

**Implementation Plan:**
1. Add `MAX_BODY_SIZE = 8192` constant
2. Reject requests with `Content-Length > MAX_BODY_SIZE`
3. Set socket timeout (5 seconds)
4. Consider `ThreadingHTTPServer` for remote access

**Estimated Effort:** 2 hours

---

### UI-07: Dangerous Flight Actions Without Confirmation
**Status:** 🔴 Not Started  
**Priority:** P1  
**Files:** [`tools/ui/context/swarm_context.py:167`](../../tools/ui/context/swarm_context.py:167), [`tools/ui/context/swarm_context.py:187`](../../tools/ui/context/swarm_context.py:187)

**Issue:**  
Immediate confirmation signals after sending commands, not after vehicle ACK. No confirmation dialogs for destructive actions.

**Implementation Plan:**
1. Rename signals: `armConfirmed` → `armCommandSent`
2. Add new signals: `armAcknowledged`, `takeoffAcknowledged`
3. Wait for telemetry/ACK before emitting acknowledged signals
4. Add confirmation dialogs for:
   - Force disarm
   - All-drone commands
   - Takeoff-all
5. Add per-drone command cooldowns (500ms)

**Estimated Effort:** 4 hours

---

## High Priority (P2)

### UI-03: Broad QML File Read/Write Bridge
**Status:** 🔴 Not Started  
**Priority:** P2  
**Files:** [`tools/ui/context/swarm_context.py:803`](../../tools/ui/context/swarm_context.py:803), [`tools/ui/context/swarm_context.py:818`](../../tools/ui/context/swarm_context.py:818)

**Implementation Plan:**
1. Replace generic `readFile`/`writeFile` with purpose-specific APIs
2. Create `readCsvFile`, `exportLogFile`, `appendSyslog`
3. Restrict log writes to `logs/syslogs` directory
4. Require FileDialog-selected paths for exports
5. Validate file extensions

**Estimated Effort:** 3 hours

---

### UI-06: JavaScript String Injection in runJavaScript
**Status:** 🔴 Not Started  
**Priority:** P2  
**Files:** [`tools/ui/qml/MapView.qml:32`](../../tools/ui/qml/MapView.qml:32), [`tools/ui/qml/MapView.qml:336`](../../tools/ui/qml/MapView.qml:336)

**Implementation Plan:**
1. Always use `JSON.stringify()` for dynamic values
2. Validate drone IDs against allowlist pattern
3. Validate map types against enum

**Code Changes:**
```qml
// Before
webView.runJavaScript("setSelectedDrone('" + did + "')")

// After
webView.runJavaScript("setSelectedDrone(" + JSON.stringify(did) + ")")
```

**Estimated Effort:** 2 hours

---

### UI-08: Coordinate and Altitude Validation
**Status:** 🔴 Not Started  
**Priority:** P2  
**Files:** [`tools/ui/context/swarm_context.py:228`](../../tools/ui/context/swarm_context.py:228), [`tools/ui/context/swarm_context.py:234`](../../tools/ui/context/swarm_context.py:234)

**Implementation Plan:**
1. Create shared validator module: `skymeshx/validation/coordinates.py`
2. Implement validators:
   - `validate_latitude(lat: float) -> float`
   - `validate_longitude(lon: float) -> float`
   - `validate_altitude(alt: float, max_alt: float) -> float`
   - `validate_velocity(vel: tuple, max_speed: float) -> tuple`
3. Use in all UI command slots, CLI, Pi API, MAVLink, ROS2 paths

**Estimated Effort:** 4 hours

---

### UI-09: ROS2 SITL Shell Command Injection Risk
**Status:** 🔴 Not Started  
**Priority:** P2  
**Files:** [`tools/ui/context/ros2_context.py:358`](../../tools/ui/context/ros2_context.py:358), [`skymeshx/simulation/px4_gazebo.py:168`](../../skymeshx/simulation/px4_gazebo.py:168)

**Implementation Plan:**
1. Remove `shell=True` from subprocess calls
2. Use `shlex.quote()` if shell is unavoidable
3. Whitelist model names: `["iris", "typhoon_h480", ...]`
4. Validate namespace pattern: `^[a-zA-Z0-9_]+$`
5. Validate setup file paths exist and are regular files

**Estimated Effort:** 3 hours

---

### UI-10: Bag Playback Arbitrary Path Access
**Status:** 🔴 Not Started  
**Priority:** P2  
**Files:** [`tools/ui/context/bag_playback_context.py:74`](../../tools/ui/context/bag_playback_context.py:74), [`tools/ui/context/ros2_context.py:939`](../../tools/ui/context/ros2_context.py:939)

**Implementation Plan:**
1. Restrict default playback to `bags/` directory
2. Permit external paths only via FileDialog selection
3. Validate bag metadata before playback
4. Add path validation helper

**Estimated Effort:** 2 hours

---

## Medium Priority (P3)

### UI-04: WebEngine Navigation Accepts Non-Internal URLs
**Status:** 🔴 Not Started  
**Priority:** P3  
**Files:** [`tools/ui/qml/MapView.qml:95`](../../tools/ui/qml/MapView.qml:95), [`tools/ui/qml/MapView.qml:140`](../../tools/ui/qml/MapView.qml:140)

**Implementation Plan:**
1. Create allowlist of permitted schemes: `["qrc", "data"]`
2. Create allowlist of permitted hosts for tiles
3. Reject all other navigation attempts

**Estimated Effort:** 2 hours

---

### UI-12: Release Repository Configuration Inconsistency
**Status:** 🔴 Not Started  
**Priority:** P3  
**Files:** [`tools/ui/_version.py:34`](../../tools/ui/_version.py:34), [`tools/installer/inno/skymeshx_gcs.iss:25`](../../tools/installer/inno/skymeshx_gcs.iss:25)

**Implementation Plan:**
1. Consolidate to single repository constant
2. Generate installer metadata from `_version.py`
3. Document release channel governance

**Estimated Effort:** 1 hour

---

### UI-01: UI Script Execution Runs Arbitrary Python
**Status:** 🔴 Not Started  
**Priority:** P3  
**Files:** [`tools/ui/context/experiment_context.py:121`](../../tools/ui/context/experiment_context.py:121), [`skymeshx/control/script_runner.py:145`](../../skymeshx/control/script_runner.py:145)

**Implementation Plan:**
1. Add prominent warning in UI: "Script execution is trusted-only"
2. Add confirmation dialog before executing unsaved/imported code
3. Consider subprocess sandbox for future versions
4. Document as trusted-only in user guide

**Estimated Effort:** 3 hours

---

## Low Priority (P4)

### UI-14: License State is Local and User-Writable
**Status:** 🔴 Not Started  
**Priority:** P4  
**Files:** [`tools/ui/license.py:137`](../../tools/ui/license.py:137), [`tools/ui/license.py:145`](../../tools/ui/license.py:145)

**Implementation Plan:**
1. Document as casual protection only
2. For stronger enforcement, implement server activation in future

**Estimated Effort:** 0 hours (documentation only)

---

### UI-15: LLM Command Path Sends Swarm State to External Providers
**Status:** 🔴 Not Started  
**Priority:** P4  
**Files:** [`skymeshx/llm/swarm_commander.py:114`](../../skymeshx/llm/swarm_commander.py:114), [`skymeshx/llm/swarm_commander.py:214`](../../skymeshx/llm/swarm_commander.py:214)

**Implementation Plan:**
1. Add privacy warning in UI before enabling cloud LLM
2. Default to `mock` or local `ollama`
3. Redact/coarsen coordinates when possible

**Estimated Effort:** 2 hours

---

### UI-16: Logs May Include Sensitive Operational Data
**Status:** 🔴 Not Started  
**Priority:** P4  
**Files:** [`tools/ui/context/swarm_context.py:95`](../../tools/ui/context/swarm_context.py:95), [`tools/ui/context/swarm_context.py:151`](../../tools/ui/context/swarm_context.py:151)

**Implementation Plan:**
1. Redact credentials in connection strings
2. Avoid logging exact paths unless debug mode
3. Provide log-scrub/export option

**Estimated Effort:** 3 hours

---

## Testing Strategy

### Security Test Suite Structure
```
tests/security/
├── __init__.py
├── test_pi_server_security.py      # SEC-01, SEC-02, SEC-03, SEC-04
├── test_ui_path_security.py        # UI-02, UI-10
├── test_ui_command_validation.py   # UI-08
├── test_map_webengine_security.py  # UI-06, UI-04
└── test_updater_security.py        # UI-11
```

### Test Coverage Goals
- All P0 fixes: 100% test coverage
- All P1 fixes: 90% test coverage
- All P2 fixes: 80% test coverage

---

## Release Criteria

### Pre-Release Checklist
- [ ] All P0 (Release Blocker) issues resolved
- [ ] Security test suite passing
- [ ] Manual penetration testing completed
- [ ] Security documentation updated
- [ ] Deployment guidelines published

### Post-Release Monitoring
- Monitor for security-related bug reports
- Track CVE disclosures for dependencies
- Schedule quarterly security reviews

---

## Timeline

| Phase | Duration | Completion Target |
|-------|----------|-------------------|
| P0 Fixes | 2 weeks | 2026-07-04 |
| P1 Fixes | 1 week | 2026-07-11 |
| P2 Fixes | 2 weeks | 2026-07-25 |
| P3 Fixes | 1 week | 2026-08-01 |
| P4 Fixes | Ongoing | 2026-09-01 |

---

## Resources

- **Security Audit:** [`docs/security/SECURITY_AUDIT_FULL_2026-06-20.md`](SECURITY_AUDIT_FULL_2026-06-20.md)
- **Security Policy:** [`SECURITY.md`](../../SECURITY.md)
- **Contributing Guidelines:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-20 | Initial remediation plan created | Security Team |