# SITL Checklist: Solar Inspection

Status: active test checklist

Last reviewed: 2026-07-01

Use this checklist for Linux PX4/Gazebo or ArduPilot SITL validation of the
solar inspection workflow. The goal is to validate panel-row drawing, preview
generation, camera trigger metadata, gimbal commands, upload/start separation,
and trace artifacts.

## Preconditions

- Linux host with PX4 SITL + Gazebo or another supported SITL setup.
- ROS2 Humble environment available if PX4 ROS2 bridge, topic health, bags, or
  camera streams are part of the test.
- SkyMeshX installed from the current checkout.
- QML UI starts with `python -m tools.ui`.
- A simulator model with camera/gimbal support is preferred, for example a PX4
  Gazebo x500 gimbal/camera profile.

Recommended PX4 setup:

```bash
source /opt/ros/humble/setup.bash
source /path/to/px4_msgs_ws/install/setup.bash

MicroXRCEAgent udp4 -p 8888

cd /path/to/PX4-Autopilot
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500_gimbal
```

Recommended trace setup:

1. Start a trace session with scenario name `sitl_solar_mission`.
2. Start PX4 bridge topic monitoring for the vehicle namespace.
3. If needed, start a ROS2 bag recording for mission, vehicle status, camera,
   and gimbal topics.

Trace bundles are written to:

```text
trace_runs/<timestamp>_sitl_solar_mission/
```

Expected files:

```text
manifest.json
ui_events.jsonl
mission_trace.jsonl
ros2_topic_health.json
```

## Test Steps

### 1. Connect the simulator

1. Start SkyMeshX with `python -m tools.ui`.
2. Open the ROS2 panel if PX4 bridge validation is part of the run.
3. Confirm namespace, world profile, video port, and model are correct.
4. Connect the vehicle and confirm telemetry.
5. Confirm map position matches the simulator home position.

### 2. Check capabilities

1. Open the Mission panel.
2. Select Solar Inspection.
3. Confirm camera/gimbal capability checks are visible.
4. Thermal camera may warn if not available; this should not block visual
   solar planning.

### 3. Draw panel rows

1. Start solar row drawing.
2. Draw at least one row with two map clicks.
3. Draw additional rows if needed.
4. Confirm row overlays remain visible.

### 4. Generate a solar preview

1. Set altitude, speed, camera field of view, overlap, trigger distance or
   trigger time, and gimbal pitch.
2. Generate the preview.

Expected UI result:

- Panel rows are visible.
- Flight path is visible.
- Camera trigger points are visible.
- Footprint polygons are visible for trigger points.
- Estimates are shown for duration, battery, image count, storage, and
  coverage area.
- Warnings are shown for thermal-disabled, trigger gaps, low/high altitude,
  coarse GSD, battery, or narrow footprint cases.

### 5. Upload the mission

1. Press Upload.
2. Confirm the UI reports a successful upload.
3. Confirm upload does not arm, take off, or start AUTO/mission mode by itself.

Expected behavior:

- Upload clears existing mission items.
- Upload adds generated solar inspection items.
- Upload transfers the mission to the connected vehicle.
- Execution remains blocked until Start Mission is pressed.

### 6. Start and observe

1. Press Start Mission after upload.
2. Observe path following, gimbal orientation, and camera trigger behavior.
3. Monitor waypoint tracking and topic health.
4. If a video stream is configured, start it only when needed and confirm the UI
   remains responsive.
5. Abort or RTL when the test objective is complete.

## What To Save For Review

After the run, keep these artifacts:

- `trace_runs/<timestamp>_sitl_solar_mission/manifest.json`
- `trace_runs/<timestamp>_sitl_solar_mission/ui_events.jsonl`
- `trace_runs/<timestamp>_sitl_solar_mission/mission_trace.jsonl`
- `trace_runs/<timestamp>_sitl_solar_mission/ros2_topic_health.json`
- Any ROS2 bag recorded for the run
- Relevant `logs/syslogs/*.txt`
- Vehicle telemetry CSV/JSONL logs from `logs/`
- Notes about camera stream source, UDP port, and whether the map or gimbal
  panel displayed the stream

## Pass Criteria

- Row drawing works for one or more rows.
- Preview contains trigger points and footprint polygons.
- Gimbal and camera trigger mission items are generated.
- Upload succeeds without automatically starting the mission.
- Start Mission is required for execution.
- Trace contains mission upload/start/abort and waypoint-tracking events where
  applicable.
- ROS2 topic health is exported when ROS2 tracing is active.
- UI remains responsive while preview overlays and optional video stream status
  are active.

## Known Follow-Up Items

- Live thermal hotspot overlays depend on available ROS2 thermal image topics
  and UI integration.
- Advanced obstacle-aware row transitions are outside the current solar mission
  planner.
