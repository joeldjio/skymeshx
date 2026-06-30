# Seeding, Solar Inspection, Camera and Gimbal Implementation Plan

Date: 2026-06-20

## Scope

This plan defines how to make the seeding and solar inspection features complete, intuitive and technically coherent across UI, API and backend.

The main product problem is not only missing controls. The user must always understand:

- which mode is currently active
- what the drone will do after upload or execution
- which hardware capability is required
- which camera, gimbal or payload action will happen during the mission
- how to cancel or leave the current mode safely

## Literature Inputs

The following local PDF files were provided as reference material:

- `C:\Users\IRUZ\Downloads\1-s2.0-S2772375525007506-main.pdf`
- `C:\Users\IRUZ\Downloads\Modern Agriculture - 2025 - Yumnam - Utilising Drones in Agriculture  A Review on Remote Sensors  Image Processing and.pdf`
- `C:\Users\IRUZ\Downloads\Application_of_drone_in_agriculture_A_review.pdf`
- `C:\Users\IRUZ\Downloads\Drone-based_solar_panel_inspection_using_machine_l (1).pdf`
- `C:\Users\IRUZ\Downloads\epjconf_riact2026_02005.pdf`
- `C:\Users\IRUZ\Downloads\s10846-025-02265-w.pdf`
- `C:\Users\IRUZ\Downloads\SolarPanel-PV-Inspection-Radiometry.pdf`

The plan below is based on the paper topics, existing project documents and the current codebase. Full text extraction was not available in this tool environment, so exact paper-level claims and citations should be verified before turning this into scientific documentation.

## Current Codebase Findings

Existing useful building blocks:

- `skymeshx/control/seeding_planner.py` already generates seeding missions with servo commands, spacing, row spacing, altitude, PWM validation and drop duration.
- `skymeshx/control/solar_inspection.py` already creates solar inspection waypoints, gimbal mount commands and camera trigger commands.
- `skymeshx/sensors/thermal_camera.py` already has a ROS2 thermal image subscription path, calibration hooks and hotspot detection.
- `skymeshx/models/observation_uav.py` already models camera, gimbal, stream and recording actions.
- `tools/ui/qml/panels/GimbalPanel.qml` exists, but currently behaves more like a basic gimbal control panel than a complete camera and payload control center.
- `tools/ui/qml/panels/MissionPanel.qml` exposes mission modes, but seeding and solar need a stronger workflow and clearer previews.

Current gaps:

- Solar inspection does not clearly explain what the drone will do when selected.
- Seeding lacks an end-to-end operator workflow for field boundary, crop/seed settings, dispenser calibration, mission preview and execution.
- There is no complete camera settings UI.
- There is no integrated video stream preview.
- Camera actions, gimbal actions and mission planning are not presented as one coherent workflow.
- Mode switching must remain exclusive: entering solar, seeding, waypoint editing or map drawing must cancel the previous mode.

## Product Model

Each advanced mode should follow the same operator contract:

1. Select mode.
2. Define area or rows on the map.
3. Configure payload and camera.
4. Preview path, actions and estimated duration.
5. Validate safety and hardware capabilities.
6. Upload mission.
7. Execute only after explicit confirmation.
8. Review results and export logs/reports.

Every mode must show a plain summary before upload:

- flight path
- altitude
- speed
- expected waypoints
- estimated duration
- camera/gimbal actions
- payload actions
- required hardware
- known warnings

## Phase 1: Camera and Gimbal Foundation

### Goal

Turn the current gimbal panel into a `Camera & Gimbal` panel. Solar inspection, seeding documentation, mapping and observation workflows should all use this shared camera layer.

### UI Work

Update `tools/ui/qml/panels/GimbalPanel.qml`:

- Add camera source selection:
  - None
  - RGB camera
  - Thermal camera
  - Multispectral camera
  - RTSP stream
  - ROS2 image topic
  - local test source
- Add stream controls:
  - start stream
  - stop stream
  - snapshot
  - start recording
  - stop recording
- Add camera settings:
  - resolution
  - frames per second
  - horizontal FOV
  - vertical FOV
  - trigger mode: distance, time, waypoint, manual
  - storage folder
- Add thermal settings:
  - calibration profile
  - temperature unit
  - hotspot threshold
  - emissivity
  - reflected temperature
  - solar irradiance note or field
- Add status display:
  - stream connected
  - recording active
  - frame age
  - dropped frames
  - selected camera profile

### Backend Work

Add a new context:

- `tools/ui/context/camera_context.py`

Responsibilities:

- own camera settings exposed to QML
- validate stream URLs and topic names
- start/stop stream through backend/model layer
- start/stop recording
- capture snapshot
- expose camera health
- expose FOV and trigger settings to mission planners

Extend:

