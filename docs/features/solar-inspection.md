# Solar Park Inspection

Automated solar panel inspection using UAVs with thermal camera integration for hotspot detection.

## Overview

The Solar Park Inspection feature enables systematic inspection of solar panel installations using automated flight patterns with camera triggering and gimbal control. Integration with thermal cameras allows for real-time detection of faulty or damaged panels through hotspot analysis.

## Features

- **Automated Flight Planning**: Generate waypoint patterns for efficient solar panel coverage
- **Camera Control**: Automatic gimbal positioning and camera triggering
- **Thermal Imaging**: Real-time thermal camera integration via ROS2
- **Hotspot Detection**: Automated detection of abnormal temperature patterns
- **Mission Metrics**: Coverage area and time estimation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Solar Inspection System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ SolarParkInspec- │         │ ThermalCamera    │          │
│  │ tionPlanner      │         │ Subscriber       │          │
│  │                  │         │                  │          │
│  │ - plan_inspection│         │ - ROS2 Image     │          │
│  │ - interpolate_row│         │ - Calibration    │          │
│  │ - calculate_area │         │ - FPS tracking   │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
│           │                            │                     │
│           │ Waypoints                  │ Thermal Data        │
│           ▼                            ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ MissionEngine    │         │ ThermalHotspot   │          │
│  │                  │         │ Detector         │          │
│  │ - Upload mission │         │                  │          │
│  │ - Execute        │         │ - detect_hotspots│          │
│  └──────────────────┘         │ - Statistics     │          │
│                                └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Inspection Mission

```python
from skymeshx.control.solar_inspection import (
    SolarParkInspectionPlanner,
    PanelRow,
    InspectionConfig
)
from skymeshx.control.mission import MissionEngine

# Initialize planner
planner = SolarParkInspectionPlanner()
planner.set_home_position(48.137, 11.575)

# Define solar panel rows
rows = [
    PanelRow(
        start=(48.137, 11.575),
        end=(48.138, 11.575),
        width=2.0  # meters
    ),
    PanelRow(
        start=(48.137, 11.576),
        end=(48.138, 11.576),
        width=2.0
    )
]

# Configure inspection parameters
config = InspectionConfig(
    altitude=15.0,              # meters above panels
    gimbal_pitch=-90.0,         # straight down
    overlap=0.3,                # 30% image overlap
    speed=3.0,                  # m/s
    trigger_distance=5.0        # meters between photos
)

# Generate waypoints
waypoints = planner.plan_inspection(rows, config, add_rtl=True)

# Upload and execute mission
mission = MissionEngine(connection)
for wp in waypoints:
    mission.add(wp)
mission.upload()
mission.start()
```

### Thermal Camera Integration

```python
from skymeshx.sensors.thermal_camera import (
    ThermalCameraSubscriber,
    ThermalHotspotDetector
)

# Initialize hotspot detector
detector = ThermalHotspotDetector(
    threshold_temp=80.0,        # °C
    min_hotspot_size=10         # pixels
)

# Callback for thermal images
def on_thermal_image(temp_image, metadata):
    # Detect hotspots
    hotspots = detector.detect_hotspots(temp_image)
    
    # Log findings
    for hotspot in hotspots:
        print(f"Hotspot detected at ({hotspot['center_x']:.1f}, "
              f"{hotspot['center_y']:.1f})")
        print(f"  Temperature: {hotspot['mean_temp']:.1f}°C")
        print(f"  Size: {hotspot['pixel_count']} pixels")

# Start thermal camera subscriber
camera = ThermalCameraSubscriber(
    topic="/thermal/image_raw",
    callback=on_thermal_image,
    calibration_a=0.01,
    calibration_b=-273.15
)

camera.start()
# ... inspection runs ...
camera.stop()
```

### Mission Metrics

```python
# Calculate coverage area
area = planner.calculate_coverage_area(rows, config)
print(f"Coverage area: {area:.1f} m²")

# Estimate mission time
time = planner.estimate_mission_time(rows, config)
print(f"Estimated time: {time:.1f} seconds ({time/60:.1f} minutes)")
```

## Configuration

### InspectionConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `altitude` | float | 15.0 | Flight altitude above panels (meters) |
| `gimbal_pitch` | float | -90.0 | Camera pitch angle (degrees, -90 = down) |
| `gimbal_roll` | float | 0.0 | Camera roll angle (degrees) |
| `gimbal_yaw` | float | 0.0 | Camera yaw angle (degrees) |
| `overlap` | float | 0.3 | Image overlap ratio (0.0-1.0) |
| `speed` | float | 3.0 | Flight speed (m/s) |
| `camera_fov_horizontal` | float | 60.0 | Camera horizontal FOV (degrees) |
| `camera_fov_vertical` | float | 45.0 | Camera vertical FOV (degrees) |
| `trigger_distance` | float | 5.0 | Distance between camera triggers (meters) |

### Thermal Camera Calibration

Thermal cameras output raw 16-bit values that need calibration:

```python
# Linear calibration: temp_celsius = a * raw + b
config = ThermalCameraSubscriber(
    calibration_a=0.01,      # Slope
    calibration_b=-273.15,   # Offset (Kelvin to Celsius)
    min_temp=-40.0,          # Minimum valid temperature
    max_temp=150.0           # Maximum valid temperature
)
```

**Common Calibrations:**
- **FLIR Lepton**: `a=0.01, b=-273.15`
- **FLIR Tau**: `a=0.04, b=-273.15`
- **Seek Thermal**: `a=0.0625, b=-273.15`

