# API Overview

## Architecture

The UAV Research Platform follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    User Applications                     │
│              (examples/, experiments/)                   │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   High-Level SDK                         │
│         Drone, Swarm, MissionEngine                      │
│              (droneresearch/sdk/)                        │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  Control & Safety                        │
│    MissionEngine, APFSafetyFilter, Formations            │
│    (droneresearch/control/, safety/)                     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                            │
│   MAVLinkConnection, StateMachine, TelemetryState        │
│              (droneresearch/core/)                       │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  Autopilot Backends                      │
│         MAVLink (ArduPilot/PX4), ROS2 (PX4)              │
│         (droneresearch/autopilot/, ros/)                 │
└─────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Connection Management

All drone communication goes through `MAVLinkConnection`, which:
- Handles MAVLink protocol (ArduPilot & PX4)
- Manages connection lifecycle (connect/disconnect/reconnect)
- Parses telemetry messages
- Sends commands (arm, takeoff, goto, etc.)
- Emits events for state changes

**Default Port Convention:**
- `tcp:127.0.0.1:5762` - Raw ArduCopter SITL (default)
- `tcp:127.0.0.1:5760` - MAVProxy-aggregated SITL
- Resolution: `--port` flag > `$DRONE_PORT` env > default 5762

### 2. State Management

The `StateMachine` (FSM) tracks drone operational state:

```
IDLE → ARMING → ARMED → TAKEOFF → FLYING → MISSION
                  ↓         ↓         ↓        ↓
                IDLE    EMERGENCY  RTL → LANDING → IDLE
```

**State Groups:**
- `AIRBORNE_STATES`: TAKEOFF, FLYING, MISSION, RTL, LANDING
- `SAFE_STATES`: IDLE, ARMED

### 3. Telemetry

`TelemetryState` is a thread-safe dataclass containing all drone telemetry:
- GPS: lat, lon, alt, alt_rel, gps_fix, satellites
- Attitude: roll, pitch, yaw
- Velocity: vx, vy, vz, airspeed, groundspeed
- Battery: voltage, percentage, current
- Status: armed, flight_mode, autopilot type

### 4. Event System

All components use an event-driven architecture:

```python
drone.on("telemetry", lambda tel: print(tel.alt_rel))
drone.on("armed", lambda armed: print(f"Armed: {armed}"))
drone.on("mode", lambda mode: print(f"Mode: {mode}"))
```

## API Layers

### High-Level SDK (`droneresearch.sdk`)

**For researchers and application developers:**

- `Drone` - Single drone control with blocking methods
- `Swarm` - Multi-drone coordination
- `formations` - Formation geometry calculations

**Example:**
```python
from droneresearch import Drone

drone = Drone("tcp:127.0.0.1:5762")
drone.connect()
drone.arm()
drone.takeoff(10)
drone.goto(48.137, 11.575, 20)
drone.land()
```

### Control Layer (`droneresearch.control`)

**For mission planning and execution:**

- `MissionEngine` - Upload/run/monitor MAVLink missions
- `ScriptRunner` - Execute Python scripts on drones

**Example:**
```python
from droneresearch.control.mission import MissionEngine, Waypoint

mission = MissionEngine(connection)
mission.add(Waypoint(lat=48.137, lon=11.575, alt=20))
mission.add(Waypoint(lat=48.138, lon=11.576, alt=20))
mission.upload()  # Blocking, ~50ms per waypoint
mission.start()
mission.wait_done()
```

### Safety Layer (`droneresearch.safety`)

**For collision avoidance and geofencing:**

- `APFSafetyFilter` - Artificial Potential Field collision avoidance
- `Pose3D` - 3D position representation (NED coordinates)
- `Geofence` - Cylindrical geofence enforcement

