# Swarm Coordination

Multi-drone coordination with formation flying, parallel operations, and synchronized control.

## Overview

The SkyMeshX Platform provides comprehensive swarm coordination capabilities:

- **Multi-drone management** - Add, remove, and control multiple drones
- **Parallel operations** - Execute commands on all drones simultaneously
- **Formation flying** - Maintain geometric formations (line, V, grid, circle, wedge)
- **Leader-follower** - Dynamic formation following with continuous updates
- **Collision avoidance** - Integrated APF safety filter
- **Synchronized telemetry** - Real-time monitoring of all drones

## Quick Start

```python
from skymeshx import Swarm

# Create swarm
swarm = Swarm()
swarm.add("D1", "tcp:127.0.0.1:5762")
swarm.add("D2", "tcp:127.0.0.1:5763")
swarm.add("D3", "tcp:127.0.0.1:5764")

# Connect all drones in parallel
results = swarm.connect_all()
print(f"Connected: {sum(results.values())}/{len(results)}")

# Parallel operations
swarm.arm_all()
swarm.takeoff_all(altitude=10.0)

# Formation flying
swarm.formation("v", spacing=5.0, leader="D1")

# Land all
swarm.land_all()
swarm.disconnect_all()
```

## Features

### 1. Multi-Drone Management

#### Adding Drones

```python
swarm = Swarm()

# Add drones with unique IDs
swarm.add("D1", "tcp:127.0.0.1:5762")
swarm.add("D2", "tcp:127.0.0.1:5763")
swarm.add("D3", "tcp:127.0.0.1:5764")

# Get individual drone
drone = swarm.get("D1")
drone.arm()
drone.takeoff(10)
```

#### Removing Drones

```python
# Remove and disconnect
swarm.remove("D3")

# Check count
print(f"Active drones: {swarm.count}")
```

#### Accessing Drones

```python
# Get all drones
for drone in swarm.drones:
    print(f"{drone.id}: {drone.telemetry.alt_rel:.1f}m")

# Get specific drone
d1 = swarm.get("D1")
if d1:
    print(f"D1 battery: {d1.battery:.0f}%")
```

### 2. Parallel Operations

All `*_all()` methods execute in parallel using threads:

```python
# Parallel connection (fastest)
results = swarm.connect_all(timeout=15.0)
# Returns: {"D1": True, "D2": True, "D3": False}

# Parallel arming
swarm.arm_all()

# Parallel takeoff
swarm.takeoff_all(altitude=10.0)

# Parallel mode change
swarm.set_mode_all("LOITER")

# Parallel speed change
swarm.set_speed_all(5.0)

# Parallel landing
swarm.land_all()

# Parallel RTL
swarm.rtl_all()

# Parallel disarm
swarm.disarm_all()

# Parallel disconnect
swarm.disconnect_all()
```

**Performance:**
- 3 drones connect in ~15 seconds (parallel) vs ~45 seconds (sequential)
- Operations complete when slowest drone finishes
- Thread-safe - no race conditions

### 3. Formation Flying

#### Static Formations

Execute formation once:

```python
# Line formation (drones trail behind leader)
swarm.formation("line", spacing=5.0, leader="D1")

# V formation (60° angle)
swarm.formation("v", spacing=5.0, leader="D1")

# Grid formation (square grid)
swarm.formation("grid", spacing=5.0, leader="D1")

# Circle formation (ring around leader)
swarm.formation("circle", spacing=5.0, leader="D1")

# Wedge formation (tight V)
swarm.formation("wedge", spacing=5.0, leader="D1")
```

**Formation Geometry:**

```
LINE:           V (60°):        GRID:           CIRCLE:
  D1              D1            D1 D2           D2
  D2            D2  D3          D3 D4         D1  D3
  D3                                            D4

WEDGE:
  D1
 D2 D3
D4   D5
```

#### Dynamic Formation Following

Continuously update formation as leader moves:

```python
# Start following
swarm.start_follow(
    shape="v",
    spacing=5.0,
    leader="D1",
    update_hz=2.0  # Update 2 times per second
)

# Leader moves, followers maintain formation
leader = swarm.get("D1")
leader.goto(48.137, 11.575, 20)  # Followers adjust automatically

# Stop following
swarm.stop_follow()
```

**Use Cases:**
- Search and rescue (leader scans, followers maintain coverage)
- Aerial photography (leader follows subject, followers provide angles)
- Exploration (leader navigates, followers map surroundings)

