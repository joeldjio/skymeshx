# Seeding Mission Planner

**Status:** ✅ Implemented (Phase 3.3)  
**Version:** v0.4.0  
**Last Updated:** 2026-06-17

## Overview

The Seeding Mission Planner extends the Field Coverage system with automated seed dispensing capabilities for agricultural UAV operations. It generates waypoint missions that combine coverage patterns with servo-controlled seed drops at precise intervals.

## Features

### Core Capabilities

- **Automated Seed Placement**: Interpolates seed drop points along coverage paths based on configurable spacing
- **Servo Control Integration**: Uses MAVLink `MAV_CMD_DO_SET_SERVO` commands for seed dispenser actuation
- **Waypoint Optimization**: Removes duplicate waypoints and validates mission constraints
- **Visual Feedback**: Green plant icons on map showing seed drop locations
- **Mission Validation**: Pre-upload checks for waypoint limits and spacing requirements

### Technical Specifications

- **Maximum Waypoints**: 700 (ArduPilot limit)
- **Minimum Waypoint Spacing**: 1.0m
- **Servo Channels**: 1-16 (configurable)
- **PWM Range**: 900-2100 µs
- **Seed Spacing**: 1-100m (configurable)

## Architecture

### Components

```
droneresearch/control/
├── field_coverage.py       # Base coverage planning
└── seeding_planner.py      # Seeding mission extension
    ├── SeedingConfig       # Configuration dataclass
    ├── SeedingMissionPlanner  # Main planner class
    └── plan_seeding_mission() # Mission generation
```

### Data Flow

```
Field Boundary → Coverage Waypoints → Seed Interpolation → Servo Commands → Mission Upload
```

## Usage

### Python API

```python
from droneresearch.control.seeding_planner import (
    SeedingMissionPlanner,
    SeedingConfig
)

# Configure seeding parameters
config = SeedingConfig(
    seed_spacing=5.0,        # meters between seeds
    servo_channel=9,         # servo output channel
    servo_open_pwm=1900,     # PWM to open dispenser
    servo_close_pwm=1100,    # PWM to close dispenser
    dispense_duration=0.5,   # seconds to keep open
    wait_after_drop=0.2      # seconds to wait after closing
)

# Create planner
planner = SeedingMissionPlanner()

# Generate seeding mission
waypoints = planner.plan_seeding_mission(
    field_boundary=[(lat1, lon1), (lat2, lon2), ...],
    home_position=(home_lat, home_lon, home_alt),
    coverage_config=coverage_config,
    seeding_config=config
)

# Upload to drone
mission_engine.upload(waypoints)
```

### UI Workflow

1. **Enable Seeding Mode**
   - Open Mission Panel
   - Toggle "Enable Seeding" checkbox
   - Seeding configuration form appears

2. **Configure Parameters**
   - **Seed Spacing**: Distance between seed drops (1-100m)
   - **Servo Channel**: Output channel for dispenser (1-16)
   - **Open PWM**: Pulse width to open dispenser (900-2100µs)
   - **Close PWM**: Pulse width to close dispenser (900-2100µs)
   - **Dispense Duration**: Time to keep dispenser open (0.1-5.0s)
   - **Wait After Drop**: Delay after closing (0.0-2.0s)

3. **Generate Mission**
   - Click "Generate Mission" button
   - System validates field boundary and parameters
   - Waypoints appear on map with green seed icons

4. **Preview & Validate**
   - Review seed placement on map
   - Check waypoint count (must be ≤700)
   - Adjust seed_spacing if needed

5. **Upload & Execute**
   - Click "Upload Mission" button
   - System performs pre-flight validation
   - Mission uploads to selected drone(s)
   - Click "Start Mission" to begin

## Configuration

### SeedingConfig Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `seed_spacing` | float | 1.0-100.0 | 5.0 | Distance between seed drops (meters) |
| `servo_channel` | int | 1-16 | 9 | Servo output channel |
| `servo_open_pwm` | int | 900-2100 | 1900 | PWM value to open dispenser (µs) |
| `servo_close_pwm` | int | 900-2100 | 1100 | PWM value to close dispenser (µs) |
| `dispense_duration` | float | 0.1-5.0 | 0.5 | Time to keep dispenser open (seconds) |
| `wait_after_drop` | float | 0.0-2.0 | 0.2 | Delay after closing dispenser (seconds) |

### Coverage Integration