- `tools/ui/backend.py`
- `skymeshx/models/observation_uav.py`

Required API methods:

- `cameraStartStream(source: str) -> bool`
- `cameraStopStream() -> bool`
- `cameraSnapshot() -> bool`
- `cameraStartRecording(path: str) -> bool`
- `cameraStopRecording() -> bool`
- `setCameraProfile(profile: dict) -> bool`
- `getCameraStatus() -> dict`

### Safety Rules

- Do not auto-start cloud upload.
- Do not auto-record without explicit operator action or mission setting.
- RTSP and file paths must be validated.
- Camera failure must not crash the mission planner.
- Mission upload must be blocked only when the selected mission requires camera capture and no valid camera is available.

## Phase 2: Solar Inspection Mode

### What Solar Mode Should Do

Solar inspection mode should mean:

The drone flies structured passes along selected solar panel rows, points the gimbal/camera at the panel surface, captures RGB and/or thermal images at configured intervals, geotags the captures, detects possible hotspots or damaged modules and exports an inspection report.

The UI must show this before upload.

### UI Workflow

Create a guided workflow inside `MissionPanel.qml` or a dedicated `SolarInspectionPanel.qml`:

1. Setup
   - inspection name
   - drone
   - camera profile
   - thermal enabled or disabled
2. Site Definition
   - draw solar farm boundary
   - draw panel rows
   - import rows from CSV, GeoJSON or KML later
3. Flight Parameters
   - altitude
   - speed
   - row overlap
   - row direction
   - safe turn distance
   - return-to-launch behavior
4. Camera and Gimbal
   - RGB or thermal source
   - gimbal pitch
   - trigger distance
   - expected image footprint
   - thermal calibration profile
5. Preview
   - row path
   - trigger points
   - camera footprints
   - estimated images
   - estimated duration
   - warnings
6. Upload and Execute
   - upload mission
   - arm/start only after separate confirmation
7. Review
   - image list
   - hotspot markers
   - report export

### Map Features

Add overlays:

- solar rows
- flight pass lines
- camera footprint rectangles
- trigger points
- skipped rows
- hotspot markers after analysis

The map should make the mission understandable without reading documentation.

### Backend Work

Extend `skymeshx/control/solar_inspection.py`:

- include camera profile in `InspectionConfig`
- include capture trigger strategy
- include expected image count
- include report metadata
- return a rich preview object, not only waypoints
- validate FOV, altitude and overlap together

Add a domain object:

- `SolarInspectionMission`

Fields:

- boundary
- panel rows
- flight path
- camera actions
- gimbal actions
- trigger points
- expected captures
- warnings
- export metadata

### Analysis and Report

Use `skymeshx/sensors/thermal_camera.py` as the first thermal backend.

Report output:

- JSON for machine use
- CSV for anomaly list
- HTML or Markdown report for operator review

Each finding should include:

- image id
- GPS coordinate
- panel row id
- temperature statistics if thermal is available
- severity
- confidence
- thumbnail path

### Important Solar Inspection Notes

Radiometric inspection is more than taking a thermal picture. The UI should capture or remind the operator about:

- time of day
- irradiance or weather conditions
- wind
- camera calibration
- emissivity
- reflected temperature
- focus and image blur
- altitude and FOV

## Phase 3: Seeding Mode

### What Seeding Mode Should Do

Seeding mode should mean:

The drone flies over a defined field and triggers a seed dispenser at calculated points or along calculated rows. The operator configures crop/seed type, spacing, dispenser behavior, altitude, speed and exclusion zones before upload.

The UI must show exactly where drops happen and which servo/channel commands will be sent.

### UI Workflow

Create a guided workflow inside `MissionPanel.qml` or a dedicated `SeedingPanel.qml`:

1. Field
   - draw field boundary
   - draw exclusion/no-drop zones
   - choose row direction
2. Crop and Seed
   - crop type
   - seed spacing
   - row spacing
   - seed rate
   - optional prescription map
3. Dispenser
   - servo channel
   - open PWM
   - close PWM
   - drop duration
   - seeds per pulse
   - tank capacity
   - bench test button
4. Flight
   - altitude
   - speed
   - turn behavior
   - RTL behavior
5. Preview
   - flight path
   - drop points
   - density heatmap
   - expected seed count
   - estimated mission time
   - hardware warnings
6. Upload and Execute
   - upload mission
   - execute only after explicit confirmation

### Backend Work

Extend `skymeshx/control/seeding_planner.py`:

- support exclusion zones
- support row direction
- support variable-rate prescription maps
- estimate seed count
- estimate seed tank usage
- split very large missions safely
- return preview data separately from MAVLink mission items

Add:

- `SeedPrescription`
- `SeedDispenserProfile`
- `SeedingMissionPreview`

### Dispenser Safety

Seeding has real actuator risk. Add validation:

