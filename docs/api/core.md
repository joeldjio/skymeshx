# Core API Reference

The core layer provides low-level MAVLink communication, state management, and telemetry handling.

## MAVLinkConnection

Thread-safe MAVLink connection handler supporting ArduPilot and PX4.

### Constructor

```python
MAVLinkConnection(
    connection_string: str,
    source_system: int = 255,
    auto_reconnect: bool = True
)
```

**Parameters:**
- `connection_string` (str): Connection string (e.g., "tcp:127.0.0.1:5762")
- `source_system` (int): MAVLink source system ID (default: 255 = GCS)
- `auto_reconnect` (bool): Enable automatic reconnection with exponential backoff

**Connection String Formats:**
- `tcp:HOST:PORT` - TCP connection (e.g., "tcp:127.0.0.1:5762")
- `udp:HOST:PORT` - UDP connection (e.g., "udp:0.0.0.0:14550")
- `/dev/ttyUSB0[:BAUD]` - Linux serial device
- `COMx[:BAUD]` - Windows serial port

**Default Port Convention:**
- `5762` - Raw ArduCopter SITL (default)
- `5760` - MAVProxy-aggregated SITL
- `14550` - Standard UDP port for GCS

### Methods

#### connect()

```python
def connect(timeout: float = 15.0) -> bool
```

Establish connection and wait for heartbeat.

**Parameters:**
- `timeout` (float): Maximum time to wait for heartbeat (seconds)

**Returns:**
- `bool`: True if connected successfully, False otherwise

**Example:**
```python
conn = MAVLinkConnection("tcp:127.0.0.1:5762")
if conn.connect(timeout=10.0):
    print("Connected!")
else:
    print("Connection failed")
```

#### disconnect()

```python
def disconnect()
```

Close the connection and stop the receive thread.

**Example:**
```python
conn.disconnect()
```

#### arm()

```python
def arm(force: bool = False) -> bool
```

Send arm command to the autopilot.

**Parameters:**
- `force` (bool): Force arming (bypasses pre-arm checks)

**Returns:**
- `bool`: True if command sent successfully

**Example:**
```python
conn.arm()  # Normal arming
conn.arm(force=True)  # Force arm (use with caution!)
```

#### disarm()

```python
def disarm(force: bool = False) -> bool
```

Send disarm command to the autopilot.

**Parameters:**
- `force` (bool): Force disarming (emergency use)

**Returns:**
- `bool`: True if command sent successfully

#### set_mode()

```python
def set_mode(mode: str) -> bool
```

Change flight mode.

**Parameters:**
- `mode` (str): Flight mode name (e.g., "GUIDED", "AUTO", "LOITER", "OFFBOARD")

**Returns:**
- `bool`: True if command sent successfully

**ArduPilot Modes:**
- STABILIZE, ACRO, ALT_HOLD, AUTO, GUIDED, LOITER, RTL, CIRCLE, LAND, etc.

**PX4 Modes:**
- MANUAL, ALTCTL, POSCTL, AUTO, ACRO, OFFBOARD, STABILIZED

**Example:**
```python
conn.set_mode("GUIDED")  # ArduPilot
conn.set_mode("OFFBOARD")  # PX4
```

#### takeoff()

```python
def takeoff(altitude: float = 10.0) -> bool
```

Send takeoff command.

**Parameters:**
- `altitude` (float): Target altitude in meters (relative to home)

**Returns:**
- `bool`: True if command sent successfully

**Example:**
```python
conn.takeoff(15.0)  # Takeoff to 15m
```

#### land()

```python
def land() -> bool
```

Send land command.

**Returns:**
- `bool`: True if command sent successfully

#### rtl()

```python
def rtl() -> bool
```

Send Return-To-Launch command.

**Returns:**
- `bool`: True if command sent successfully

#### goto()

```python
def goto(lat: float, lon: float, alt: float) -> bool
```

Fly to GPS coordinate using SET_POSITION_TARGET_GLOBAL_INT.

**Parameters:**
- `lat` (float): Latitude in degrees
- `lon` (float): Longitude in degrees
- `alt` (float): Altitude in meters (relative to home)

**Returns:**
- `bool`: True if command sent successfully

**Frame:** MAV_FRAME_GLOBAL_RELATIVE_ALT (6)  
**Type Mask:** 0x0FF8 (position only, ignore velocity/accel/yaw)

**Example:**
```python
# Fly to Munich coordinates at 20m altitude
conn.goto(48.137154, 11.576124, 20.0)
```

#### set_speed()

```python
def set_speed(speed_ms: float) -> bool
```

Set target speed.

**Parameters:**
- `speed_ms` (float): Speed in meters per second

**Returns:**
- `bool`: True if command sent successfully

**Example:**
```python
conn.set_speed(5.0)  # 5 m/s
```

### Properties

#### connected

```python
@property
def connected() -> bool
```

Check if connection is active.

**Returns:**
- `bool`: True if connected

#### telemetry

```python
@property
def telemetry() -> TelemetryState
```

Get current telemetry state.

**Returns:**
- `TelemetryState`: Thread-safe telemetry container

### Events

Register callbacks with `on(event, callback)`:

