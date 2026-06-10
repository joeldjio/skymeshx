# Safety API Reference

The safety layer provides collision avoidance and geofencing using Artificial Potential Fields (APF).

## Overview

The APF Safety Filter prevents collisions between drones and enforces operational boundaries by:
- Applying **repulsive forces** between drones (and obstacles)
- Applying **attractive forces** toward desired waypoints
- Enforcing **kinematic limits** (max speed)
- Clipping positions to **geofence boundaries**

**Based on:** SkySim (Shibu et al., 2025) - "SkySim: A ROS2-based Simulation Environment for Natural Language Control of Drone Swarms using Large Language Models" (arXiv:2602.01226)

---

## Pose3D

3D position representation in local NED coordinates.

### Constructor

```python
@dataclass
class Pose3D:
    x: float = 0.0  # North in meters
    y: float = 0.0  # East in meters
    z: float = 0.0  # Altitude above ground (positive = UP)
```

**Coordinate System:**
- `x` = North (meters)
- `y` = East (meters)
- `z` = Altitude above ground (meters, **positive = UP**)

**Note:** The APF filter internally inverts `z` for NED calculations, but the API uses positive-up for intuitive altitude handling.

**Example:**
```python
from droneresearch.safety.apf import Pose3D

# Drone at 10m north, 5m east, 15m altitude
pos = Pose3D(x=10.0, y=5.0, z=15.0)
```

### Methods

#### dist()

```python
def dist(other: Pose3D) -> float
```

Calculate 3D Euclidean distance to another position.

**Parameters:**
- `other` (Pose3D): Target position

**Returns:**
- `float`: Distance in meters

**Example:**
```python
pos1 = Pose3D(0, 0, 10)
pos2 = Pose3D(3, 4, 10)
distance = pos1.dist(pos2)  # 5.0 meters
```

#### dist_2d()

```python
def dist_2d(other: Pose3D) -> float
```

Calculate 2D horizontal distance (ignoring altitude).

**Parameters:**
- `other` (Pose3D): Target position

**Returns:**
- `float`: Horizontal distance in meters

**Example:**
```python
pos1 = Pose3D(0, 0, 10)
pos2 = Pose3D(3, 4, 20)
distance = pos1.dist_2d(pos2)  # 5.0 meters (altitude ignored)
```

#### norm()

```python
def norm() -> float
```

Calculate vector magnitude (distance from origin).

**Returns:**
- `float`: Magnitude in meters

#### normalized()

```python
def normalized() -> Pose3D
```

Return unit vector in same direction.

**Returns:**
- `Pose3D`: Normalized vector (magnitude = 1.0)

**Example:**
```python
vec = Pose3D(3, 4, 0)
unit = vec.normalized()  # Pose3D(0.6, 0.8, 0.0)
```

#### clamp()

```python
def clamp(max_norm: float) -> Pose3D
```

Limit vector magnitude to maximum value.

**Parameters:**
- `max_norm` (float): Maximum allowed magnitude

**Returns:**
- `Pose3D`: Clamped vector

**Example:**
```python
vec = Pose3D(10, 0, 0)
clamped = vec.clamp(5.0)  # Pose3D(5.0, 0.0, 0.0)
```

### Operators

```python
# Addition
pos1 + pos2  # Component-wise addition

# Scalar multiplication
pos * 2.0    # Scale all components

# String representation
str(pos)     # "Pose3D(10.00, 5.00, 15.00)"
```

---

## Geofence

Cylindrical geofence with horizontal radius and altitude band.

### Constructor

```python
@dataclass
class Geofence:
    origin_x: float = 0.0    # Origin north coordinate (meters)
    origin_y: float = 0.0    # Origin east coordinate (meters)
    radius: float = 50.0     # Horizontal radius (meters)
    alt_min: float = 1.0     # Minimum altitude (meters)
    alt_max: float = 30.0    # Maximum altitude (meters)
```

**Example:**
```python
from droneresearch.safety.apf import Geofence

# 100m radius, 2-50m altitude
fence = Geofence(
    origin_x=0.0,
    origin_y=0.0,
    radius=100.0,
    alt_min=2.0,
    alt_max=50.0
)
```

### Methods

#### contains()

```python
def contains(p: Pose3D) -> bool
```

Check if position is within geofence.

**Parameters:**
- `p` (Pose3D): Position to check

**Returns:**
- `bool`: True if inside geofence

