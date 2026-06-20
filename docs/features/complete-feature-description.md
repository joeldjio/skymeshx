# SkyMeshX Complete Feature Description

Date: 2026-06-20

SkyMeshX is a drone research and ground-control platform for single-drone operation, multi-drone swarm coordination, mission planning, safety monitoring, ROS2/PX4 integration, experiment execution, and field-oriented workflows such as coverage, seeding, and solar inspection.

This document describes the complete feature surface of the software at a product level. It is intended as a central reference for documentation, release planning, open-source/commercial packaging, and user-facing descriptions.

## 1. Platform Overview

SkyMeshX combines four major layers:

- Core SDK for drone and swarm control.
- Ground Control Station UI built with PySide6 and QML.
- Mission, safety, experiment, and data tooling.
- Robotics integrations for MAVLink, ArduPilot, PX4, ROS2, and uXRCE-DDS.

The system is designed to support both simulated and real vehicles. Core tests are hardware-free and use mocks, while examples and UI workflows can connect to SITL or hardware through MAVLink and ROS2.

## 2. Core Drone Control

The core drone layer provides the basic vehicle operations expected from a research ground station.

Main capabilities:

- Connect to MAVLink endpoints over TCP, UDP, serial, or COM ports.
- Resolve connection ports from CLI flags, environment variables, or defaults.
- Track connection state, telemetry state, and autopilot type.
- Arm and disarm vehicles.
- Take off to a target altitude.
- Land in place.
- Return to launch.
- Change flight mode.
- Send GPS goto commands.
- Set speed and other command-long actions.
- Send selected raw MAVLink messages through a whitelist.
- Reconnect after connection loss.
- Surface command acknowledgements and negative acknowledgements.

Relevant modules:

- `skymeshx/core/connection.py`
- `skymeshx/core/telemetry.py`
- `skymeshx/core/fsm.py`
- `skymeshx/sdk/drone.py`
- `skymeshx/autopilot/mavlink/backend.py`

## 3. Telemetry and State Management

SkyMeshX keeps a live telemetry model for each vehicle.

Tracked telemetry includes:

- GPS latitude and longitude.
- Absolute and relative altitude.
- Roll, pitch, and yaw.
- Groundspeed, airspeed, climb rate, and velocity components.
- Battery voltage, current, and percentage.
- GPS fix type and satellite count.
- Flight mode and armed state.
- Autopilot type and vehicle type.
- Firmware and board metadata where available.

State management features:

- Finite-state machine for drone lifecycle.
- Rejected transition counting.
- Safe state tracking.
- Mission and formation bookkeeping.
- UI-facing telemetry snapshots.
- Per-drone connection status.

## 4. Command Line Interface

The `skymeshx` CLI provides scriptable access to the core platform.

Commands include:

- `connect`: connect and print a telemetry snapshot.
- `status`: print current state and telemetry.
- `arm` and `disarm`: arm/disarm with optional force mode.
- `takeoff`: take off to a specified altitude.
- `land`: land in place.
- `rtl`: return to launch.
- `mode`: change flight mode.
- `goto`: fly to a GPS coordinate.
- `run`: execute a trusted Python script with drone access.
- `experiment run`: run a configured experiment scenario.
- `ui`: launch the graphical ground control station.

The default MAVLink endpoint is `tcp:127.0.0.1:5762`, matching raw ArduCopter SITL. MAVProxy-aggregated SITL commonly uses `tcp:127.0.0.1:5760`.

## 5. Swarm Control

SkyMeshX supports multi-drone operations through the SDK, backend, and GCS UI.

Swarm capabilities:

- Add and remove multiple drones.
- Assign unique drone IDs.
- Connect, disconnect, and reconnect individual drones.
- Run parallel connect, arm, disarm, takeoff, land, RTL, and mode operations.
- Select one or more mission target drones.
- Dispatch missions to multiple drones.
- Offset shared waypoint routes into separate lanes for multi-drone execution.
- Track connected, active, and selected drones.
- Manage leader/follower roles.

