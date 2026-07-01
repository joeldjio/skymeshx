# Solar Inspection

Status: active feature

Last reviewed: 2026-07-01

Solar inspection generates waypoint missions for flying along photovoltaic panel
rows with gimbal orientation and camera trigger commands. The feature is built
for preview-first operation: the operator can inspect panel rows, trigger
points, image footprints, estimates, and warnings before upload or execution.

## Architecture

```text
SolarInspectionPanel.qml
        |
        v
MissionContext.startDrawingSolarRows()
        |
        v
MissionContext.generateSolarPreview()
        |
        v
SolarParkInspectionPlanner.generate_solar_mission_with_preview()
        |
        v
Panel rows + camera trigger points + footprint polygons
        |
        v
MissionContext.uploadSolarMission()
        |
        v
MissionEngine.clear() / add() / upload()
        |
        v
Explicit Start Mission button starts execution
```

Important boundary:

- Preview generation is hardware-free and does not upload or execute anything.
- Upload only transfers mission items to connected vehicles.
- Mission execution happens only after the operator presses Start Mission.

## Capabilities

- Draw or provide one or more solar panel rows.
- Configure altitude, speed, overlap, trigger distance, camera field of view,
  and gimbal pitch.
- Generate navigation waypoints along each panel row.
- Add `MAV_CMD_DO_MOUNT_CONTROL` commands for gimbal orientation.
- Add `MAV_CMD_DO_DIGICAM_CONTROL` commands for image capture.
- Generate QML-ready camera trigger points with expected image IDs.
- Generate footprint polygons for each trigger point.
- Estimate duration, battery usage, image count, storage, and coverage area.
- Warn about coverage gaps, footprint width, altitude, GSD, battery, and
  missing thermal-camera support.
- Support thermal-enabled preview metadata and storage estimates.

## Current Limitations

- The mission planner generates row-following inspection paths. Advanced
  obstacle-aware row transitions are not part of this planner.
- Battery, storage, and GSD values are planning estimates.
- Thermal processing is available through `skymeshx.sensors.thermal_camera`,
  but live hotspot overlays depend on ROS2 camera topics and UI integration.
- Image footprint polygons are first-order ground projections based on altitude
  and configured camera FOV.

## Python API

```python
from skymeshx.control.solar_inspection import (
    InspectionConfig,
    PanelRow,
    SolarParkInspectionPlanner,
)

rows = [
    PanelRow(
        start=(48.1370, 11.5750),
        end=(48.1380, 11.5750),
        width=2.0,
    ),
    PanelRow(
        start=(48.1370, 11.5755),
        end=(48.1380, 11.5755),
        width=2.0,
    ),
]

config = InspectionConfig(
    altitude=15.0,
    gimbal_pitch=-90.0,
    gimbal_roll=0.0,
    gimbal_yaw=0.0,
    overlap=0.3,
    speed=3.0,
    camera_fov_horizontal=60.0,
    camera_fov_vertical=45.0,
    trigger_distance=5.0,
)

planner = SolarParkInspectionPlanner()
preview = planner.generate_solar_mission_with_preview(
    panel_rows=rows,
    config=config,
    add_rtl=True,
    thermal_enabled=True,
)

data = preview.to_dict()
print(data["totalImages"])
print(data["triggerPoints"][0]["footprint"])
```

For waypoint-only planning:

```python
waypoints = planner.plan_inspection(rows, config, add_rtl=True)
```

## Preview Contract

`SolarMissionPreview.to_dict()` returns:

| Key | Description |
| --- | --- |
| `waypoints` | Full waypoint list as dictionaries with `lat`, `lon`, `alt`, and `cmd` |
| `triggerPoints` | Camera trigger markers with gimbal angle, footprint, and expected image ID |
| `flightPath` | Navigation-only path for map rendering |
| `estimatedDuration` | Estimated mission duration in seconds |
| `estimatedBatteryUsage` | Estimated battery percentage |
| `totalImages` | Number of expected images |
| `storageRequired` | Estimated storage in MB |
| `coverageArea` | Estimated inspected area in square meters |
| `warnings` | Non-fatal planning warnings |

`MissionContext.generateSolarPreview()` adds:

- `valid`
- `errors`
- `validation`

The QML wrapper accepts both direct planner parameter names and UI aliases such
as `panelRows`, `gimbalAngle`, `cameraHFOV`, `cameraVFOV`, `triggerTime`, and
`thermalEnabled`. If trigger distance is non-positive and trigger time is set,
the context converts trigger time to distance using `speed * triggerTime`.

## Mission Item Sequence

For every interpolated point along a row, the planner emits:

1. `MAV_CMD_NAV_WAYPOINT` at the inspection position.
2. `MAV_CMD_DO_MOUNT_CONTROL` at the first point of each row.
3. `MAV_CMD_DO_DIGICAM_CONTROL` to trigger image capture.

If `add_rtl=True`, a final `MAV_CMD_NAV_RETURN_TO_LAUNCH` item is appended.

## Thermal Camera Integration

Thermal camera support is optional and lazy-loaded. The implementation lives in
`skymeshx.sensors.thermal_camera`:

- `ThermalCameraSubscriber` subscribes to ROS2 thermal image topics.
- `ThermalHotspotDetector` detects hotspot candidates in thermal arrays.

Solar capability checks use the capability registry. A thermal camera is
recommended for hotspot detection, but visual solar inspection can still be
planned without it; validation will include a warning when thermal is disabled.

## UI Workflow

1. Open the Mission panel and select Solar Inspection.
2. Verify camera/gimbal capability warnings in Step 1.
3. Draw one or more panel rows on the map.
4. Configure altitude, speed, overlap, trigger mode, camera FOV, and gimbal
   pitch.
5. Generate the preview and inspect flight path, trigger points, footprints,
   storage, battery, and warnings.
6. Upload the mission to connected drone(s).
7. Press Start Mission only when the uploaded mission is ready to execute.

## Validation Behavior

Validation errors stop planning, for example an empty row list or invalid
camera footprint.

Warnings flag operator decisions:

- Trigger distance may leave image gaps.
- Camera footprint is narrower than a panel row.
- Altitude may be too low for clearance or too high for detail.
- Ground sample distance may be too coarse.
- Estimated battery usage is high or above available battery.
- Thermal camera is disabled.

## Tests

The solar inspection tests are hardware-free and use mocked dependencies:

```bash
pytest tests/test_solar_inspection.py -v
pytest tests/test_mission_context_solar_preview.py -v
pytest tests/test_thermal_camera.py -v
pytest tests/test_capability_registry.py -v
```

Important coverage:

- Panel row and config validation.
- Waypoint, gimbal, and camera trigger generation.
- Trigger spacing.
- Preview dictionary contract.
- Footprint polygon generation.
- Thermal-enabled preview warnings.
- MissionContext signal and getter flow.
- QML wizard aliases.

## SITL Checklist

Use [docs/testing/sitl-solar-mission.md](../testing/sitl-solar-mission.md)
for Linux PX4/Gazebo validation before hardware tests.