**Example:**
```python
fence = Geofence(radius=50.0, alt_min=1.0, alt_max=30.0)
pos = Pose3D(10, 10, 15)
if fence.contains(pos):
    print("Inside geofence")
```

#### clip()

```python
def clip(p: Pose3D) -> Pose3D
```

Clip position to geofence boundary.

**Parameters:**
- `p` (Pose3D): Position to clip

**Returns:**
- `Pose3D`: Clipped position (guaranteed inside geofence)

**Example:**
```python
fence = Geofence(radius=50.0, alt_min=1.0, alt_max=30.0)
pos = Pose3D(60, 0, 35)  # Outside fence
safe = fence.clip(pos)    # Pose3D(50.0, 0.0, 30.0)
```

---

## APFSafetyFilter

Artificial Potential Field collision avoidance filter.

### Constructor

```python
APFSafetyFilter(
    min_separation: float = 2.0,
    max_speed: float = 3.0,
    geofence_radius: float = 50.0,
    geofence_alt: Tuple[float, float] = (1.0, 30.0),
    repulsion_gain: float = 2.0,
    attraction_gain: float = 1.0,
    obstacle_radius: float = 4.0,
    dt: float = 0.05  # 20 Hz
)
```

**Parameters:**
- `min_separation` (float): Minimum safe distance between drones (meters)
- `max_speed` (float): Maximum velocity step per update (m/s)
- `geofence_radius` (float): Horizontal geofence radius from origin (meters)
- `geofence_alt` (Tuple[float, float]): (min_alt, max_alt) altitude band (meters)
- `repulsion_gain` (float): Strength of repulsive force between drones
- `attraction_gain` (float): Strength of attractive force toward waypoints
- `obstacle_radius` (float): Safety margin - repulsion activates within this range (meters)
- `dt` (float): Time step for velocity integration (seconds)

**Example:**
```python
from droneresearch.safety.apf import APFSafetyFilter

apf = APFSafetyFilter(
    min_separation=2.0,      # Keep 2m apart
    max_speed=3.0,           # Max 3 m/s movement per step
    geofence_radius=50.0,    # 50m radius fence
    geofence_alt=(1.0, 30.0),# 1-30m altitude
    repulsion_gain=2.0,      # Strong repulsion
    attraction_gain=1.0,     # Moderate attraction
    obstacle_radius=4.0,     # Activate repulsion at 4m
    dt=0.05                  # 20 Hz update rate
)
```

### Methods

#### filter()

```python
def filter(
    positions: Dict[str, Pose3D],
    desired: Dict[str, Pose3D]
) -> Dict[str, Pose3D]
```

Apply APF to compute safe waypoints for all drones.

**Parameters:**
- `positions` (Dict[str, Pose3D]): Current positions of all drones
- `desired` (Dict[str, Pose3D]): Desired target positions

**Returns:**
- `Dict[str, Pose3D]`: Safe waypoints after APF filtering

**Algorithm:**
1. For each drone:
   - Calculate **attractive force** toward desired position
   - Calculate **repulsive forces** from other drones
   - Calculate **repulsive forces** from static obstacles
   - Sum forces and clamp to max_speed
   - Apply geofence clipping

**Example:**
```python
# Current positions
positions = {
    "D1": Pose3D(0, 0, 10),
    "D2": Pose3D(3, 0, 10),
    "D3": Pose3D(6, 0, 10),
}

# Desired positions (from mission planner / LLM)
desired = {
    "D1": Pose3D(0, 5, 10),
    "D2": Pose3D(5, 5, 10),
    "D3": Pose3D(10, 5, 10),
}

# Apply APF filter
safe = apf.filter(positions, desired)

# Send safe waypoints to drones
for drone_id, pos in safe.items():
    drone = swarm.get(drone_id)
    drone.goto(pos.x, pos.y, pos.z)
```

#### check_separation()

```python
def check_separation(
    positions: Dict[str, Pose3D]
) -> List[Tuple[str, str, float]]
```

Check for minimum separation violations.

**Parameters:**
- `positions` (Dict[str, Pose3D]): Current positions of all drones

**Returns:**
- `List[Tuple[str, str, float]]`: List of (drone_a, drone_b, distance) for violations

**Example:**
```python
positions = {
    "D1": Pose3D(0, 0, 10),
    "D2": Pose3D(1, 0, 10),  # Only 1m apart!
}

violations = apf.check_separation(positions)
for drone_a, drone_b, dist in violations:
    print(f"WARNING: {drone_a} and {drone_b} are {dist:.2f}m apart")
```

#### add_obstacle()

