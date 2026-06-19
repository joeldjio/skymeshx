# Frame Conventions in SkyMeshX

This document describes the coordinate frame conventions used throughout the SkyMeshX platform and how to convert between them.

## Overview

The platform uses multiple coordinate frames depending on the context:

1. **NED (North-East-Down)** - Used by PX4, ArduPilot, and most flight controllers
2. **ENU (East-North-Up)** - Used by ROS2 and geographic visualization tools
3. **FRD (Forward-Right-Down)** - Body frame used by PX4
4. **FLU (Forward-Left-Up)** - Body frame used by ROS2

## Coordinate Frame Definitions

### NED (North-East-Down)
- **X-axis**: Points North
- **Y-axis**: Points East
- **Z-axis**: Points Down (positive = below origin)
- **Used by**: PX4, ArduPilot, MAVLink, field coverage planning
- **Altitude convention**: Positive Z = below ground level

### ENU (East-North-Up)
- **X-axis**: Points East
- **Y-axis**: Points North
- **Z-axis**: Points Up (positive = above origin)
- **Used by**: ROS2, geographic tools, visualization
- **Altitude convention**: Positive Z = above ground level

### FRD (Forward-Right-Down) - Body Frame
- **X-axis**: Points Forward (nose direction)
- **Y-axis**: Points Right (starboard)
- **Z-axis**: Points Down
- **Used by**: PX4 body frame commands

### FLU (Forward-Left-Up) - Body Frame
- **X-axis**: Points Forward (nose direction)
- **Y-axis**: Points Left (port)
- **Z-axis**: Points Up
- **Used by**: ROS2 body frame commands

## Conversion Functions

### Position Frame Conversions

#### NED → ENU
```python
from skymeshx.ros.px4_bridge import ned_to_enu

# Convert NED coordinates to ENU
north, east, down = 10.0, 20.0, 30.0  # 10m North, 20m East, 30m Down
enu_east, enu_north, enu_up = ned_to_enu(north, east, down)
# Result: (20.0, 10.0, -30.0) = 20m East, 10m North, 30m Up
```

**Formula**: `[E, N, U] = [East, North, -Down]`

#### ENU → NED
```python
from skymeshx.ros.px4_bridge import enu_to_ned

# Convert ENU coordinates to NED
east, north, up = 20.0, 10.0, -30.0  # 20m East, 10m North, 30m Up
ned_north, ned_east, ned_down = enu_to_ned(east, north, up)
# Result: (10.0, 20.0, 30.0) = 10m North, 20m East, 30m Down
```

**Formula**: `[N, E, D] = [North, East, -Up]`

### Body Frame Conversions

#### FRD → FLU
```python
from skymeshx.ros.px4_bridge import frd_to_flu

# Convert FRD body frame to FLU
forward, right, down = 1.0, 2.0, 3.0  # 1m Forward, 2m Right, 3m Down
flu_forward, flu_left, flu_up = frd_to_flu(forward, right, down)
# Result: (1.0, -2.0, -3.0) = 1m Forward, 2m Left, 3m Up
```

**Formula**: `[F, L, U] = [Forward, -Right, -Down]`

This is a π (180°) rotation around the X-axis (forward axis).

## Module-Specific Conventions

### Safety Module (`skymeshx/safety/`)
- **APF (Artificial Potential Field)**: Uses NED with **positive z_up** (altitude above ground)
  - Input: `Pose3D(x=North, y=East, z=altitude_above_ground)`
  - Filter inverts z internally for NED calculations
- **CollisionPredictor**: Uses NED with standard convention
  - `DroneState(x=North, y=East, z=Down)`

### Field Coverage (`skymeshx/control/field_coverage.py`)
- Uses **local NED** coordinates relative to home position
- GPS coordinates converted to NED for planning
- Waypoints generated in NED, then converted back to GPS

### ROS2 Bridges (`skymeshx/ros/`)
- **PX4Bridge**: Automatically converts between PX4 (NED/FRD) and ROS2 (ENU/FLU)
- **PX4FormationController**: Uses NED with positive altitude for formation offsets
- All conversions handled transparently

### Exploration (`skymeshx/exploration/`)
- **FrontierBridge**: Uses local NED for odometry and carrot poses
- **VSwarmBridge**: Converts body-frame velocities to NED for navigation

## Common Pitfalls

### 1. Altitude Sign Convention
**Problem**: Mixing positive-up and positive-down conventions

```python
# ❌ WRONG: Mixing conventions
ned_down = 10.0  # 10m below origin
altitude_agl = ned_down  # WRONG! Should be negative

# ✅ CORRECT: Explicit conversion
ned_down = 10.0  # 10m below origin
altitude_agl = -ned_down  # 10m above ground level
```

### 2. Parameter Order Confusion
**Problem**: Using generic (x, y, z) instead of semantic names

```python
# ❌ CONFUSING: What does x, y, z mean?
result = convert_frame(x, y, z)

# ✅ CLEAR: Semantic parameter names
result = ned_to_enu(north, east, down)
```

### 3. Frame Mismatch in Calculations
**Problem**: Performing calculations in mixed frames

```python
# ❌ WRONG: Mixing NED and ENU
ned_pos = (10.0, 20.0, 30.0)
enu_vel = (1.0, 2.0, 3.0)
result = ned_pos + enu_vel  # WRONG! Different frames

# ✅ CORRECT: Convert to same frame first
ned_pos = (10.0, 20.0, 30.0)
enu_vel = (1.0, 2.0, 3.0)
ned_vel = enu_to_ned(*enu_vel)
result = tuple(p + v for p, v in zip(ned_pos, ned_vel))
```

## Testing Frame Conversions

The platform includes comprehensive tests for frame conversions:

```bash
# Run frame conversion tests
pytest tests/test_frame_conversion.py -v
```

Tests verify:
- Mathematical correctness of conversions
- Roundtrip consistency (NED→ENU→NED)
- Consistency between modules
- Altitude sign conventions
- Zero coordinate handling

## Best Practices

1. **Always use semantic parameter names** (`north`, `east`, `down`) instead of generic (`x`, `y`, `z`)
2. **Document the frame** in function docstrings and variable names
3. **Convert at boundaries** - keep internal calculations in one frame
4. **Test conversions** - verify roundtrip consistency
5. **Use provided functions** - don't implement conversions manually

## References

- PX4 Frame Conventions: https://docs.px4.io/main/en/ros/external_position_estimation.html
- ROS REP 103 (Standard Units): https://www.ros.org/reps/rep-0103.html
- ROS REP 105 (Coordinate Frames): https://www.ros.org/reps/rep-0105.html