### 4. Formation Geometry Details

All formations use canonical geometry from `skymeshx.sdk.formations`:

#### Line Formation

```python
# Followers trail directly behind leader
# Spacing: distance between consecutive drones
swarm.formation("line", spacing=5.0)

# Positions (relative to leader at origin):
# D1: (0, 0)      - Leader
# D2: (-5, 0)     - 5m behind
# D3: (-10, 0)    - 10m behind
# D4: (-15, 0)    - 15m behind
```

#### V Formation

```python
# 60° V-shape, followers fan out behind
swarm.formation("v", spacing=5.0)

# Positions (relative to leader):
# D1: (0, 0)              - Leader at apex
# D2: (-4.33, -2.5)       - Left wing
# D3: (-4.33, +2.5)       - Right wing
# D4: (-8.66, -5.0)       - Left wing, rank 2
# D5: (-8.66, +5.0)       - Right wing, rank 2
```

#### Grid Formation

```python
# Square grid, leader at front-left
swarm.formation("grid", spacing=5.0)

# Positions (4 drones):
# D1: (0, -2.5)    - Leader
# D2: (0, +2.5)    - Same row
# D3: (-5, -2.5)   - Second row
# D4: (-5, +2.5)   - Second row
```

#### Circle Formation

```python
# Ring around leader, radius scales with count
swarm.formation("circle", spacing=5.0)

# Radius = spacing * count / (2π)
# Positions evenly distributed around circle
```

#### Wedge Formation

```python
# Tight V-shape (0.8x longitudinal, 0.5x lateral)
swarm.formation("wedge", spacing=5.0)

# Tighter than V formation, better for high-speed flight
```

### 5. Coordinate Conversion

Formations use local NED offsets, converted to GPS:

```python
# Formation calculates offsets in meters (north, east)
offsets = formation_offsets("v", count=3, spacing=5.0)
# Returns: [(-4.33, -2.5), (-4.33, +2.5), ...]

# Convert to GPS coordinates
lat0, lon0, alt0 = leader.position

for i, drone in enumerate(followers):
    north_m, east_m = offsets[i]
    
    # Meters to degrees
    dlat = north_m / 111320.0
    dlon = east_m / (111320.0 * cos(radians(lat0)))
    
    target_lat = lat0 + dlat
    target_lon = lon0 + dlon
    
    drone.goto(target_lat, target_lon, alt0)
```

### 6. Telemetry Monitoring

```python
# Get all telemetry
all_tel = swarm.telemetry_all()
# Returns: {"D1": {...}, "D2": {...}, "D3": {...}}

# Monitor specific fields
for drone_id, tel in all_tel.items():
    print(f"{drone_id}: Alt={tel['alt_rel']:.1f}m, "
          f"Battery={tel['battery_pct']:.0f}%, "
          f"Mode={tel['flight_mode']}")

# Check health
for drone_id, tel in all_tel.items():
    if tel['battery_pct'] < 20:
        print(f"WARNING: {drone_id} low battery!")
    if not tel['armed']:
        print(f"WARNING: {drone_id} disarmed!")
```

### 7. Event Handling

```python
# Register swarm-level events
def on_swarm_event(event_data):
    print(f"Swarm event: {event_data}")

swarm.on("formation_complete", on_swarm_event)

# Individual drone events still work
for drone in swarm.drones:
    drone.on("altitude", lambda alt, d=drone: 
        print(f"{d.id} altitude: {alt:.1f}m"))
```

## Advanced Usage

### 1. Custom Formation Patterns

```python
from skymeshx.sdk.formations import formation_offsets

# Get offsets for custom processing
offsets = formation_offsets("v", count=5, spacing=10.0)

# Apply custom transformations
for i, (north, east) in enumerate(offsets):
    # Rotate formation 45°
    import math
    angle = math.radians(45)
    north_rot = north * math.cos(angle) - east * math.sin(angle)
    east_rot = north * math.sin(angle) + east * math.cos(angle)
    
    # Apply to drone
    drone = swarm.drones[i+1]  # Skip leader
    # ... convert to GPS and send
```

### 2. Heterogeneous Swarms