```python
def add_obstacle(x: float, y: float, z: float = 0.0)
```

Add a static obstacle (e.g., building, tree).

**Parameters:**
- `x` (float): North coordinate (meters)
- `y` (float): East coordinate (meters)
- `z` (float): Altitude (meters, default: 0.0)

**Example:**
```python
# Add building at (20, 30) with 25m height
apf.add_obstacle(x=20.0, y=30.0, z=25.0)

# Add tree at (10, 15) with 10m height
apf.add_obstacle(x=10.0, y=15.0, z=10.0)
```

#### clear_obstacles()

```python
def clear_obstacles()
```

Remove all static obstacles.

**Example:**
```python
apf.clear_obstacles()
```

---

## APFFilterLoop

Background thread running APF filter at configurable rate.

### Constructor

```python
APFFilterLoop(
    apf: APFSafetyFilter,
    get_positions: Callable[[], Dict[str, Pose3D]],
    get_desired: Callable[[], Dict[str, Pose3D]],
    on_safe: Callable[[Dict[str, Pose3D]], None],
    hz: float = 20.0,
    on_violation: Optional[Callable[[List], None]] = None
)
```

**Parameters:**
- `apf` (APFSafetyFilter): Configured APF filter
- `get_positions` (Callable): Function returning current drone positions
- `get_desired` (Callable): Function returning desired target positions
- `on_safe` (Callable): Callback receiving safe waypoints
- `hz` (float): Update rate in Hz (default: 20.0)
- `on_violation` (Callable): Optional callback for separation violations

**Example:**
```python
from droneresearch.safety.apf import APFSafetyFilter, APFFilterLoop

apf = APFSafetyFilter()

# Data sources
def get_positions():
    return {
        "D1": Pose3D(swarm.get("D1").telemetry.x, ...),
        "D2": Pose3D(swarm.get("D2").telemetry.x, ...),
    }

def get_desired():
    return mission_planner.get_targets()

# Callback to send safe waypoints
def on_safe(safe_waypoints):
    for drone_id, pos in safe_waypoints.items():
        swarm.get(drone_id).goto(pos.x, pos.y, pos.z)

# Violation handler
def on_violation(violations):
    for drone_a, drone_b, dist in violations:
        print(f"COLLISION RISK: {drone_a}-{drone_b} at {dist:.2f}m")

# Start filter loop
loop = APFFilterLoop(
    apf=apf,
    get_positions=get_positions,
    get_desired=get_desired,
    on_safe=on_safe,
    hz=20.0,
    on_violation=on_violation
)
loop.start()

# ... run mission ...

loop.stop()
```

### Methods

#### start()

```python
def start()
```

Start the filter loop in a background thread.

#### stop()

```python
def stop()
```

Stop the filter loop.

---

## Complete Usage Example

```python
from droneresearch import Swarm
from droneresearch.safety.apf import APFSafetyFilter, Pose3D

# Create swarm
swarm = Swarm()
swarm.add("D1", "tcp:127.0.0.1:5762")
swarm.add("D2", "tcp:127.0.0.1:5763")
swarm.add("D3", "tcp:127.0.0.1:5764")
swarm.connect_all()

# Configure APF filter
apf = APFSafetyFilter(
    min_separation=3.0,
    max_speed=2.0,
    geofence_radius=100.0,
    geofence_alt=(2.0, 50.0)
)

# Add obstacles
apf.add_obstacle(x=20.0, y=20.0, z=15.0)  # Building

# Takeoff
swarm.arm_all()
swarm.takeoff_all(altitude=10.0)

# Mission waypoints (potentially unsafe)
desired = {
    "D1": Pose3D(10, 10, 15),
    "D2": Pose3D(10, 10, 15),  # Same as D1 - collision!
    "D3": Pose3D(10, 10, 15),  # Same as D1 - collision!
}

# Get current positions
positions = {
    "D1": Pose3D(0, 0, 10),
    "D2": Pose3D(5, 0, 10),
    "D3": Pose3D(10, 0, 10),
}

# Apply APF filter
safe = apf.filter(positions, desired)

# Safe waypoints will be spread out to maintain separation
for drone_id, pos in safe.items():
    print(f"{drone_id}: {pos}")
    drone = swarm.get(drone_id)
    # Convert to GPS if needed, or use local NED
    drone.goto(home_lat + pos.x/111320, home_lon + pos.y/111320, pos.z)

# Check for violations
violations = apf.check_separation(safe)
if violations:
    print("WARNING: Separation violations detected!")
    for drone_a, drone_b, dist in violations:
        print(f"  {drone_a} - {drone_b}: {dist:.2f}m")
```