- servo channel is configured
- PWM values are within safe range
- open and close values are not equal
- drop duration is within configured bounds
- bench test is disabled while armed unless explicitly allowed
- no drop command outside field boundary
- no drop command inside exclusion zones

## Phase 4: Shared Mission and Mode Architecture

### Capability Registry

Add a central capability model:

- camera available
- thermal camera available
- gimbal available
- seeding dispenser available
- mission upload available
- live stream available
- recording available

Each mode declares requirements:

- Solar inspection requires mission planning, gimbal and at least one camera.
- Radiometric solar inspection requires thermal camera and calibration profile.
- Seeding requires mission planning and dispenser.
- Mapping requires camera.
- Manual waypoint mode requires mission planning only.

If a requirement is missing, the UI should explain what is missing and disable execution, not hide the whole mode.

### Command Ownership

Add a command ownership rule:

- only one active mode may own map editing
- only one active mode may own mission generation
- only one active mode may own camera automation
- only one active mode may own gimbal automation
- manual gimbal override should pause mission camera automation or require confirmation

This extends the current map mode mutex work.

### Mode State Machine

Every complex mode should use:

- `Idle`
- `Editing`
- `Configured`
- `PreviewReady`
- `Uploaded`
- `Executing`
- `Review`
- `Cancelled`
- `Error`

ESC behavior:

- while editing: cancel active drawing/editing
- while previewing: return to editing
- while executing: do not silently stop mission; show safe action options
- while modal dialog is open: close dialog first

## Phase 5: UI Improvements

### Navigation

Recommended panels:

- Mission
- Seeding
- Solar Inspection
- Camera & Gimbal
- Telemetry
- Safety
- Logs/Reports

If panels remain combined, use tabs inside `MissionPanel.qml`:

- Waypoints
- Survey
- Seeding
- Solar
- Upload

### Preview First

Both seeding and solar should prioritize preview:

- path visible
- payload actions visible
- warnings visible
- estimated outputs visible

The operator should not need to guess what the mode does.

### Copy and Labels

Use action labels that explain the operation:

- `Draw field boundary`
- `Draw solar row`
- `Preview seed drops`
- `Preview inspection passes`
- `Upload mission`
- `Start stream`
- `Start recording`
- `Bench test dispenser`

Avoid vague labels such as only `Solar Mode` or `Seeding Mode` without an adjacent summary.

## Phase 6: Tests

Follow the repository rule: tests must be hardware-free.

### Unit Tests

Add tests for:

- solar inspection config validation
- expected solar trigger count
- solar FOV footprint calculation
- seeding exclusion zones
- seeding seed count estimate
- dispenser PWM validation
- camera profile validation
- capability requirement checks

### UI/Mode Tests

Add or extend tests for:

- switching from seeding to solar cancels seeding edit mode
- switching from solar to waypoint mode cancels solar drawing
- ESC cancels active edit mode
- camera settings are readable by solar inspection planner
- seeding upload is disabled without dispenser capability
- solar radiometric mode is disabled without thermal capability

### Integration Tests

Mock:

- drone connection
- camera stream
- thermal camera
- mission upload
- seeding dispenser

Verify:

- mission preview does not upload
- upload does not execute
- camera failure creates warning
- report export works with mocked captures

## Phase 7: Suggested Implementation Order

1. Stabilize mode mutex and ESC behavior across map, mission, seeding and solar.
2. Add `CameraContext` and expand `GimbalPanel.qml` into `Camera & Gimbal`.
3. Add camera profile objects and connect them to solar planner.
4. Convert solar inspection into a guided preview workflow.
5. Add solar map overlays for rows, trigger points and camera footprints.
6. Add solar report export from mocked captures.
7. Convert seeding into a guided preview workflow.
8. Add dispenser profile, bench test and safety validation.
9. Add seeding density/drop preview overlays.
10. Add capability registry and mode requirement checks.
11. Add hardware-free tests for all mode transitions and planner validation.

## Minimum Viable Commercial Feature Set

For a strong first commercial version, prioritize:

- Solar inspection wizard
- Camera & Gimbal panel with live stream and recording
- Thermal hotspot detection
- Inspection report export
- Seeding wizard
- Dispenser calibration and bench test
- Mission preview with warnings
- Capability checks
- Mode mutex and safe cancellation

## Definition of Done

The feature set is intuitive when:

- selecting solar mode immediately explains the inspection mission
- selecting seeding mode immediately explains the seeding mission
- the operator can see all drone actions before upload
- camera and gimbal behavior is visible in preview
- seeding drop points are visible before upload
- solar image trigger points and footprints are visible before upload
- missing hardware is shown as a clear warning
- upload never implies automatic execution
- ESC reliably leaves the active edit mode
- changing mode cancels the previous mode cleanly

