# Security Audit Full Report

Date: 2026-06-20
Scope: core package, Pi server, GCS UI/QML, updater, installer scripts, ROS2/SITL helpers, script execution, licensing.

This audit is a static source review. Test execution was attempted but could not be completed in the local environment:

- `pytest tests/` failed because `pytest` was not available in PATH.
- `python -m pytest tests/` failed because `python.exe` could not start in this Windows session.

## Executive Summary

The highest risk is operational safety: multiple paths can send live flight commands without strong guardrails. The Pi server exposes unauthenticated HTTP command endpoints on all interfaces. The GCS UI has trusted Python script execution, file operations exposed to QML, update installation from GitHub release assets, and WebEngine map content that loads external JavaScript.

Most issues are fixable with a small security baseline:

1. Bind remote-control services to localhost by default.
2. Add token-based auth to HTTP APIs.
3. Validate all coordinates, altitude, command rates, and filesystem paths before use.
4. Treat UI script execution as trusted-only or isolate it by default.
5. Bundle/sign update artifacts and WebEngine dependencies.

## Findings

### SEC-01 Critical: Pi HTTP server allows unauthenticated flight commands

Files:

- `pi/server.py:210`
- `pi/server.py:502`
- `pi/server.py:550`

Issue:

`POST /api/command` accepts `ARM`, `DISARM`, `TAKEOFF`, `LAND`, `RTL`, `MODE`, and `GOTO` without authentication. The server binds to `0.0.0.0`, so any host that can reach the Pi HTTP port can attempt to control the vehicle.

Impact:

Remote network users can issue safety-critical commands. In a lab or field Wi-Fi network this can become full unauthorized vehicle control.

Recommended fix:

- Add `--host` with default `127.0.0.1`; require explicit `--host 0.0.0.0`.
- Add `--api-token` or `SKYMESHX_PI_TOKEN`.
- Require `Authorization: Bearer <token>` for all `/api/*`, especially `/api/command`.
- Add command allow/deny policy flags for destructive commands.

### SEC-02 Critical: Pi server enables cross-origin telemetry and command exposure

Files:

- `pi/server.py:522`
- `pi/server.py:526`

Issue:

Every response includes `Access-Control-Allow-Origin: *`. Combined with unauthenticated endpoints, arbitrary browser origins can read telemetry/logs and interact with the API if the browser can reach the Pi.

Impact:

Telemetry leakage, log leakage, and possible drive-by command attempts from a malicious web page in the same network context.

Recommended fix:

- Remove CORS by default.
- If needed, add explicit `--cors-origin`.
- Enforce auth before CORS responses.

### SEC-03 High: XSS in Pi dashboard log rendering

Files:

- `pi/server.py:197`
- `pi/server.py:381`

Issue:

MAVLink `STATUSTEXT` is appended to `_log` and rendered into the dashboard using `innerHTML`:

```javascript
el.innerHTML=lines.map(l=>`<span class="log-${l.l}">... ${l.m}</span>`).join('<br>');
```

Impact:

A malicious MAVLink source, simulated autopilot, or compromised flight controller can inject HTML/JavaScript into the dashboard.

Recommended fix:

- Build log entries with `document.createElement()` and `textContent`.
- Whitelist log levels before using them in CSS class names.

### SEC-04 High: Unbounded request body and single-threaded Pi server can be blocked

Files:

- `pi/server.py:504`
- `pi/server.py:555`

Issue:

The handler reads `Content-Length` bytes without a size cap. `HTTPServer` is single-threaded.

Impact:

A slow or large request can block the server and delay status/command handling.

Recommended fix:

- Reject body sizes above a small limit, for example 8 KiB.
- Set socket/request timeouts.
- Consider `ThreadingHTTPServer` if remote access remains supported.

### UI-01 High: UI experiment script execution runs arbitrary Python in-process

Files:

- `tools/ui/context/experiment_context.py:121`
- `tools/ui/context/experiment_context.py:250`
- `tools/ui/context/experiment_context.py:277`
- `skymeshx/control/script_runner.py:145`
- `skymeshx/control/script_runner.py:161`
- `skymeshx/cli/main.py:240`

Issue:

The UI and CLI execute user-provided Python using `exec`. The code runs in the same process with access to Python imports, filesystem, environment variables, and in some paths live drone objects.

Impact:

This is remote-code-execution equivalent if untrusted scripts can be loaded, pasted, downloaded, or shared. It also makes accidental destructive code possible.

Recommended fix:

- Label this feature as trusted-only in UI and docs.
- Default UI script execution to a subprocess sandbox where possible.
- Add a confirmation dialog before executing unsaved/imported code.
- Consider a restricted mission DSL for untrusted scenarios.

### UI-02 High: Path traversal in UI uploaded script operations

Files:

- `tools/ui/context/experiment_context.py:195`
- `tools/ui/context/experiment_context.py:300`
- `tools/ui/context/experiment_context.py:348`
- `tools/ui/context/experiment_context.py:359`

Issue:

`filename` is joined directly with `experiments/uploads` for save, read, and delete operations. Values such as `../other.py` can escape the intended upload directory.

Impact:

QML or a manipulated UI state can overwrite, read, or delete files outside the uploads folder within the process permissions.

Recommended fix:

- Use `Path(filename).name` for uploaded script names.
- Resolve the final path and require it to stay below `_scripts_dir.resolve()`.
- Reject absolute paths and `..` segments.

### UI-03 Medium/High: Broad QML file read/write bridge

Files:

- `tools/ui/context/swarm_context.py:803`
- `tools/ui/context/swarm_context.py:818`
- `tools/ui/context/swarm_context.py:861`

Issue:

`readFile`, `appendFile`, and `writeFile` accept arbitrary paths after stripping `file://`. They create parent directories and read/write directly from QML-exposed slots.

Impact:

Any QML code path, injected QML, or compromised WebEngine/QML bridge behavior that can call these slots can read or write files accessible to the user account.

Recommended fix:

- Split into purpose-specific APIs: `readCsvFile`, `exportLogFile`, `appendSyslog`.
- Restrict log writes to `logs/syslogs`.
- For user-selected exports, require FileDialog-selected paths and validate extension.
- Do not expose generic filesystem primitives to QML.

### UI-04 Medium: WebEngine map loads Leaflet from external CDN without SRI

Files:

- `tools/ui/qml/MapView.qml:86`
- `tools/ui/qml/MapView.qml:376`
- `tools/ui/qml/MapView.qml:377`

Issue:

The QML WebEngine map loads Leaflet CSS/JS from `https://unpkg.com`. There is no bundled copy and no subresource integrity.

Impact:

Supply-chain risk and offline fragility. A compromised CDN or upstream package delivery path can run JavaScript in the WebEngine map context.

Recommended fix:

- Bundle Leaflet assets locally and load them from the app resources.
- If CDN must remain, pin exact version and enforce SRI where supported.
- Add tests/manual checklist for offline map startup.

### UI-05 Medium: WebEngine navigation accepts non-internal URLs

Files:

- `tools/ui/qml/MapView.qml:95`
- `tools/ui/qml/MapView.qml:140`

Issue:

`onNavigationRequested` rejects internal `qrc://pick`, `qrc://boundary-point`, `qrc://solar-row-point`, and `qrc://waypoint-moved` URLs, but accepts all other navigation.

Impact:

External content or accidental links can navigate the embedded map frame away from trusted map HTML. This increases the blast radius of CDN or content injection issues.

Recommended fix:

- Reject all navigation except the known internal `qrc://...` callback schemes and expected tile/CDN requests.
- Use explicit allowlists for schemes and hosts.

### UI-06 Medium: JavaScript string injection risks in `runJavaScript` calls

Files:

- `tools/ui/qml/MapView.qml:32`
- `tools/ui/qml/MapView.qml:336`
- `tools/ui/qml/MapView.qml:343`
- `tools/ui/qml/MapView.qml:355`

Issue:

Several `runJavaScript` calls concatenate strings directly, for example:

```qml
webView.runJavaScript("setSelectedDrone('" + did + "')")
webView.runJavaScript("updateFormation('"+leaderId+"', "+JSON.stringify(positions)+")")
```

Some values currently come from internal models, but the boundary is not enforced.

Impact:

If drone IDs, leader IDs, mission type, or map type become user-controlled or telemetry-derived, JavaScript injection becomes possible inside WebEngine.

Recommended fix:

- Always pass dynamic values through `JSON.stringify`, including scalar strings:

```qml
webView.runJavaScript("setSelectedDrone(" + JSON.stringify(did) + ")")
```

- Validate drone IDs and map types against allowlists.

### UI-07 High: Dangerous flight actions are exposed with immediate UI confirmation signals

Files:

- `tools/ui/context/swarm_context.py:167`
- `tools/ui/context/swarm_context.py:187`
- `tools/ui/context/swarm_context.py:204`
- `tools/ui/context/ros2_context.py:252`
- `tools/ui/context/ros2_context.py:270`
- `tools/ui/context/ros2_context.py:279`