**Available Events:**
- `"connected"` - Fired when connection established
- `"disconnected"` - Fired when connection lost
- `"telemetry"` - Fired on telemetry update (receives `TelemetryState`)
- `"message"` - Fired on every raw MAVLink message
- `"statustext"` - Fired on STATUSTEXT (receives `text: str, severity: int`)
- `"armed"` - Fired when armed state changes (receives `armed: bool`)
- `"mode"` - Fired when flight mode changes (receives `mode: str`)
- `"command_ack"` - Fired on command acknowledgment (receives `cmd_name, code, result_name, success`)

**Example:**
```python
def on_telemetry(tel: TelemetryState):
    print(f"Alt: {tel.alt_rel:.1f}m, Battery: {tel.battery_pct:.0f}%")

def on_armed(armed: bool):
    print(f"Armed: {armed}")

conn.on("telemetry", on_telemetry)
conn.on("armed", on_armed)
```

### Auto-Reconnect

When `auto_reconnect=True`, the connection automatically attempts to reconnect on failure:

- **Backoff sequence:** 1s, 2s, 4s, 8s, 16s, capped at 30s
- **Events:** Emits `"disconnected"` on loss, `"connected"` on recovery
- **Thread-safe:** Safe to call methods during reconnection

**Example:**
```python
conn = MAVLinkConnection("tcp:127.0.0.1:5762", auto_reconnect=True)
conn.on("disconnected", lambda: print("Connection lost, reconnecting..."))
conn.on("connected", lambda: print("Reconnected!"))
conn.connect()
```

---

## StateMachine

Finite State Machine for drone operational state tracking.

### States

```python
class DroneState(Enum):
    IDLE       # Connected, disarmed, on ground
    ARMING     # Arm command sent, waiting for confirmation
    ARMED      # Armed, on ground
    TAKEOFF    # Takeoff in progress
    FLYING     # Airborne, in LOITER/GUIDED
    MISSION    # Executing autonomous mission
    RTL        # Returning to launch
    LANDING    # Landing in progress
    EMERGENCY  # Failsafe / emergency
    ERROR      # Unrecoverable error
```

### Valid Transitions

```
IDLE      → ARMING
ARMING    → ARMED | IDLE
ARMED     → TAKEOFF | IDLE
TAKEOFF   → FLYING | EMERGENCY
FLYING    → MISSION | RTL | LANDING | EMERGENCY
MISSION   → FLYING | RTL | EMERGENCY
RTL       → LANDING | EMERGENCY
LANDING   → IDLE | EMERGENCY
EMERGENCY → IDLE (manual reset only)
ERROR     → IDLE (manual reset only)
```

### Constructor

```python
StateMachine(drone_id: str = "drone")
```

**Parameters:**
- `drone_id` (str): Identifier for this drone (used in logs)

### Methods

#### transition()

```python
def transition(new_state: DroneState, force: bool = False) -> bool
```

Attempt to transition to a new state.

**Parameters:**
- `new_state` (DroneState): Target state
- `force` (bool): Bypass validation (emergency use only)

**Returns:**
- `bool`: True if transition successful, False if rejected

**Example:**
```python
fsm = StateMachine(drone_id="D1")
if fsm.transition(DroneState.ARMING):
    print("Transitioning to ARMING")
else:
    print("Invalid transition")
```

#### reset()

```python
def reset()
```

Force reset to IDLE state (emergency/manual use).

**Example:**
```python
fsm.reset()  # Force back to IDLE
```

#### emergency()

```python
def emergency()
```

Immediate transition to EMERGENCY state (always allowed).

**Example:**
```python
fsm.emergency()  # Trigger emergency state
```

#### on_transition()

```python
def on_transition(cb: Callable[[DroneState, DroneState], None])
```

Register callback for state transitions.

**Parameters:**
- `cb` (Callable): Callback function receiving `(old_state, new_state)`

**Example:**
```python
def on_state_change(old, new):
    print(f"State: {old.name} → {new.name}")

fsm.on_transition(on_state_change)
```

#### on_rejection()

```python
def on_rejection(cb: Callable[[DroneState, DroneState], None])
```

Register callback for rejected transitions.

**Parameters:**
- `cb` (Callable): Callback function receiving `(current_state, requested_state)`

**Example:**
```python
def on_reject(current, requested):
    print(f"REJECTED: {current.name} → {requested.name}")

fsm.on_rejection(on_reject)
```

#### history()

```python
def history(last_n: int = 20) -> List[dict]
```

Get recent state transition history.

**Parameters:**
- `last_n` (int): Number of recent transitions to return

**Returns:**
- `List[dict]`: List of `{"t": timestamp, "from": state, "to": state}`

**Example:**
```python
for entry in fsm.history(10):
    print(f"{entry['t']}: {entry['from']} → {entry['to']}")
```

### Properties

#### state

```python
@property
def state() -> DroneState
```

Get current state.

#### previous

```python
@property
def previous() -> DroneState
```

Get previous state.

#### is_airborne

```python
@property
def is_airborne() -> bool
```

Check if drone is airborne (TAKEOFF, FLYING, MISSION, RTL, LANDING).

