# Windows Serial Connection Guide

## Connecting to Flight Controller via COM Port

SkyMeshX supports direct serial connections to flight controllers on Windows using COM ports.

## Quick Start

### 1. Find Your COM Port

Open **Device Manager** (Geräte-Manager) and look under "Ports (COM & LPT)" to find your flight controller's COM port (e.g., COM5).

### 2. Determine Baud Rate

Most ArduPilot flight controllers use one of these baud rates:
- **57600** - Standard for older FCs
- **115200** - Most common for modern FCs (default in Mission Planner)
- **921600** - High-speed connections

Check your Mission Planner or QGroundControl settings to see which baud rate you normally use.

### 3. Connect Using CLI

```bash
# Using 115200 baud (most common)
python -m skymeshx.cli.main connect --port COM5 --baud 115200

# Using 57600 baud
python -m skymeshx.cli.main connect --port COM5 --baud 57600

# Check status
python -m skymeshx.cli.main status --port COM5 --baud 115200

# Arm the drone (be careful!)
python -m skymeshx.cli.main arm --port COM5 --baud 115200
```

### 4. Using in Python Scripts

```python
from skymeshx import Drone

# Connect to COM5 at 115200 baud
drone = Drone("COM5", baud=115200)

if drone.connect(timeout=15.0):
    print(f"Connected to {drone.telemetry.autopilot}")
    print(f"Position: {drone.lat:.6f}, {drone.lon:.6f}")
    print(f"Altitude: {drone.alt_rel:.1f}m")
    print(f"Battery: {drone.battery_pct:.0f}%")
    print(f"GPS: {drone.satellites} satellites")
    
    drone.disconnect()
else:
    print("Connection failed!")
```

## Troubleshooting

### Connection Timeout

If you get a timeout error:

1. **Check if port is in use**: Close Mission Planner, QGroundControl, or any other software using the COM port
2. **Verify COM port**: Check Device Manager to confirm the correct port number
3. **Try different baud rate**: Test both 57600 and 115200
4. **Check USB cable**: Some cables are charge-only and don't support data
5. **Wait for FC boot**: Give the flight controller 10-15 seconds to fully boot before connecting

### Diagnostic Tool

Use the diagnostic script to test your connection:

```bash
python examples/diagnose_serial_connection.py COM5 115200
```

This will:
- Test if the port can be opened
- Wait for MAVLink heartbeat
- Display autopilot information
- Verify bidirectional communication

### Permission Issues

If you get "Access Denied" errors:
- Run your terminal/IDE as Administrator
- Check if another program has locked the port
- Restart your computer to release any stuck port locks

## Advanced Usage

### Environment Variable

Set a default connection string:

```bash
# PowerShell
$env:DRONE_PORT = "COM5"
$env:DRONE_BAUD = "115200"

# Then just use:
python -m skymeshx.cli.main connect --baud 115200
```

### Multiple Drones

Connect to multiple flight controllers:

```python
from skymeshx import Drone

drone1 = Drone("COM5", drone_id="UAV1", baud=115200)
drone2 = Drone("COM6", drone_id="UAV2", baud=115200)

drone1.connect()
drone2.connect()

# Now control both drones
```

## Supported Autopilots

- ✅ ArduPilot (Copter, Plane, Rover)
- ✅ PX4 (via MAVLink)
- ✅ Any MAVLink-compatible autopilot

## Common Baud Rates

| Baud Rate | Use Case |
|-----------|----------|
| 9600      | Very old hardware |
| 57600     | Standard ArduPilot |
| 115200    | Modern FCs (recommended) |
| 230400    | High-speed telemetry |
| 921600    | Maximum speed |

## See Also

- [Installation Guide](installation.md)
- [Frame Conventions](frame-conventions.md)
- [CLI Documentation](../api/overview.md)