```python
# Different drone types
swarm.add("quad_1", "tcp:127.0.0.1:5762")  # Quadcopter
swarm.add("hexa_1", "tcp:127.0.0.1:5763")  # Hexacopter
swarm.add("fixed_1", "tcp:127.0.0.1:5764") # Fixed-wing

# Type-specific operations
quad = swarm.get("quad_1")
quad.set_speed(5.0)  # Fast

fixed = swarm.get("fixed_1")
fixed.set_speed(15.0)  # Very fast

# Formation with mixed types
swarm.formation("line", spacing=10.0)  # Larger spacing for fixed-wing
```

### 3. Swarm with Safety Filter

```python
from skymeshx.safety.apf import APFSafetyFilter, Pose3D

swarm = Swarm()
# ... add drones ...

# Configure safety
apf = APFSafetyFilter(
    min_separation=3.0,
    max_speed=2.0,
    geofence_radius=100.0
)

# Formation with safety
def safe_formation(shape, spacing):
    # Get current positions
    positions = {}
    for drone in swarm.drones:
        tel = drone.telemetry
        positions[drone.id] = Pose3D(tel.lat, tel.lon, tel.alt_rel)
    
    # Calculate desired formation
    leader = swarm.drones[0]
    lat0, lon0, alt0 = leader.position
    offsets = formation_offsets(shape, len(swarm.drones)-1, spacing)
    
    desired = {leader.id: positions[leader.id]}
    for i, drone in enumerate(swarm.drones[1:]):
        north, east = offsets[i]
        desired[drone.id] = Pose3D(
            lat0 + north/111320,
            lon0 + east/111320,
            alt0
        )
    
    # Apply APF filter
    safe = apf.filter(positions, desired)
    
    # Send safe waypoints
    for drone_id, pos in safe.items():
        swarm.get(drone_id).goto(pos.x, pos.y, pos.z)

safe_formation("v", 5.0)
```

### 4. Swarm Mission Coordination

```python
# Parallel mission upload
def upload_mission(drone, waypoints):
    drone.mission.clear()
    for wp in waypoints:
        drone.mission.add(wp)
    return drone.mission.upload()

# Upload different missions to each drone
import threading
threads = []
for i, drone in enumerate(swarm.drones):
    waypoints = generate_waypoints_for_drone(i)
    t = threading.Thread(
        target=upload_mission,
        args=(drone, waypoints),
        daemon=True
    )
    threads.append(t)
    t.start()

# Wait for all uploads
for t in threads:
    t.join(timeout=30)

# Start all missions simultaneously
for drone in swarm.drones:
    drone.mission.start()
```

### 5. Swarm State Monitoring

```python
from skymeshx.core.fsm import DroneState

# Check if all drones are ready
def all_ready():
    for drone in swarm.drones:
        if not drone.connected:
            return False
        if not drone.armed:
            return False
    return True

# Wait for all drones to reach state
def wait_all_airborne(timeout=60):
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if all(d.telemetry.alt_rel > 5.0 for d in swarm.drones):
            return True
        time.sleep(0.5)
    return False

# Execute when ready
if all_ready():
    swarm.takeoff_all(10.0)
    if wait_all_airborne():
        swarm.formation("v", spacing=5.0)
```

## Use Cases

### 1. Search and Rescue

```python
# Grid search pattern
swarm = Swarm()
for i in range(9):  # 3x3 grid
    swarm.add(f"D{i+1}", f"tcp:127.0.0.1:{5762+i}")

swarm.connect_all()
swarm.arm_all()
swarm.takeoff_all(20.0)

# Spread into grid
swarm.formation("grid", spacing=50.0)

# Each drone searches its sector
for i, drone in enumerate(swarm.drones):
    sector_waypoints = generate_search_pattern(i)
    drone.run_mission(sector_waypoints, wait=False)

# Monitor for target detection
for drone in swarm.drones:
    drone.on("statustext", lambda text, sev, d=drone:
        if "TARGET" in text:
            print(f"{d.id} found target!"))
```

### 2. Aerial Photography

```python
# Leader follows subject, followers provide angles
swarm = Swarm()
swarm.add("leader", "tcp:127.0.0.1:5762")
swarm.add("left", "tcp:127.0.0.1:5763")
swarm.add("right", "tcp:127.0.0.1:5764")
swarm.add("top", "tcp:127.0.0.1:5765")

swarm.connect_all()
swarm.arm_all()
swarm.takeoff_all(15.0)

# Start dynamic following
swarm.start_follow("circle", spacing=10.0, leader="leader", update_hz=2.0)

# Leader tracks subject
leader = swarm.get("leader")
while tracking:
    subject_pos = get_subject_position()
    leader.goto(subject_pos.lat, subject_pos.lon, 15.0)
    time.sleep(0.5)

swarm.stop_follow()
```