## MAVLink Commands

The inspection planner generates the following MAVLink commands:

### Navigation Waypoint (16)
```python
Waypoint(
    lat=48.137,
    lon=11.575,
    alt=15.0,
    cmd=16,  # MAV_CMD_NAV_WAYPOINT
    speed=3.0
)
```

### Gimbal Control (205)
```python
Waypoint(
    lat=48.137,
    lon=11.575,
    alt=15.0,
    cmd=205,  # MAV_CMD_DO_MOUNT_CONTROL
    param1=-90.0,  # Pitch
    param2=0.0,    # Roll
    param3=0.0,    # Yaw
    param7=2.0     # MAV_MOUNT_MODE_MAVLINK_TARGETING
)
```

### Camera Trigger (203)
```python
Waypoint(
    lat=48.137,
    lon=11.575,
    alt=15.0,
    cmd=203,  # MAV_CMD_DO_DIGICAM_CONTROL
    param5=1.0  # Trigger
)
```

## Hotspot Detection

The thermal hotspot detector identifies abnormal temperature patterns:

```python
detector = ThermalHotspotDetector(
    threshold_temp=80.0,
    min_hotspot_size=10
)

hotspots = detector.detect_hotspots(temp_image)

for hotspot in hotspots:
    print(f"Hotspot ID: {hotspot['id']}")
    print(f"Location: ({hotspot['center_x']}, {hotspot['center_y']})")
    print(f"Size: {hotspot['pixel_count']} pixels")
    print(f"Temperature: {hotspot['min_temp']:.1f} - {hotspot['max_temp']:.1f}°C")
    print(f"Mean: {hotspot['mean_temp']:.1f}°C ± {hotspot['std_temp']:.1f}°C")
```

## Frame Conventions

### GPS Coordinates
- Panel rows defined in latitude/longitude (WGS84)
- Waypoints use GPS coordinates for navigation

### Thermal Images
- Input: ROS2 `sensor_msgs/Image` (16-bit raw values)
- Output: NumPy array with temperature in Celsius
- Coordinate system: Image pixels (x=width, y=height)

### Gimbal Angles
- Pitch: -90° (down) to +90° (up)
- Roll: -180° to +180°
- Yaw: 0° (forward) to 360°

## Performance

### Mission Planning
- Waypoint generation: ~1ms per row
- Coverage calculation: ~0.1ms per row
- Time estimation: ~0.1ms per row

### Thermal Processing
- Image calibration: ~5ms for 640x480
- Hotspot detection: ~10-50ms depending on complexity
- Frame rate: Up to 30 FPS (hardware dependent)

## Testing

Run the test suite:

```bash
# Solar inspection planner tests
python -m pytest tests/test_solar_inspection.py -v

# Thermal camera tests
python -m pytest tests/test_thermal_camera.py -v
```

## Examples

### Complete Inspection Workflow

```python
from skymeshx.control.solar_inspection import (
    SolarParkInspectionPlanner,
    PanelRow,
    InspectionConfig
)
from skymeshx.sensors.thermal_camera import (
    ThermalCameraSubscriber,
    ThermalHotspotDetector
)
from skymeshx.control.mission import MissionEngine

# 1. Plan inspection mission
planner = SolarParkInspectionPlanner()
rows = [
    PanelRow(start=(48.137, 11.575), end=(48.138, 11.575)),
    PanelRow(start=(48.137, 11.576), end=(48.138, 11.576))
]
config = InspectionConfig(altitude=15.0, trigger_distance=5.0)
waypoints = planner.plan_inspection(rows, config)

# 2. Setup thermal camera
detector = ThermalHotspotDetector(threshold_temp=80.0)
hotspot_log = []

def on_thermal(temp_image, metadata):
    hotspots = detector.detect_hotspots(temp_image)
    if hotspots:
        hotspot_log.extend(hotspots)
        print(f"Found {len(hotspots)} hotspot(s)")

camera = ThermalCameraSubscriber(
    topic="/thermal/image_raw",
    callback=on_thermal
)
camera.start()

# 3. Execute mission
mission = MissionEngine(connection)
for wp in waypoints:
    mission.add(wp)
mission.upload()
mission.start()
mission.wait_done()

# 4. Analyze results
camera.stop()
print(f"\nInspection complete!")
print(f"Total hotspots detected: {len(hotspot_log)}")
print(f"Coverage area: {planner.calculate_coverage_area(rows, config):.1f} m²")
```

## Troubleshooting

### No Thermal Images Received
- Check ROS2 topic: `ros2 topic list | grep thermal`
- Verify camera is publishing: `ros2 topic echo /thermal/image_raw`
- Check calibration parameters match your camera

### Hotspots Not Detected
- Verify threshold temperature is appropriate
- Check `min_hotspot_size` isn't too large
- Ensure thermal image has sufficient contrast

### Mission Upload Fails
- Verify connection to autopilot
- Check waypoint count doesn't exceed autopilot limit
- Ensure gimbal and camera commands are supported

## References

- [Field Coverage Planning](field-coverage-planning.md)
- [Mission Upload](../setup/px4-mission-upload.md)
- [ROS2 Integration](../setup/px4-sitl.md)
- [MAVLink Protocol](https://mavlink.io/en/messages/common.html)

## See Also

- [`skymeshx.control.solar_inspection`](../api/control.md#solar-inspection)
- [`skymeshx.sensors.thermal_camera`](../api/reference.md#thermal-camera)
- [Phase 4 Implementation Plan](../project/master-implementation-plan-2026.md#phase-4)