---

## APF Algorithm Details

### Attractive Force

Pulls drone toward desired position:

```
F_attr = (desired - current) * attraction_gain
F_attr = clamp(F_attr, max_speed * dt)
```

### Repulsive Force

Pushes drone away from obstacles/drones:

```
For each obstacle within obstacle_radius:
    distance = ||current - obstacle||
    if distance < obstacle_radius:
        magnitude = repulsion_gain * (1/d - 1/r) / d²
        direction = normalize(current - obstacle)
        F_rep += direction * magnitude * dt
```

### Total Force

```
F_total = F_attr + F_rep
F_total = clamp(F_total, max_speed * dt)
new_position = current + F_total
```

### Geofence Clipping

```
if new_position outside geofence:
    new_position = clip_to_boundary(new_position)
```

---

## Tuning Guidelines

### min_separation

- **Too small:** Risk of collisions
- **Too large:** Drones spread too far, formations break
- **Recommended:** 2-3 meters for outdoor, 1-2 meters for indoor

### max_speed

- **Too small:** Slow response, drones lag behind
- **Too large:** Jerky motion, overshooting
- **Recommended:** 2-5 m/s depending on drone capabilities

### repulsion_gain

- **Too small:** Weak avoidance, collisions possible
- **Too large:** Drones repel too strongly, formations unstable
- **Recommended:** 1.5-3.0

### attraction_gain

- **Too small:** Slow convergence to target
- **Too large:** Overshooting, oscillation
- **Recommended:** 0.5-1.5

### obstacle_radius

- **Too small:** Late avoidance, near-misses
- **Too large:** Drones avoid too early, inefficient paths
- **Recommended:** 2× min_separation (4-6 meters)

---

## Performance Considerations

### Computational Complexity

- **O(n²)** for n drones (all-pairs repulsion)
- **O(n×m)** for m static obstacles
- **20 Hz:** ~50ms budget per cycle
- **Practical limit:** ~20 drones at 20 Hz on modern CPU

### Optimization Tips

1. **Reduce update rate** for large swarms (10 Hz instead of 20 Hz)
2. **Spatial partitioning** for >20 drones (only check nearby pairs)
3. **Async filtering** in separate thread (use `APFFilterLoop`)

### Memory Usage

- **Per drone:** ~100 bytes
- **10 drones:** ~1 KB
- **100 drones:** ~10 KB
- Negligible compared to telemetry/logging

---

## Integration with Mission Planning

```python
from droneresearch.control.mission import MissionEngine, Waypoint
from droneresearch.safety.apf import APFSafetyFilter, Pose3D

# Mission waypoints
mission_waypoints = [
    Waypoint(lat=48.137, lon=11.575, alt=20),
    Waypoint(lat=48.138, lon=11.576, alt=20),
]

# Convert to local NED
def gps_to_ned(lat, lon, alt, home_lat, home_lon):
    x = (lat - home_lat) * 111320  # meters north
    y = (lon - home_lon) * 111320 * cos(radians(home_lat))  # meters east
    z = alt  # meters altitude
    return Pose3D(x, y, z)

# Apply APF before sending to drones
apf = APFSafetyFilter()
for wp in mission_waypoints:
    ned = gps_to_ned(wp.lat, wp.lon, wp.alt, home_lat, home_lon)
    desired = {"D1": ned}
    positions = {"D1": get_current_position()}
    safe = apf.filter(positions, desired)
    # Send safe waypoint
    drone.goto(safe["D1"].x, safe["D1"].y, safe["D1"].z)
```

---

## Safety Guarantees

### What APF Guarantees

✅ Collision avoidance between drones (if properly tuned)  
✅ Geofence enforcement (hard boundary)  
✅ Kinematic limits (max speed)  
✅ Smooth trajectories (no sudden jumps)

### What APF Does NOT Guarantee

❌ Optimal paths (greedy local optimization)  
❌ Deadlock-free (drones can get stuck in local minima)  
❌ Real-time guarantees (depends on CPU load)  
❌ Obstacle detection (only pre-defined obstacles)

### Recommended Additional Safety

1. **Pre-flight checks:** GPS fix, battery, geofence
2. **Failsafe modes:** RTL on low battery, loss of GPS
3. **Manual override:** Always have RC control available
4. **Redundant sensors:** Use onboard collision avoidance if available
5. **Conservative tuning:** Start with large separations, slow speeds