Formation capabilities:

- Line formation.
- V formation.
- Circle formation.
- Grid formation.
- Wedge-style formations.
- Diamond and letter-style custom layouts in UI logic.
- Configurable spacing and formation size.
- Leader-follower updates.
- Boids-inspired flocking behavior.
- Consensus and behavior-tree demonstration controls.

Relevant modules:

- `skymeshx/sdk/swarm_api.py`
- `skymeshx/sdk/formations.py`
- `skymeshx/models/coordinator_uav.py`
- `tools/ui/context/swarm_context.py`
- `tools/ui/qml/panels/SwarmPanel.qml`

## 6. Mission Planning and Upload

The mission system supports both simple waypoint workflows and more advanced mission generation.

Mission features:

- Manual waypoint lists.
- Map-click waypoint creation.
- Latitude, longitude, and altitude waypoint entry.
- Mission target selection.
- Mission upload to autopilot.
- Mission progress tracking.
- Preflight validation.
- Configurable timeouts.
- Async mission upload for UI responsiveness.
- Mission cancellation and lock coordination.
- Multi-drone dispatch with waypoint lane offsets.
- Mission completion notification.

Mission safety and validation:

- Empty mission rejection.
- Coordinate validation hooks.
- Mission target tracking.
- Collision-aware mission coordination through safety modules.
- Preflight validation for PX4 missions.

Relevant modules:

- `skymeshx/control/mission.py`
- `skymeshx/control/mission_validation.py`
- `skymeshx/ros/px4_mission.py`
- `tools/ui/context/mission_context.py`
- `tools/ui/qml/panels/MissionPanel.qml`

## 7. Ground Control Station UI

The GCS is built with PySide6, Qt Quick, and QML. It provides a panel-based interface for operators and researchers.

Main panels:

- Dashboard panel.
- Map view.
- Swarm panel.
- Mission panel.
- Safety panel.
- ROS2 panel.
- Gimbal panel.
- Flight log panel.
- Experiment panel.
- Log panel.
- Help panel.

Global UI features:

- Header with connection controls.
- Serial port discovery.
- Drone selection.
- Live telemetry indicators.
- Instrument bar and flight instruments.
- Theme components.
- Update and license banners.
- Global log handler.
- QML context services.

UI context bridge:

- `TelemetryContext`
- `SwarmContext`
- `SafetyContext`
- `MissionContext`
- `ROS2Context`
- `ExperimentContext`
- `BagPlaybackContext`
- `EscapeContext`
- `ServiceLocator`

## 8. Interactive Map

The map is one of the main operator surfaces.

Map features:

- Embedded WebEngine map.
- Leaflet-based map rendering.
- OpenStreetMap tile layer.
- Street, dark, satellite, hybrid, and topographic modes.
- Live drone marker updates.
- Selected drone visualization.
- Flight tracks.
- Waypoint markers.
- Dispatched waypoint layer.
- Geofence visualization.
- Field boundary drawing.
- Solar row drawing.
- Coverage waypoint visualization.
- Collision prediction overlays.
- Thermal hotspot markers.
- Formation and swarm visualization.

Map workflows:

- Click to add waypoint.
- Drag waypoint positions.
- Draw field boundary.
- Draw solar panel rows.
- Center map on drone.
- Fly-to selected coordinates.

## 9. Safety Systems

SkyMeshX includes several safety modules for research and operational support.

APF safety filter:

- Artificial Potential Field collision avoidance.
- Local NED position handling.
- Positive altitude-above-ground convention for `Pose3D.z`.
- Repulsive forces between drones.
- Obstacle repulsion.
- Goal attraction.
- Geofence clipping.
- Separation checks.
- Optional filter loop running at a configured rate.

Adaptive APF:

- Velocity-aware safety margins.
- Wind-speed adjustment.
- GPS uncertainty adjustment.
- Per-drone adaptive margin tracking.

Collision prediction:

- Time-to-collision estimation.
- Pairwise drone risk analysis.
- Velocity-based future position projection.
- Waypoint-aware prediction.
- Severity classification.

Battery monitoring:

- Battery sample history.
- Battery status estimation.
- Low and critical thresholds.
- Return-to-launch recommendation.
- Estimated power consumption rate.
- Persistent battery history.

Perception-enhanced avoidance:

- Point-cloud obstacle updates.
- Voxel-based obstacle map.
- Obstacle timeout cleanup.
- Nearby obstacle lookup.
- APF integration with perception obstacles.

Relevant modules:

- `skymeshx/safety/apf.py`
- `skymeshx/safety/collision_predictor.py`
- `skymeshx/safety/battery_monitor.py`
- `skymeshx/safety/perception_avoidance.py`
- `tools/ui/context/safety_context.py`
- `tools/ui/qml/panels/SafetyPanel.qml`

## 10. ROS2 and PX4 Integration

SkyMeshX supports PX4-native ROS2 workflows through uXRCE-DDS rather than MAVLink-over-ROS.

ROS2/PX4 capabilities:

- Shared `rclpy` context management.
- PX4 bridge lifecycle management.
- Namespace-aware bridge start/stop.
- Native PX4 topic subscriptions.
- Vehicle command publishing.
- Offboard mode activation.
- NED and ENU frame handling.
- FRD and FLU attitude/body-frame conversion helpers.
- Position and velocity setpoints.
- PX4 mission upload and monitoring.
- Formation control through ROS2/PX4 modules.
- Connection status and reconnect info.

PX4 topic convention:

- PX4 to ROS2: `/fmu/out/*`
- ROS2 to PX4: `/fmu/in/*`

Relevant modules:

- `skymeshx/ros/context.py`
- `skymeshx/ros/px4_bridge.py`
- `skymeshx/ros/px4_mission.py`
- `skymeshx/ros/px4_formation.py`
- `tools/ui/context/ros2_context.py`
- `tools/ui/qml/panels/ROS2Panel.qml`

## 11. SITL and Simulation

Simulation support is designed for development, demos, tests, and research scenarios.

Simulation features:

- ArduPilot SITL helper.
- PX4 Gazebo helper.
- PX4 multi-vehicle automation.
- Micro XRCE-DDS Agent startup.
- PX4 model and world configuration.
- Namespace setup for multiple vehicles.
- Log streaming from SITL processes.
- Replay helpers.
- Mock backend support for hardware-free examples.

Relevant modules:

- `skymeshx/simulation/sitl.py`
- `skymeshx/simulation/px4_gazebo.py`
- `skymeshx/simulation/replay.py`
- `examples/px4_sitl_automation.py`
- `examples/px4_multi_vehicle.py`

## 12. Field Coverage Planning

Field coverage tools generate waypoint patterns for area scanning.

Coverage capabilities:

- Polygon field boundary support.
- Parallel-line coverage.
- Spiral pattern.
- Grid pattern.
- Zigzag pattern.
- Line spacing configuration.
- Altitude configuration.
- Overlap-aware planning.
- Mission time estimation.
- Local NED conversion for pattern generation.
- Multi-drone coverage allocation.

Use cases:

- Agriculture monitoring.
- Field survey.
- Repeated inspection passes.
- Research coverage experiments.

Relevant modules:

- `skymeshx/control/field_coverage.py`
- `docs/features/field-coverage-planning.md`

## 13. Seeding Mission Planning

The seeding planner extends coverage planning with seed-drop mission points.

Capabilities:

- Generate seed drop waypoints.
- Configure seed spacing and drop altitude.
- Integrate seed points with coverage paths.
- Add servo/dispenser command support through mission items.
- Validate mission inputs.
- Prepare upload-ready mission plans.

