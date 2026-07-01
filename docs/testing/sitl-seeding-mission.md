# SITL Checklist: Seeding Mission

Status: active test checklist

Last reviewed: 2026-07-01

Use this checklist for Linux SITL validation of the seeding workflow before any
hardware test. The goal is to prove that the UI, mission preview, upload path,
explicit start action, and trace artifacts all work together.

## Preconditions

- Linux host with ArduPilot SITL or PX4 SITL available.
- SkyMeshX installed from the current checkout.
- QML UI starts with `python -m tools.ui`.
- A vehicle is reachable from the GCS.
- For ArduPilot SITL, the default raw endpoint is `tcp:127.0.0.1:5762`.
- For PX4 SITL, start the PX4 bridge and keep namespace/ports recorded in the
  trace manifest.

Recommended trace setup:

1. Open the ROS2 or Log/Trace tooling in the UI.
2. Start a trace session with scenario name `sitl_seeding_mission`.
3. If ROS2 is part of the scenario, start a bag recording with the mission
   preset or the relevant `/fmu/out/*` topics.

Trace bundles are written to:

```text
trace_runs/<timestamp>_sitl_seeding_mission/
```

Expected files:

```text
manifest.json
ui_events.jsonl
mission_trace.jsonl
ros2_topic_health.json
```

If bag recording is enabled, the bag path should be visible in the UI and
referenced by the trace/session data.

## Test Steps

### 1. Start the simulator

ArduPilot example:

```bash
sim_vehicle.py -v ArduCopter
```

PX4 example:

```bash
source /opt/ros/humble/setup.bash
source /path/to/px4_msgs_ws/install/setup.bash

MicroXRCEAgent udp4 -p 8888

cd /path/to/PX4-Autopilot
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500
```

### 2. Connect from the UI

1. Start SkyMeshX with `python -m tools.ui`.
2. Connect the vehicle.
3. Confirm telemetry is updating.
4. Confirm the map marker is close to the simulator home position.

### 3. Generate a seeding preview

1. Open the Mission panel.
2. Select Seeding mode.
3. Draw a field boundary with at least three points.
4. Optional: draw an exclusion zone.
5. Set a realistic seed spacing and row spacing.
6. Generate the preview.

Expected UI result:

- Field boundary is visible.
- Coverage rows are visible.
- Seed drop points are visible.
- Estimates are shown for seed usage, duration, battery, distance, and waypoint
  count.
- Large missions show warnings instead of blocking preview generation.
- If exclusion zones are present, a warning explains that they are preview
  overlays and are not carved from the path yet.

### 4. Upload the mission

1. Press Upload.
2. Confirm the UI reports a successful upload.
3. Do not expect the vehicle to arm, take off, or enter mission mode after
   upload.

Expected behavior:

- Upload clears existing mission items.
- Upload adds generated seeding items.
- Upload transfers the mission to the connected vehicle.
- The drone remains in its current mode until Start Mission is pressed.

### 5. Start and observe

1. Press Start Mission only after upload is complete.
2. Confirm the vehicle arms/takes off/starts according to the current mission
   start workflow and simulator state.
3. Observe waypoint tracking and path following.
4. Abort or RTL when the test objective is complete.

## What To Save For Review

After the run, keep these artifacts:

- `trace_runs/<timestamp>_sitl_seeding_mission/manifest.json`
- `trace_runs/<timestamp>_sitl_seeding_mission/ui_events.jsonl`
- `trace_runs/<timestamp>_sitl_seeding_mission/mission_trace.jsonl`
- `trace_runs/<timestamp>_sitl_seeding_mission/ros2_topic_health.json`
- Any ROS2 bag recorded for the run
- Relevant `logs/syslogs/*.txt`
- Vehicle telemetry CSV/JSONL logs from `logs/`

## Pass Criteria

- Preview generation succeeds without hardware.
- Preview contains flight rows and seed drop points.
- Large fields are not rejected by a fixed planner limit.
- Upload succeeds without automatically starting the mission.
- Start Mission is required for execution.
- Mission trace contains upload/start/abort events where applicable.
- ROS2 topic health is exported when ROS2 tracing is active.

## Known Follow-Up Items

- Path clipping around exclusion zones is not implemented yet.
- Very large generated missions may require mission splitting depending on the
  vehicle firmware and upload limits.