Issue:

The UI exposes arm/disarm/takeoff/land/RTL for MAVLink and ROS2 bridges. Several methods emit confirmation signals immediately after sending the command, not after actual vehicle state confirmation.

Impact:

Operators can receive misleading success feedback. Accidental clicks can trigger fleet-wide commands quickly.

Recommended fix:

- Rename immediate signals to `commandSent` or wait for telemetry/ACK before `Confirmed`.
- Add confirmation dialogs for force-disarm, all-drone commands, and takeoff-all.
- Add per-drone command cooldowns and visible pending/failed states.

### UI-08 Medium: Coordinate and altitude validation is inconsistent before flight commands

Files:

- `tools/ui/context/swarm_context.py:228`
- `tools/ui/context/swarm_context.py:234`
- `tools/ui/context/swarm_context.py:374`
- `tools/ui/context/ros2_context.py:225`
- `tools/ui/context/ros2_context.py:234`

Issue:

UI slots forward coordinates, altitude, NED setpoints, and velocity setpoints directly to backends after type conversion. Range checks and geofence checks are not centralized.

Impact:

Invalid values can propagate to MAVLink/ROS2 control paths. This is especially risky for manual UI entry, map interaction, or malformed QML state.

Recommended fix:

- Create a shared validator for:
  - latitude `[-90, 90]`
  - longitude `[-180, 180]`
  - altitude `[0, configured_max_alt_m]`
  - velocity magnitude limits
  - geofence containment
- Use it in all UI command slots before calling backend methods.

### UI-09 Medium: ROS2 SITL configuration flows into shell-based launcher

Files:

- `tools/ui/context/ros2_context.py:358`
- `tools/ui/context/ros2_context.py:368`
- `tools/ui/context/ros2_context.py:388`
- `tools/ui/context/ros2_context.py:424`
- `skymeshx/simulation/px4_gazebo.py:168`
- `skymeshx/simulation/px4_gazebo.py:171`

Issue:

The UI can set `px4_dir`, `model`, namespace, and ROS2 setup files. On non-Windows, `PX4GazeboCluster` builds a shell string using these values when `ros2_setups` is present.

Impact:

If these fields are influenced by untrusted input, this is command injection. Even in trusted UI use, accidental shell metacharacters can break SITL startup.

Recommended fix:

- Avoid `shell=True`; run a wrapper script with validated arguments.
- If shell is unavoidable, use `shlex.quote`.
- Whitelist model names and namespace patterns.
- Validate setup paths exist and are regular files.

### UI-10 Medium: Bag playback accepts arbitrary paths

Files:

- `tools/ui/context/bag_playback_context.py:74`
- `tools/ui/context/bag_playback_context.py:107`
- `tools/ui/context/bag_playback_context.py:141`
- `tools/ui/context/ros2_context.py:939`

Issue:

Bag playback accepts any existing path and passes it to `ros2 bag info/play`. `playBag` in `ROS2Context` delegates arbitrary `bag_path` to the recorder.

Impact:

This is not shell injection because args are passed as a list, but it can cause the UI to process unexpected files/directories or invoke ROS2 tooling against attacker-controlled paths.

Recommended fix:

- Restrict default playback to the project `bags/` directory.
- Permit external paths only via explicit FileDialog selection.
- Validate bag metadata before playback.

### UI-11 Medium: Updater executes downloaded installer without mandatory independent signature

Files:

- `tools/ui/updater.py:120`
- `tools/ui/updater.py:183`
- `tools/ui/updater.py:399`
- `tools/ui/updater.py:402`

Issue:

The updater downloads a release asset and launches it. SHA256 verification is optional and the `.sha256` file comes from the same release channel as the installer.

Impact:

A compromised GitHub account/release repo can distribute a malicious installer that will be launched by the application.

Recommended fix:

- Require a detached signature verified with a public key embedded in the app.
- Treat missing signature as update failure.
- Pin release repository and asset naming in a single config source.

### UI-12 Medium: Release repository configuration is inconsistent

Files:

- `tools/ui/_version.py:34`
- `tools/installer/inno/skymeshx_gcs.iss:25`

Issue:

The updater uses `joeldjio/skymeshx-releases`; the installer metadata uses `joeldjio/skymeshx-gcs-releases`.

Impact:

Users may check/install updates from the wrong channel. This weakens release governance and makes audit trails harder.

Recommended fix:

- Use one release repository constant.
- Generate installer metadata from the same source as `tools/ui/_version.py`.