Use cases:

- Agricultural reseeding.
- Environmental restoration research.
- Controlled payload-drop experiments.

Relevant modules:

- `skymeshx/control/seeding_planner.py`
- `docs/features/seeding-mission-planner.md`

## 14. Solar Inspection

Solar inspection workflows support automated inspection of photovoltaic fields.

Capabilities:

- Solar row definition.
- Row-based mission generation.
- Panel inspection path planning.
- Thermal hotspot representation.
- Thermal camera integration hooks.
- Hotspot detection helpers.
- UI visualization of panel rows and hotspots.

Use cases:

- Solar farm inspection.
- Thermal anomaly detection.
- Panel-level data collection.
- Research into automated inspection planning.

Relevant modules:

- `skymeshx/control/solar_inspection.py`
- `skymeshx/sensors/thermal_camera.py`
- `tools/ui/qml/panels/MissionPanel.qml`
- `docs/features/solar-inspection.md`

## 15. Sensors and Perception

SkyMeshX includes optional sensor integrations.

Thermal camera features:

- ROS2 image subscription.
- Thermal frame processing.
- Temperature calibration hooks.
- Frame-rate statistics.
- Hotspot detection.

Depth camera features:

- ROS2 point-cloud subscription.
- Point-cloud callback support.
- Statistics and runtime status.
- Integration with perception avoidance.

Relevant modules:

- `skymeshx/sensors/thermal_camera.py`
- `skymeshx/sensors/depth_camera.py`

## 16. ESCAPE and Exploration Features

Exploration and ESCAPE-related modules support mapping, allocation, and obstacle-aware planning.

Capabilities:

- Distributed occupancy map.
- Voxel updates and cleanup.
- Remote map merge.
- Consensus-style map handling.
- Frontier bridge integration.
- Distributed allocation.
- Auction-based task assignment.
- ESCAPE UI context for obstacle and voxel visualization.

Relevant modules:

- `skymeshx/mapping/distributed_map.py`
- `skymeshx/exploration/distributed_allocation.py`
- `skymeshx/exploration/frontier_bridge.py`
- `skymeshx/exploration/vswarm_bridge.py`
- `tools/ui/context/escape_context.py`

## 17. Experiment Framework

The experiment framework supports repeatable research scenarios.

Capabilities:

- Scenario definition.
- Parameter sweeps.
- Repeated trial execution.
- Scenario result recording.
- Result summaries.
- CSV and structured output export.
- QML experiment runner.
- Trusted Python script execution for local experiments.
- Script timeout and cooperative stop support.

Relevant modules:

- `skymeshx/experiment/scenario.py`
- `skymeshx/experiment/manager.py`
- `skymeshx/experiment/metrics.py`
- `tools/ui/context/experiment_context.py`
- `tools/ui/qml/panels/ExperimentPanel.qml`

## 18. Data Logging, Flight Logs, and ROS2 Bags

SkyMeshX supports operational and research logging.

Logging features:

- JSONL event logging.
- Per-drone event logs.
- Async logger queue.
- Dropped-log tracking.
- Flight log view.
- CSV export helpers.
- Global UI logs.
- System log directory handling.

ROS2 bag features:

- Start and stop recording selected topics.
- Compression options such as zstd, lz4, or none.
- List recorded bags.
- Bag metadata display.
- Bag playback.
- Playback rate control.
- Playback progress display.
- Bag compression benchmark tooling.

Relevant modules:

- `skymeshx/data/logger.py`
- `skymeshx/ros/bag_recorder.py`
- `tools/ui/context/bag_playback_context.py`
- `tools/ui/qml/panels/FlightLogPanel.qml`
- `docs/features/bag-compression-benchmark.md`

## 19. Gimbal and Observation UAV Features

Observation UAV models extend the generic drone model with camera and gimbal behavior.

Capabilities:

- Gimbal point commands.
- Gimbal target tracking.
- Gimbal home command.
- Gimbal state reporting.
- Camera stream lifecycle hooks.
- Recording lifecycle hooks.
- Detection callbacks.
- ROS image publication hooks.

Relevant modules:

- `skymeshx/models/observation_uav.py`
- `tools/ui/qml/panels/GimbalPanel.qml`

## 20. Communication and Swarm Protocol

SkyMeshX includes communication structures for swarm coordination.

Capabilities:

- Swarm message handling.
- Communication statistics.
- Drone-to-drone coordination primitives.
- Distributed map and allocation support.
- Consensus and auction testing hooks.

Relevant modules:

- `skymeshx/communication/swarm_protocol.py`
- `skymeshx/exploration/distributed_allocation.py`

## 21. LLM-Assisted Swarm Commands

The LLM module translates natural-language commands into waypoint intents.

Backends:

- Mock backend for deterministic offline tests.
- Local Ollama backend.
- OpenAI backend.
- Gemini backend.

Capabilities:

- Build prompt from current drone positions.
- Parse JSON waypoint responses.
- Apply APF safety filtering to generated targets.
- Return raw and filtered waypoints.
- Record command history.

Use cases:

- Research into natural-language drone control.
- Offline demonstrations using the mock backend.
- Local LLM experiments with Ollama.

Relevant modules:

- `skymeshx/llm/swarm_commander.py`
- `examples/llm_swarm_control.py`

## 22. Raspberry Pi Server

The Pi server is a lightweight HTTP and MAVLink bridge intended for constrained Raspberry Pi deployments.

Capabilities:

- Stdlib-only HTTP server.
- MAVLink connection to serial, TCP, or UDP endpoints.
- Telemetry polling.
- REST status endpoint.
- REST telemetry endpoint.
- REST log endpoint.
- REST command endpoint.
- Inline dashboard.
- Demo mode.

Design target:

- Raspberry Pi 1 class hardware.
- Low memory footprint.
- Minimal dependencies: `pymavlink` and `pyserial`.

Relevant files:

- `pi/server.py`
- `pi/README_PI.md`
- `pi/install.sh`
- `pi/droneresearch.service`

## 23. Installer, Updater, and Licensing

The project includes packaging infrastructure for desktop distribution.

Installer features:

- Windows installer build script.
- PyInstaller specs for CLI and GCS bundles.
- Inno Setup scripts.
- Linux Debian build script.
- Branding asset generation.
- License file bundling.

Updater features:

- GitHub release check.
- Platform-specific asset detection.
- Download progress.
- Optional SHA256 verification.
- Installer launch flow.

Licensing features:

- Offline trial state.
- Offline license key validation.
- HMAC-based license key format.
- License activation UI.
- License status banner.

Relevant files:

- `tools/installer/build.ps1`
- `tools/installer/build_linux_deb.sh`
- `tools/installer/specs/`
- `tools/installer/inno/`
- `tools/ui/updater.py`
- `tools/ui/license.py`
- `tools/ui/_version.py`

## 24. Security Features and Hardening

Security-related capabilities include both implemented features and active hardening documentation.

Implemented/security-aware features:

- Connection string validation.
- Raw MAVLink message whitelist.
- Hardware-free test mocks.
- Lazy imports for optional high-risk dependencies.
- ROS2 context reference counting.
- License audit documentation.
- Security baseline documentation.
- Security remediation plan.
- Dedicated security tests under `tests/security`.

Active hardening areas:

- Pi server authentication and CORS.
- UI path security.
- License secret validation.
- WebEngine dependency hardening.
- Updater signature verification.
- Command validation and geofence enforcement.

Relevant docs:

- `docs/security/SECURITY_BASELINE.md`
- `docs/security/SECURITY_REMEDIATION_PLAN.md`
- `docs/security/SECURITY_AUDIT_FULL_2026-06-20.md`

## 25. Internationalization and UI Text

