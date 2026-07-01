# Seeding Mission Planner

Status: active feature

Last reviewed: 2026-07-01

The seeding mission planner generates agricultural coverage rows, seed drop
points, and MAVLink servo commands for a seed dispenser. It is designed to work
from both the Python API and the QML ground control station.

The planner is hardware-free: preview generation does not connect to a drone,
does not upload a mission, and never starts a mission. Upload and execution are
separate UI actions.

## Architecture

```text
SeedingPanel.qml
        |
        v
MissionContext.generateSeedingPreview()
        |
        v
SeedingMissionPlanner.generate_seeding_mission_with_preview()
        |
        v
FieldCoveragePlanner + seed drop insertion
        |
        v
Preview dictionary + Waypoint list
        |
        v
MissionContext.uploadSeedingMission()
        |
        v
MissionEngine.clear() / add() / upload()
        |
        v
Explicit Start Mission button starts execution
```

Important boundary:

- `generateSeedingPreview()` returns map/validation data and stores generated
  waypoints for upload.
- `uploadSeedingMission()` only uploads mission items to connected vehicles.
- `startMission()` is the explicit execution action for arming, takeoff, and
  mission start.

## Capabilities

- Draw or provide a field boundary with at least three points.
- Generate parallel coverage rows using the field coverage planner.
- Insert seed drop actions at regular spacing along the path.
- Configure dispenser servo channel, open PWM, close PWM, and drop duration.
- Estimate seed count, seed weight, duration, battery usage, distance, field
  area, and waypoint count.
- Return QML-ready preview data for map overlays.
- Include exclusion-zone overlays in the preview.
- Warn about vehicle waypoint limits, dispenser capacity, drop-rate limits,
  battery estimates, and exclusion-zone limitations.

## Current Limitations

- Exclusion zones are included in the preview and validation warnings, but they
  are not yet carved out of the flight path.
- Large fields are allowed at preview time. If a generated mission exceeds a
  vehicle-specific upload limit, the mission must be split or uploaded to a
  vehicle/firmware configuration that supports the generated mission size.
- Battery and seed usage estimates are first-order planning estimates, not a
  replacement for field validation.

## Python API

```python
from skymeshx.control.field_coverage import FieldBoundary
from skymeshx.control.seeding_planner import (
    DispenserCalibration,
    SeedingConfig,
    SeedingMissionPlanner,
)

planner = SeedingMissionPlanner()
planner.set_home_position(48.1370, 11.5750)

boundary = FieldBoundary(
    corners=[
        (48.1370, 11.5750),
        (48.1370, 11.5760),
        (48.1380, 11.5760),
        (48.1380, 11.5750),
    ]
)

config = SeedingConfig(
    seed_spacing=2.0,
    row_spacing=5.0,
    altitude=10.0,
    speed=3.0,
    servo_channel=9,
    servo_open_pwm=1900,
    servo_close_pwm=1100,
    drop_duration=0.5,
)

calibration = DispenserCalibration(
    seed_capacity=500,
    seed_weight_g=0.05,
    tank_capacity_kg=1.0,
    seeds_per_drop=1,
    max_drop_rate=2.0,
)

preview = planner.generate_seeding_mission_with_preview(
    boundary=boundary,
    config=config,
    calibration=calibration,
    exclusion_zones=[],
    add_rtl=True,
)

data = preview.to_dict()
print(data["estimatedSeedUsage"])
print(data["warnings"])
```

For waypoint-only planning:

```python
waypoints = planner.plan_seeding_mission(
    boundary=boundary,
    seed_spacing=2.0,
    row_spacing=5.0,
    altitude=10.0,
    speed=3.0,
    servo_channel=9,
    servo_open_pwm=1900,
    servo_close_pwm=1100,
    drop_duration=0.5,
    add_rtl=True,
)
```

## Preview Contract

`SeedingMissionPreview.to_dict()` returns:

| Key | Description |
| --- | --- |
| `waypoints` | Full waypoint list as dictionaries with `lat`, `lon`, `alt`, and `cmd` |
| `flightPath` | Navigation-only path for map rendering |
| `flightRows` | Planned seeding rows for row overlays |
| `dropPoints` | Seed drop markers with expected drop IDs |
| `exclusionZones` | User-provided exclusion-zone overlays |
| `estimatedSeedUsage` | Estimated seed count |
| `estimatedSeedWeightKg` | Estimated seed mass |
| `estimatedDuration` | Estimated mission duration in seconds |
| `estimatedBatteryUsage` | Estimated battery percentage |
| `estimatedDistance` | Estimated path distance in meters |
| `fieldArea` | Estimated field area in square meters |
| `estimatedWaypointCount` | Estimated mission item count |
| `warnings` | Non-fatal planning warnings |

`MissionContext.generateSeedingPreview()` adds:

- `valid`
- `errors`
- `validation`

## Mission Item Sequence

For each seed drop, the planner emits a four-item sequence:

1. `MAV_CMD_NAV_WAYPOINT` at the drop position.
2. `MAV_CMD_DO_SET_SERVO` with `servo_open_pwm`.
3. `MAV_CMD_NAV_DELAY` for `drop_duration`.
4. `MAV_CMD_DO_SET_SERVO` with `servo_close_pwm`.

This keeps the generated mission explicit and inspectable in logs and mission
upload traces.

## UI Workflow

1. Open the Mission panel and select Seeding.
2. Draw a field boundary on the map.
3. Optionally draw exclusion zones.
4. Configure spacing, altitude, speed, and dispenser calibration.
5. Generate the preview and inspect rows, drop points, estimates, and warnings.
6. Upload the mission to connected drone(s).
7. Press Start Mission only when the uploaded mission is ready to execute.

## Validation Behavior

Validation returns errors only for conditions that prevent planning, such as
missing home position or invalid configuration.

Warnings are used for conditions that need operator attention:

- Estimated mission size is above the common 700-waypoint vehicle limit.
- Seed usage is near or above dispenser capacity.
- Estimated seed weight exceeds tank capacity.
- Flight speed is too high for the configured drop rate.
- Drop duration may overlap the next seed point.
- Exclusion zones are present but not carved from the path.
- Estimated battery usage is high or above available battery.

## Tests

The seeding tests are hardware-free and use mocked dependencies:

```bash
pytest tests/test_seeding_planner.py -v
pytest tests/test_mission_context_seeding_preview.py -v
```

Important coverage:

- Config validation.
- Servo command parameters.
- Delay command duration.
- Waypoint sequence generation.
- Preview dictionary contract.
- Large-field preview above common vehicle limits.
- MissionContext signal and getter flow.
- Stored boundary and exclusion-zone handling.

## SITL Checklist

Use [docs/testing/sitl-seeding-mission.md](../testing/sitl-seeding-mission.md)
for Linux SITL validation before hardware tests.
