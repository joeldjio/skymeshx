# PX4 Frame Conversion Visualization

## Overview

This feature provides real-time visualization of coordinate frame conversions between PX4's NED (North-East-Down) frame and ROS2's ENU (East-North-Up) frame. This is essential for debugging position and velocity data when integrating PX4 with ROS2.

## Frame Conventions

### PX4 NED Frame (North-East-Down)
- **X-axis**: North (positive = north)
- **Y-axis**: East (positive = east)
- **Z-axis**: Down (positive = down, negative = up)
- **Altitude**: Negative values (e.g., -10m = 10m altitude)

### ROS2 ENU Frame (East-North-Up)
- **X-axis**: East (positive = east)
- **Y-axis**: North (positive = north)
- **Z-axis**: Up (positive = up, negative = down)
- **Altitude**: Positive values (e.g., 10m = 10m altitude)

### Conversion Formula
```
ENU = [E, N, U] = [ned_east, ned_north, -ned_down]
NED = [N, E, D] = [enu_north, enu_east, -enu_up]
```

## Features

### 1. Backend Frame Data Tracking

The `PX4ROS2Bridge` class now tracks both NED and ENU coordinates:

```python
# In droneresearch/ros/px4_bridge.py
self.telemetry: dict = {
    # ... existing fields ...
    "ned_north": 0.0,
    "ned_east": 0.0,
    "ned_down": 0.0,
    "enu_east": 0.0,
    "enu_north": 0.0,
    "enu_up": 0.0,
}
```

### 2. ROS2Context Frame Data Access

The `ROS2Context` class provides a slot to retrieve frame data:

```python
@pyqtSlot(str, result="QVariant")
def getFrameData(self, drone_id: str) -> dict:
    """Get frame conversion data for a drone."""
    bridge = self._bridges.get(drone_id)
    if not bridge:
        return {}
    
    telem = bridge.telemetry
    return {
        "ned_north": telem.get("ned_north", 0.0),
        "ned_east": telem.get("ned_east", 0.0),
        "ned_down": telem.get("ned_down", 0.0),
        "enu_east": telem.get("enu_east", 0.0),
        "enu_north": telem.get("enu_north", 0.0),
        "enu_up": telem.get("enu_up", 0.0),
    }
```

### 3. UI Visualization

The ROS2 Panel includes a "Frame Conversion Debug" section with:

#### Text Display
- Side-by-side comparison of NED vs ENU coordinates
- Color-coded: NED (red), ENU (green)
- Real-time updates (100ms refresh rate)

#### 2D Canvas Visualization
- Top-down view showing drone position
- Grid with 10m spacing
- Coordinate axes (North/East)
- Drone position marker (blue circle)
- Scale: 1 pixel = 0.5 meters

## Usage

### 1. Start PX4 SITL with ROS2

```bash
# Terminal 1: Start PX4 SITL
cd ~/PX4-Autopilot
make px4_sitl gz_x500

# Terminal 2: Start MicroXRCEAgent
MicroXRCEAgent udp4 -p 8888
```

### 2. Launch UI and Connect

```bash
# Terminal 3: Launch UI
python -m tools.ui
```

1. Go to **ROS2** tab
2. Enter drone namespace (e.g., `px4_0`)
3. Click **Connect**
4. Scroll down to **Frame Conversion Debug** section

### 3. Observe Frame Data

The visualization shows:
- **NED coordinates** (red text): PX4's native frame
- **ENU coordinates** (green text): ROS2's standard frame
- **2D map**: Top-down view with drone position

### 4. Test with Movement

```bash
# Terminal 4: Send offboard commands
python examples/px4_ros2_offboard.py
```

Watch the frame data update in real-time as the drone moves.

## Example Script

Run the frame conversion demo to understand the conversions:

```bash
python examples/frame_conversion_demo.py
```

This demonstrates:
- Basic NED ↔ ENU conversion
- Altitude sign convention
- Velocity vector conversion
- Body frame conversion (FRD ↔ FLU)
- Roundtrip conversion verification
- Practical flight scenarios

## Testing

Run the frame conversion tests:

```bash
pytest tests/test_frame_conversion.py -v
```

Tests cover:
- Basic conversions
- Roundtrip conversions
- Zero and negative values
- Altitude sign convention
- Position and velocity examples

## Common Issues

### Issue 1: Altitude Sign Confusion

**Problem**: Drone appears to be underground in ENU frame.

**Solution**: Remember that PX4 uses negative altitude:
- PX4 NED: `down = -10.0` (10m altitude)
- ROS2 ENU: `up = 10.0` (10m altitude)

### Issue 2: North/East Swap

**Problem**: Drone position appears rotated 90 degrees.

**Solution**: Check axis mapping:
- NED: `[north, east, down]`
- ENU: `[east, north, up]`
- Note: East and North are swapped!

### Issue 3: Velocity Direction Inverted

**Problem**: Climbing drone shows negative velocity.

**Solution**: Check frame convention:
- PX4 NED: Climbing = negative `vD`
- ROS2 ENU: Climbing = positive `vU`

## API Reference

### Frame Conversion Functions

```python
from droneresearch.ros.px4_bridge import ned_to_enu, enu_to_ned, frd_to_flu

# Convert position from NED to ENU
enu_e, enu_n, enu_u = ned_to_enu(ned_n, ned_e, ned_d)

# Convert position from ENU to NED
ned_n, ned_e, ned_d = enu_to_ned(enu_e, enu_n, enu_u)

# Convert body frame from FRD to FLU
flu_f, flu_l, flu_u = frd_to_flu(frd_f, frd_r, frd_d)
```

### ROS2Context Methods

```python
# Get frame data for a drone
frame_data = ros2_context.getFrameData("px4_0")

# Returns dict with keys:
# - ned_north, ned_east, ned_down
# - enu_east, enu_north, enu_up
```

## Implementation Details

### Backend Changes

1. **px4_bridge.py**: Extended telemetry dict with frame fields
2. **px4_bridge.py**: Modified `_cb_local_pos` to store both NED and ENU
3. **ros2_context.py**: Added `getFrameData()` slot

### UI Changes

1. **ROS2Panel.qml**: Added Frame Conversion Debug section
2. **ROS2Panel.qml**: Text display with color-coded NED/ENU values
3. **ROS2Panel.qml**: Canvas-based 2D visualization with grid and axes

### Test Coverage

- 11 unit tests for frame conversion functions
- Tests for basic conversions, roundtrips, edge cases
- Tests for altitude sign convention
- Tests for position and velocity examples

## Related Documentation

- [PX4 Coordinate Systems](https://docs.px4.io/main/en/ros/external_position_estimation.html#reference-frames-and-ros)
- [ROS REP 103: Standard Units of Measure and Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)
- [PX4 Mission Upload](px4-mission-upload.md)
- [PX4 Mission Monitoring](px4-mission-monitoring.md)

## Troubleshooting

### Visualization Not Updating

1. Check that drone is connected in ROS2 tab
2. Verify telemetry is being received (check Dashboard tab)
3. Check console for errors

### Incorrect Position Display

1. Verify PX4 is publishing `/fmu/out/vehicle_local_position`
2. Check that MicroXRCEAgent is running
3. Restart UI and reconnect

### Canvas Not Rendering

1. Check that Qt3D is properly installed
2. Verify QML Canvas is supported
3. Check browser console for QML errors

## Future Enhancements

Potential improvements:
- 3D visualization with altitude
- Historical trajectory display
- Multiple drone comparison
- Frame conversion calculator tool
- Export frame data to CSV