Seeding missions use the same coverage patterns as standard field coverage:
- Parallel Lines (default)
- Spiral
- Grid
- Zigzag

All coverage parameters (line_spacing, altitude, speed, overlap) apply to seeding missions.

## Mission Structure

### Waypoint Sequence

For each seed drop point:

```
1. NAV_WAYPOINT (lat, lon, alt, speed, hold=dispense_duration)
2. DO_SET_SERVO (channel, servo_open_pwm)
3. DO_SET_SERVO (channel, servo_close_pwm)
```

### Example Mission

```python
# Seed drop at (48.137, 11.575, 20m)
waypoints = [
    Waypoint(
        lat=48.137, lon=11.575, alt=20.0,
        speed=5.0, hold=0.5,  # Wait 0.5s at waypoint
        cmd=16,  # MAV_CMD_NAV_WAYPOINT
        radius=2.0
    ),
    Waypoint(
        lat=48.137, lon=11.575, alt=20.0,
        speed=0.0, hold=0.0,
        cmd=183,  # MAV_CMD_DO_SET_SERVO
        param1=9,    # channel
        param2=1900  # open PWM
    ),
    Waypoint(
        lat=48.137, lon=11.575, alt=20.0,
        speed=0.0, hold=0.0,
        cmd=183,  # MAV_CMD_DO_SET_SERVO
        param1=9,    # channel
        param2=1100  # close PWM
    ),
    # ... next seed drop ...
]
```

## Validation

### Pre-Generation Checks

- Field boundary must have ≥3 points
- Home position required
- Seed spacing must be ≥1.0m
- Servo channel must be 1-16
- PWM values must be 900-2100µs

### Pre-Upload Checks

- Total waypoints ≤700 (ArduPilot limit)
- Waypoint spacing ≥1.0m (except DO commands)
- Valid GPS coordinates
- Altitude >0

### Automatic Adjustments

If estimated waypoints exceed 700:
```
Recommended seed_spacing = (total_distance / (700 / 3))
```

Example: For 2000m field with 5m spacing:
- Estimated waypoints: ~1200 (exceeds limit)
- Recommended spacing: 8.6m
- Adjusted waypoints: ~696 ✓

## Smart Mission Upload

The system automatically adapts upload behavior based on drone state:

### State-Based Upload

```python
if drone.fsm_state in ["FLYING", "MISSION"]:
    # Drone already airborne
    mission.start()  # Just start mission
else:
    # Drone on ground
    drone.arm()
    drone.takeoff(altitude)
    mission.start()
```

### Benefits

- No redundant ARM/TAKEOFF commands for flying drones
- Seamless mission switching during flight
- Reduced upload time
- Better state management

## Troubleshooting

### Common Issues

**Issue: "Too many waypoints (>700)"**
- **Cause**: Seed spacing too small for field size
- **Solution**: Increase seed_spacing parameter
- **Formula**: `seed_spacing ≥ total_distance / 233`

**Issue: "Too close to previous waypoint (0.00m < 1m)"**
- **Cause**: Duplicate waypoints or invalid interpolation
- **Solution**: System automatically skips segments <1m
- **Note**: Should not occur in v0.4.0+

**Issue: "Seeds only at field boundary"**
- **Cause**: Old interpolation logic (pre-v0.4.0)
- **Solution**: Update to v0.4.0+ with fixed interpolation

**Issue: "Servo not actuating"**
- **Cause**: Incorrect PWM values or channel
- **Solution**: 
  - Verify servo channel (1-16)
  - Test PWM range (typically 1000-2000µs)
  - Check servo power supply
  - Verify MAVLink parameter `SERVOx_FUNCTION`

**Issue: "Mission upload fails"**
- **Cause**: Validation errors
- **Solution**: Check Flight Log panel for detailed errors
- **Note**: First 5 errors shown, fix and retry

## Performance

### Benchmarks

| Field Size | Seed Spacing | Waypoints | Generation Time | Upload Time |
|------------|--------------|-----------|-----------------|-------------|
| 100m × 100m | 5m | ~600 | <100ms | ~30s |
| 200m × 200m | 10m | ~400 | <150ms | ~20s |
| 500m × 500m | 20m | ~625 | <200ms | ~31s |

### Optimization Tips

1. **Larger Spacing**: Reduces waypoint count and upload time
2. **Parallel Lines**: Fastest pattern for large fields
3. **Higher Speed**: Reduces mission duration (but may affect seed placement accuracy)
4. **Lower Altitude**: Better seed placement accuracy (but slower)

