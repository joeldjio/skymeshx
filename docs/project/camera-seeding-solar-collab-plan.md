# Camera, Seeding, Solar Collaboration Plan

**Purpose:** Coordinate parallel implementation between Codex and Bob without editing the same resources at the same time.

**Source plan:** `docs/project/comprehensive-camera-seeding-solar-implementation.md`

## Collaboration Model

Codex and Bob do not communicate directly. All progress, blockers, feedback, API needs, and review notes go into:

`docs/project/camera-seeding-solar-collab-feedback.md`

Each agent should write short entries with:

- Date/time
- Agent name
- Files touched
- Progress
- Blockers
- Feedback or API requests for the other agent

## Work Split

Codex owns backend and foundation work.

Bob owns QML, wizard UI, and map overlays.

The split is designed so both agents can work in parallel without touching the same files most of the time.

## Codex Tasks

### 1. Camera Context Foundation

Create:

- `tools/ui/context/camera_context.py`

Provide a QML-facing `CameraContext` with this initial API:

```python
cameraStartStream(source: str) -> bool
cameraStopStream() -> bool
cameraSnapshot() -> bool
cameraStartRecording(path: str) -> bool
cameraStopRecording() -> bool
setCameraProfile(profile: dict) -> bool
getCameraStatus() -> dict
setTempRange(min_c: float, max_c: float) -> bool
setColorPalette(palette: str) -> bool
setHotspotDetection(enabled: bool) -> bool
```

Expose properties/signals useful to QML:

- Current source
- Stream active
- Recording active
- Recording duration
- Frame age
- Dropped frames
- Current profile
- Thermal settings
- Last error/warning

### 2. Backend Camera Delegation

Extend carefully:

- `tools/ui/backend.py`
- `skymeshx/models/observation_uav.py`

Goal:

- Start/stop camera stream through the selected observation drone.
- Start/stop recording.
- Capture snapshots.
- Return camera/gimbal/stream health status.
- Keep all behavior hardware-free when no camera backend is available.

### 3. Capability Registry

Create:

- `skymeshx/models/capabilities.py`

Initial model:

```python
DroneCapabilities
check_mode_requirements(mode, capabilities)
```

Modes:

- Solar inspection
- Seeding
- Mapping

Important rule:

- Missing capabilities should be shown as warnings, not hidden from the UI.

### 4. Tests

Create or extend:

- `tests/test_camera_context.py`
- `tests/test_capability_registry.py`

Tests must stay hardware-free:

- No real MAVLink
- No ROS2
- No SITL
- No real camera

Use fake/stub objects where needed.

### 5. Safety Review Notes

Review but do not refactor without coordination:

- `tools/ui/context/mission_context.py`

Known concern:

- Current Solar/Seeding upload paths appear to upload and then arm/takeoff/start mission.
- The implementation plan requires: upload does not auto-execute.
- This should be documented in the feedback file before changing behavior.

## Bob Tasks

### 1. Camera & Gimbal Control UI

Primary file:

- `tools/ui/qml/panels/GimbalPanel.qml`

Use the future `camera` QML context from Codex.

UI sections:

- Camera source selection
- Stream start/stop
- Snapshot
- Recording start/stop
- Recording indicator
- Camera settings
- Thermal settings
- Camera health/status

### 2. Mission Wizard UI

Primary files:

- `tools/ui/qml/panels/MissionPanel.qml`

Optional new files:

- `tools/ui/qml/panels/SolarInspectionPanel.qml`
- `tools/ui/qml/panels/SeedingPanel.qml`

Solar wizard:

1. Setup
2. Site definition
3. Flight and camera settings
4. Preview and upload

Seeding wizard:

1. Field definition
2. Crop and seed configuration
3. Dispenser configuration
4. Flight parameters
5. Preview and upload
6. Execution monitoring

### 3. Map Overlays

Primary file:

- `tools/ui/qml/MapView.qml`

Add overlays for:

- Solar rows
- Solar trigger points
- Camera footprints
- Seeding rows
- Drop points
- Exclusion zones
- Mission preview path

### 4. Main QML Integration

Primary file:

- `tools/ui/qml/main.qml`

Integrate panels and context usage after Codex exposes stable context properties.

### 5. Feedback to Codex

Bob should write API needs in:

- `docs/project/camera-seeding-solar-collab-feedback.md`

Examples:

- Missing QML property
- Missing slot
- Data format mismatch
- Map overlay format request
- UI warning text requiring backend reason codes

## File Ownership

### Codex Primary Files

- `tools/ui/context/camera_context.py`
- `tools/ui/backend.py`
- `skymeshx/models/observation_uav.py`
- `skymeshx/models/capabilities.py`
- `tests/test_camera_context.py`
- `tests/test_capability_registry.py`
- `docs/project/camera-seeding-solar-collab-feedback.md`

### Bob Primary Files

- `tools/ui/qml/panels/GimbalPanel.qml`
- `tools/ui/qml/panels/MissionPanel.qml`
- `tools/ui/qml/MapView.qml`
- `tools/ui/qml/main.qml`
- `tools/ui/qml/panels/SolarInspectionPanel.qml`
- `tools/ui/qml/panels/SeedingPanel.qml`

### Shared Files Requiring Coordination

- `tools/ui/context/mission_context.py`
- `tools/ui/service_locator.py`
- `tools/ui/context/__init__.py`

If either agent needs to edit a shared file, write an entry in the feedback file first.

## API Contract Draft

QML context name:

```qml
camera
```

Expected QML usage:

```qml
camera.cameraStartStream(source)
camera.cameraStopStream()
camera.cameraSnapshot()
camera.cameraStartRecording(path)
camera.cameraStopRecording()
camera.getCameraStatus()
```

Status object draft:

```json
{
  "source": "Test Source",
  "streamActive": false,
  "recordingActive": false,
  "recordingDurationSec": 0,
  "frameAgeMs": 0,
  "droppedFrames": 0,
  "profile": "RGB Camera",
  "resolution": "1920x1080",
  "fps": 30,
  "hfov": 90,
  "vfov": 60,
  "thermalEnabled": false,
  "hotspotDetection": false,
  "lastError": ""
}
```

## Implementation Order

1. Create collaboration feedback file.
2. Codex defines CameraContext API and tests.
3. Bob builds GimbalPanel against the `camera` context.
4. Bob records missing API needs in feedback file.
5. Codex adjusts backend/context API.
6. Bob builds Solar/Seeding UI flows.
7. Codex adds capability checks and preview data support.
8. Both review `mission_context.py` upload/execute separation.
9. Add tests for the agreed behavior.

## Ground Rules

- Do not auto-start missions after upload.
- Do not call real hardware in tests.
- Do not hide modes when hardware is missing; show warnings instead.
- Do not edit another agent's primary files unless coordinated in the feedback file.
- Keep QML/backend contracts documented before changing them.
- Use the feedback file for blockers and review notes.