### UI-13 Medium: Development license secret is active in product source

Files:

- `tools/ui/_version.py:50`
- `tools/ui/license.py:26`
- `tools/installer/gen_license.py:103`

Issue:

`LICENSE_SECRET` is set to `skymeshx-dev-secret-CHANGE-ME-before-shipping`.

Impact:

Any build shipped with this value allows anyone with source access to mint valid offline license keys.

Recommended fix:

- Rotate before release.
- Add a build-time check that fails if the secret starts with `skymeshx-dev-secret`.
- For stronger licensing, move activation/signing to a server-side flow.

### UI-14 Low/Medium: License and activation state is local-only and user-writable

Files:

- `tools/ui/license.py:137`
- `tools/ui/license.py:145`
- `tools/ui/license.py:163`

Issue:

Trial start and key are stored in a local JSON file under app-local data or home fallback.

Impact:

Local users can reset or manipulate trial state. This is acceptable for casual protection, but not for strong commercial enforcement.

Recommended fix:

- Document as casual protection only.
- If stronger protection is required, use server activation and signed machine-bound grants.

### UI-15 Low: LLM command path sends precise swarm state to external providers

Files:

- `skymeshx/llm/swarm_commander.py:114`
- `skymeshx/llm/swarm_commander.py:214`
- `skymeshx/llm/swarm_commander.py:240`

Issue:

OpenAI/Gemini backends receive current drone positions and natural-language commands.

Impact:

Position and mission intent can leave the local machine when cloud LLM backends are selected.

Recommended fix:

- Add a clear UI/CLI privacy warning before enabling cloud LLM backends.
- Default to `mock` or local `ollama`.
- Redact or coarsen sensitive coordinates when possible.

### UI-16 Low: Logs may include sensitive operational data

Files:

- `tools/ui/context/swarm_context.py:95`
- `tools/ui/context/swarm_context.py:151`
- `tools/ui/context/ros2_context.py:412`
- `tools/ui/context/ros2_context.py:963`

Issue:

Logs include connection strings, local paths, bag paths, namespace details, and positions in several places.

Impact:

Exported logs can leak operational metadata.

Recommended fix:

- Redact credentials in connection strings.
- Avoid logging exact paths unless debug mode is enabled.
- Provide a log-scrub/export option.

## Positive Notes

- `skymeshx/core/connection.py` validates MAVLink connection string formats before connecting.
- `send_raw()` uses a whitelist of MAVLink message types.
- Experiment YAML loading uses `yaml.safe_load`.
- The test architecture is hardware-free, which is good for adding security regression tests.
- ROS2 context management has a dedicated reference-counted context layer.

## Recommended Remediation Plan

### Immediate

1. Lock down `pi/server.py`: localhost default, token auth, CORS off, request size limits.
2. Fix Pi dashboard log rendering with `textContent`.
3. Fix `ExperimentContext` path traversal.
4. Make updater signatures mandatory or disable in-app install for release builds until signing exists.

### Short Term

1. Add shared coordinate/altitude/geofence validation and call it from UI, CLI, Pi API, MAVLink, and ROS2 command paths.
2. Replace generic QML file read/write slots with purpose-specific safe APIs.
3. Bundle Leaflet locally and reject unexpected WebEngine navigation.
4. Rename immediate command confirmation signals or wait for real telemetry/ACK confirmation.

### Medium Term

1. Isolate script execution by default.
2. Remove shell construction in `PX4GazeboCluster`.
3. Add privacy warnings for cloud LLM backends.
4. Add log scrubbing.

## Suggested Security Tests

- `tests/test_pi_server_security.py`
  - rejects `/api/command` without token
  - rejects oversized body
  - does not emit wildcard CORS by default

- `tests/test_ui_path_security.py`
  - rejects `../escape.py` in `saveAndRunScript`
  - rejects absolute paths in uploaded script delete/read helpers

- `tests/test_ui_command_validation.py`
  - rejects invalid lat/lon/alt in UI command slots
  - rejects takeoff altitude above configured max

- `tests/test_map_webengine_security.py`
  - `runJavaScript` string calls use JSON encoding for dynamic strings
  - unexpected navigation URLs are rejected

- `tests/test_updater_security.py`
  - update install fails without signature
  - wrong signature rejects installer

## Release Blockers

Treat the following as release blockers before shipping to users:

1. Unauthenticated Pi flight-command HTTP API.
2. UI path traversal in script upload/read/delete.
3. Optional/weak updater verification.
4. Development license secret in release builds.
5. External WebEngine JavaScript without pinning/bundling.