### 3. Infrastructure Inspection

```python
# Coordinated inspection of structure
swarm = Swarm()
for i in range(4):
    swarm.add(f"D{i+1}", f"tcp:127.0.0.1:{5762+i}")

swarm.connect_all()
swarm.arm_all()
swarm.takeoff_all(10.0)

# Position around structure
structure_center = (48.137, 11.575)
radius = 20.0

for i, drone in enumerate(swarm.drones):
    angle = i * (360 / len(swarm.drones))
    lat = structure_center[0] + radius * cos(radians(angle)) / 111320
    lon = structure_center[1] + radius * sin(radians(angle)) / 111320
    drone.goto(lat, lon, 15.0)

# Synchronized inspection
for altitude in range(10, 30, 5):
    for drone in swarm.drones:
        drone.goto(drone.lat, drone.lon, altitude)
    time.sleep(10)  # Capture images
```

## Performance Considerations

### Scalability

- **Tested:** Up to 20 drones
- **Theoretical:** 50+ drones (limited by MAVLink bandwidth)
- **Recommended:** 5-10 drones for reliable operation

### Network Bandwidth

- **Per drone:** ~10 KB/s telemetry
- **10 drones:** ~100 KB/s
- **Formation updates:** ~1 KB/s per drone

### CPU Usage

- **Connection management:** ~1% per drone
- **Telemetry processing:** ~2% per drone
- **Formation calculations:** ~5% for 10 drones
- **Total (10 drones):** ~30-40% CPU

### Memory Usage

- **Per drone:** ~5 MB
- **10 drones:** ~50 MB
- **Telemetry history:** ~1 MB per drone per hour

## Best Practices

### 1. Connection Management

```python
# Always check connection results
results = swarm.connect_all(timeout=15.0)
failed = [did for did, ok in results.items() if not ok]
if failed:
    print(f"Failed to connect: {failed}")
    # Handle failures
```

### 2. Error Handling

```python
# Wrap operations in try-except
try:
    swarm.arm_all()
    swarm.takeoff_all(10.0)
except Exception as e:
    print(f"Error: {e}")
    swarm.rtl_all()  # Emergency RTL
```

### 3. Graceful Shutdown

```python
# Always disconnect properly
try:
    # ... operations ...
finally:
    swarm.land_all()
    time.sleep(30)  # Wait for landing
    swarm.disconnect_all()
```

### 4. Formation Spacing

```python
# Adjust spacing based on:
# - Drone size (larger drones need more space)
# - Wind conditions (increase spacing in wind)
# - Maneuver type (tighter for slow, wider for fast)

if wind_speed > 5.0:
    spacing = 8.0  # Wider spacing
else:
    spacing = 5.0  # Normal spacing

swarm.formation("v", spacing=spacing)
```

### 5. Battery Management

```python
# Monitor battery levels
def check_batteries():
    low_battery = []
    for drone in swarm.drones:
        if drone.battery < 30:
            low_battery.append(drone.id)
    return low_battery

# Periodic check
while mission_active:
    low = check_batteries()
    if low:
        print(f"Low battery: {low}")
        swarm.rtl_all()
        break
    time.sleep(10)
```

## Troubleshooting

### Formation Not Working

**Problem:** Drones don't move to formation positions

**Solutions:**
1. Check flight mode (must be GUIDED/OFFBOARD)
2. Verify GPS fix on all drones
3. Check spacing (too small = collisions, too large = out of range)
4. Ensure leader is specified correctly

### Drones Colliding

**Problem:** Drones get too close during formation

**Solutions:**
1. Increase `spacing` parameter
2. Enable APF safety filter
3. Reduce `update_hz` in `start_follow()`
4. Check for GPS drift

### Slow Formation Updates

**Problem:** Followers lag behind leader

**Solutions:**
1. Increase `update_hz` in `start_follow()`
2. Reduce network latency
3. Use faster drones
4. Decrease formation spacing

### Connection Failures

**Problem:** Some drones fail to connect

**Solutions:**
1. Check connection strings
2. Verify SITL/hardware is running
3. Increase timeout in `connect_all()`
4. Check firewall settings