#### is_safe

```python
@property
def is_safe() -> bool
```

Check if drone is in safe state (IDLE, ARMED).

#### can_arm

```python
@property
def can_arm() -> bool
```

Check if arming is allowed (state == IDLE).

#### can_takeoff

```python
@property
def can_takeoff() -> bool
```

Check if takeoff is allowed (state == ARMED).

#### can_mission

```python
@property
def can_mission() -> bool
```

Check if mission start is allowed (state == FLYING).

#### rejected_count

```python
@property
def rejected_count() -> int
```

Get total number of rejected transitions.

---

## TelemetryState

Thread-safe container for all drone telemetry data.

### Fields

**GPS:**
- `lat` (float): Latitude in degrees
- `lon` (float): Longitude in degrees
- `alt` (float): Altitude AMSL in meters
- `alt_rel` (float): Altitude relative to home in meters
- `gps_fix` (int): GPS fix type (0=no fix, 3=3D fix)
- `satellites` (int): Number of visible satellites

**Attitude:**
- `roll` (float): Roll angle in degrees
- `pitch` (float): Pitch angle in degrees
- `yaw` (float): Yaw angle (heading) in degrees (0-360)

**Velocity:**
- `vx` (float): Velocity north in m/s
- `vy` (float): Velocity east in m/s
- `vz` (float): Velocity down in m/s
- `airspeed` (float): Airspeed in m/s
- `groundspeed` (float): Ground speed in m/s
- `climb` (float): Climb rate in m/s

**Battery:**
- `battery_v` (float): Battery voltage in volts
- `battery_pct` (float): Battery percentage (0-100, -1=unknown)
- `current_a` (float): Current draw in amperes

**Status:**
- `armed` (bool): Armed state
- `flight_mode` (str): Current flight mode
- `autopilot` (str): Autopilot type ("ardupilot" | "px4" | "unknown")
- `vehicle_type` (str): Vehicle type (e.g., "QUADROTOR")
- `system_status` (int): MAVLink system status code

**Timestamps:**
- `last_heartbeat` (float): Last heartbeat time (Unix timestamp)
- `last_gps` (float): Last GPS update time
- `last_attitude` (float): Last attitude update time

### Methods

#### update()

```python
def update(**kwargs)
```

Thread-safe update of telemetry fields.

**Parameters:**
- `**kwargs`: Field names and values to update

**Example:**
```python
tel = TelemetryState()
tel.update(lat=48.137, lon=11.576, alt_rel=15.0)
```

#### snapshot()

```python
def snapshot() -> dict
```

Get thread-safe snapshot of all telemetry fields.

**Returns:**
- `dict`: Dictionary of all telemetry fields

**Example:**
```python
snap = tel.snapshot()
print(f"Position: {snap['lat']}, {snap['lon']}, {snap['alt_rel']}")
```

### Properties

#### is_stale

```python
@property
def is_stale() -> bool
```

Check if telemetry is stale (no heartbeat for >5 seconds).

#### has_gps

```python
@property
def has_gps() -> bool
```

Check if GPS has 3D fix (gps_fix >= 3).

---

## Usage Examples

### Basic Connection

```python
from droneresearch.core.connection import MAVLinkConnection

conn = MAVLinkConnection("tcp:127.0.0.1:5762")
conn.on("connected", lambda: print("Connected!"))
conn.on("telemetry", lambda tel: print(f"Alt: {tel.alt_rel:.1f}m"))

if conn.connect():
    conn.arm()
    conn.takeoff(10.0)
    # ... fly ...
    conn.land()
    conn.disconnect()
```

### State Machine Integration

```python
from droneresearch.core.connection import MAVLinkConnection
from droneresearch.core.fsm import StateMachine, DroneState

conn = MAVLinkConnection("tcp:127.0.0.1:5762")
fsm = StateMachine(drone_id="D1")

# Wire connection events to FSM
conn.on("armed", lambda armed: 
    fsm.transition(DroneState.ARMED if armed else DroneState.IDLE))

conn.on("mode", lambda mode:
    fsm.transition(DroneState.MISSION if mode == "AUTO" else DroneState.FLYING))

# Monitor state changes
fsm.on_transition(lambda old, new: print(f"{old.name} → {new.name}"))

conn.connect()
```

### Telemetry Monitoring

```python
from droneresearch.core.connection import MAVLinkConnection

conn = MAVLinkConnection("tcp:127.0.0.1:5762")

def monitor_telemetry(tel):
    if tel.is_stale:
        print("WARNING: Telemetry stale!")
    if not tel.has_gps:
        print("WARNING: No GPS fix!")
    if tel.battery_pct < 20:
        print(f"WARNING: Low battery ({tel.battery_pct:.0f}%)")
    
    print(f"Pos: {tel.lat:.6f}, {tel.lon:.6f}, {tel.alt_rel:.1f}m")
    print(f"Attitude: R={tel.roll:.1f}° P={tel.pitch:.1f}° Y={tel.yaw:.1f}°")
    print(f"Speed: {tel.groundspeed:.1f} m/s")

conn.on("telemetry", monitor_telemetry)
conn.connect()