SkyMeshX includes translation resources.

Capabilities:

- Qt translation files.
- English translation resource.
- QML text prepared with `qsTr` in many UI areas.
- Foundation for multi-language UI.

Relevant files:

- `skymeshx/i18n/translations/uavresearch_en.ts`
- `skymeshx/i18n/translations/uavresearch_en.qm`

## 26. Testing Features

The test suite is designed to be hardware-free by default.

Testing capabilities:

- Fake MAVLink connection fixtures.
- Fake telemetry fixtures.
- Fake MAV message fixtures.
- Unit tests for control, safety, SDK, ROS context, UI contexts, and mission workflows.
- Security tests for path handling, Pi server behavior, and license-secret validation.
- E2E test scaffolding for UI workflows.
- Pytest markers for slow tests.

Important testing convention:

- Tests should not require real MAVLink, ROS2, SITL, or hardware unless explicitly marked and isolated.

Relevant files:

- `tests/conftest.py`
- `tests/security/`
- `pytest.ini`
- `pyproject.toml`

## 27. Open Source and Commercial Packaging

SkyMeshX can be packaged as an open-core product.

Open-source-appropriate features:

- Core SDK.
- CLI.
- Basic simulation support.
- Safety primitives.
- Mission primitives.
- Hardware-free tests.
- Basic examples and documentation.

Commercial-appropriate features:

- Pro GCS.
- Signed installers.
- Auto-updater.
- License management.
- Enterprise security.
- Advanced fleet operations.
- Mission approval workflows.
- Audit logging and compliance reports.
- Priority support and custom integrations.

See:

- `docs/project/open-source-commercial-feature-split.md`

## 28. Example Workflows

### First SITL Mission

1. Start ArduCopter SITL on `tcp:127.0.0.1:5762`.
2. Launch the GCS.
3. Add a drone with ID `UAV_1`.
4. Add map waypoints.
5. Enable APF safety checks.
6. Start the mission.
7. Watch telemetry, map markers, and logs.

### Multi-Drone Formation

1. Add multiple drones with unique IDs.
2. Connect all drones.
3. Select a leader.
4. Choose formation type and spacing.
5. Arm and take off.
6. Start formation following.
7. Monitor separation and collision warnings.

### Field Coverage Mission

1. Draw or define a field boundary.
2. Choose coverage pattern.
3. Configure altitude, spacing, and overlap.
4. Generate waypoints.
5. Validate mission.
6. Upload and execute mission.

### Solar Inspection Mission

1. Define solar panel rows.
2. Configure inspection altitude and path settings.
3. Generate row-following waypoints.
4. Run inspection flight.
5. Review thermal hotspots and logs.

### ROS2/PX4 Offboard Test

1. Start PX4 SITL with uXRCE-DDS.
2. Start ROS2 bridge for a namespace.
3. Confirm `/fmu/out/*` telemetry.
4. Activate offboard mode.
5. Send NED position or velocity setpoints.
6. Stop offboard mode and land.

## 29. Feature Status Categories

Suggested labels for planning:

- Stable: core MAVLink, telemetry, CLI basics, many safety primitives.
- Active development: QML GCS, mission UI, ROS2 panels, security hardening.
- Research: LLM control, distributed allocation, ESCAPE/perception workflows.
- Commercialization: installer, updater, license, enterprise security.

## 30. Summary

SkyMeshX is more than a basic ground station. Its feature set spans:

- Drone control.
- Swarm coordination.
- Mission planning.
- Safety and collision avoidance.
- Field workflows.
- ROS2/PX4 integration.
- Simulation and SITL.
- Experiment automation.
- Data logging and replay.
- Sensor integration.
- UI-based operations.
- Packaging, licensing, and security hardening.

The strongest product direction is to keep the core platform open and use the commercial version for the operational features that matter most in real deployments: a polished GCS, secure updates, advanced safety, auditability, fleet operations, and support.