## Hardware Requirements

### Servo Specifications

- **Type**: Standard RC servo (analog or digital)
- **Voltage**: 5-6V (from flight controller BEC)
- **Torque**: ≥3kg-cm (depends on dispenser mechanism)
- **Speed**: ≥0.1s/60° (faster = shorter dispense_duration)

### Dispenser Integration

```
Flight Controller → Servo Output → Servo → Seed Dispenser
     (PWM)            (Channel 9)    (5V)    (Mechanical)
```

### Wiring Example (Pixhawk)

```
AUX OUT 1 (Channel 9) → Servo Signal (Orange/White)
+5V Rail              → Servo Power (Red)
GND                   → Servo Ground (Brown/Black)
```

## Testing

### Unit Tests

```bash
# Run seeding planner tests
pytest tests/test_field_coverage.py -v
pytest tests/test_multi_drone_coverage.py -v

# Expected: 27/27 tests passing
```

### SITL Testing

```bash
# 1. Start ArduCopter SITL
sim_vehicle.py -v ArduCopter --console --map

# 2. Launch UI
python -m tools.ui

# 3. Test workflow
# - Connect to SITL (tcp:127.0.0.1:5762)
# - Draw field boundary
# - Enable seeding mode
# - Configure parameters
# - Generate mission
# - Upload and start
```

### Hardware Testing Checklist

- [ ] Servo responds to PWM commands
- [ ] Dispenser opens/closes reliably
- [ ] Seeds dispense consistently
- [ ] No jamming or clogging
- [ ] Timing parameters adequate
- [ ] Battery capacity sufficient
- [ ] GPS accuracy acceptable
- [ ] Altitude hold stable

## API Reference

### SeedingMissionPlanner

```python
class SeedingMissionPlanner:
    """Generate seeding missions with servo-controlled seed drops."""
    
    def plan_seeding_mission(
        self,
        field_boundary: List[Tuple[float, float]],
        home_position: Tuple[float, float, float],
        coverage_config: CoverageConfig,
        seeding_config: SeedingConfig
    ) -> List[Waypoint]:
        """
        Generate seeding mission waypoints.
        
        Args:
            field_boundary: List of (lat, lon) tuples defining field
            home_position: (lat, lon, alt) of takeoff location
            coverage_config: Coverage pattern configuration
            seeding_config: Seeding parameters
            
        Returns:
            List of Waypoint objects with NAV and SERVO commands
            
        Raises:
            ValueError: If validation fails or waypoint limit exceeded
        """
```

### SeedingConfig

```python
@dataclass
class SeedingConfig:
    """Configuration for seeding missions."""
    
    seed_spacing: float = 5.0          # meters
    servo_channel: int = 9             # 1-16
    servo_open_pwm: int = 1900         # µs
    servo_close_pwm: int = 1100        # µs
    dispense_duration: float = 0.5     # seconds
    wait_after_drop: float = 0.2       # seconds
```

## Future Enhancements

### Planned Features (Phase 4+)

- [ ] Variable seed density (more seeds in certain areas)
- [ ] Multi-seed-type support (different crops)
- [ ] Seed inventory tracking
- [ ] Automatic refill detection
- [ ] Seed placement verification (camera feedback)
- [ ] Terrain-adaptive spacing
- [ ] Wind compensation
- [ ] Real-time seed count monitoring

### Research Directions

- Machine learning for optimal seed spacing
- Computer vision for seed placement verification
- Multi-drone coordinated seeding
- Precision agriculture integration
- Soil moisture-based seed placement

## References

### MAVLink Commands

- [MAV_CMD_NAV_WAYPOINT (16)](https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_WAYPOINT)
- [MAV_CMD_DO_SET_SERVO (183)](https://mavlink.io/en/messages/common.html#MAV_CMD_DO_SET_SERVO)

### Related Documentation

- [Field Coverage Planning](field-coverage-planning.md)
- [Multi-Drone Coverage](swarm-coordination.md)
- [Mission Upload](../setup/px4-mission-upload.md)
- [API Reference](../api/control.md)

## Support

For issues or questions:
- GitHub Issues: [uavresearchproject/issues](https://github.com/yourusername/uavresearchproject/issues)
- Documentation: [docs/](../README.md)
- Tests: [tests/test_field_coverage.py](../../tests/test_field_coverage.py)