**Example:**
```python
from droneresearch.safety.apf import APFSafetyFilter, Pose3D

apf = APFSafetyFilter(
    min_separation=2.0,
    max_speed=3.0,
    geofence_radius=50.0,
    geofence_alt=(1.0, 30.0)
)

positions = {"D1": Pose3D(0, 0, 10), "D2": Pose3D(3, 0, 10)}
desired = {"D1": Pose3D(0, 5, 10), "D2": Pose3D(5, 5, 10)}
safe = apf.filter(positions, desired)
```

### Core Layer (`droneresearch.core`)

**For low-level control and integration:**

- `MAVLinkConnection` - MAVLink protocol handler
- `StateMachine` - Drone state FSM
- `TelemetryState` - Thread-safe telemetry container

**Example:**
```python
from droneresearch.core.connection import MAVLinkConnection
from droneresearch.core.fsm import StateMachine, DroneState

conn = MAVLinkConnection("tcp:127.0.0.1:5762")
fsm = StateMachine(drone_id="D1")

conn.on("armed", lambda armed: 
    fsm.transition(DroneState.ARMED if armed else DroneState.IDLE))

conn.connect()
```

### ROS2 Integration (`droneresearch.ros`)

**For PX4 native integration:**

- `PX4Bridge` - PX4 uXRCE-DDS bridge (NOT MAVLink-over-ROS)
- `PX4Formation` - Formation control via ROS2
- `BagRecorder` - ROS2 bag recording
- Frame conversions: NED↔ENU, FRD↔FLU

**Critical:** Use `acquire_ros()` / `release_ros()` for context management.

**Example:**
```python
from droneresearch.ros.context import acquire_ros, release_ros
from droneresearch.ros.px4_bridge import PX4Bridge

acquire_ros()
try:
    bridge = PX4Bridge(namespace="/px4_1")
    bridge.arm()
    bridge.takeoff(10.0)
finally:
    release_ros()
```

## Design Patterns

### 1. Service Locator
Lazy imports avoid hard dependencies:
```python
def get_backend(autopilot: str = "mavlink"):
    from droneresearch.autopilot import get_backend as _get
    return _get(autopilot)
```

### 2. Observer Pattern
Event-driven architecture throughout:
```python
connection.on("telemetry", callback)
fsm.on_transition(callback)
mission.on_waypoint_reached(callback)
```

### 3. State Machine
Explicit state management with validation:
```python
fsm.transition(DroneState.FLYING)  # Returns False if invalid
```

### 4. Factory Pattern
Centralized object creation:
```python
from droneresearch import get_sitl, get_coordinator, get_swarm_commander
```

### 5. Thread-Safe Containers
All shared state uses locks:
```python
@dataclass
class TelemetryState:
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def update(self, **kwargs):
        with self._lock:
            # Update fields
```

## Testing Strategy

**Hardware-Free Tests:**
All tests use mocked dependencies from `tests/conftest.py`:
- `FakeConnection` - Mock MAVLink connection
- `FakeMav` - Captures MAVLink messages
- `snap_factory()` - Creates telemetry snapshots

**Example:**
```python
def test_arm(fake_conn):
    drone = Drone("fake://")
    drone._conn = fake_conn
    drone.arm()
    assert fake_conn.telemetry.armed
```

Full test suite runs in ~1 second with no hardware dependencies.

## Optional Dependencies

The platform uses lazy imports to make dependencies optional:

- **Core:** Only `pymavlink` required
- **ROS2:** `rclpy`, `px4_msgs` (optional)
- **UI:** `PyQt6` (optional)
- **Testing:** `pytest` (dev only)

Check availability:
```python
from droneresearch.ros import _ROS2_OK
if _ROS2_OK:
    # Use ROS2 features
```

## Next Steps

- [Core API Reference](core.md) - Low-level connection and state management
- [Control API Reference](control.md) - Mission planning and execution
- [Safety API Reference](safety.md) - Collision avoidance and geofencing
- [Design Patterns](patterns.md) - Detailed pattern documentation
- [Full API Reference](reference.md) - Complete class/method documentation