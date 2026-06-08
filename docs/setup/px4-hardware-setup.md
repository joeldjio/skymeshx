# PX4 Hardware Setup Guide

## Overview

This guide explains how to set up **real PX4 hardware** (actual drones) with the UAV Research Platform using uXRCE-DDS for ROS2 integration.

**Important**: This is for **real hardware**, not simulation. For SITL/Gazebo setup, see [px4-sitl-automation.md](px4-sitl-automation.md).

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Ground Station │         │ Companion Comp.  │         │   Flight Ctrl   │
│   (Your PC)     │◄───────►│  (Raspberry Pi)  │◄───────►│     (PX4)       │
│                 │  WiFi   │                  │  Serial │                 │
│  - UI (PyQt6)   │         │  - uXRCE Agent   │  or USB │  - Firmware     │
│  - ROS2 Nodes   │         │  - ROS2 Bridge   │         │  - Sensors      │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Prerequisites

### Hardware Requirements

1. **Flight Controller** with PX4 v1.14+ firmware
   - Pixhawk 4/5/6
   - Holybro Kakute H7
   - CUAV V5+/V6X
   - Any PX4-compatible FC

2. **Companion Computer** (one of):
   - Raspberry Pi 4 (recommended: 4GB+ RAM)
   - Raspberry Pi 5
   - NVIDIA Jetson Nano/Xavier
   - Any Linux SBC with ROS2 support

3. **Connection** between FC and Companion:
   - USB cable (easiest)
   - UART/Serial (TELEM2 port)
   - Ethernet (on supported FCs)

4. **Network**:
   - WiFi router or access point
   - Ground station and companion on same network

### Software Requirements

**On Companion Computer:**
- Ubuntu 22.04 (Jammy) or 24.04 (Noble)
- ROS2 Humble or Jazzy
- Python 3.10+

**On Ground Station:**
- Windows 10/11, Ubuntu 22.04+, or macOS
- Python 3.10+
- UAV Research Platform installed

## Quick Start

```bash
# On Companion Computer
sudo systemctl start uxrce-agent  # Start uXRCE-DDS Agent

# On Ground Station
python -m tools.ui
# → Go to ROS2 tab
# → Enter namespace: px4_0
# → Click "Connect"
```

## Detailed Setup

### Step 1: Flash PX4 Firmware

1. Download [QGroundControl](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html)

2. Connect FC to PC via USB

3. In QGC:
   - Go to **Vehicle Setup** → **Firmware**
   - Select **PX4 Flight Stack**
   - Choose **Standard Version** (v1.14.0 or newer)
   - Click **OK** to flash

4. Verify version in QGC MAVLink Console:
   ```bash
   ver all
   # Should show: PX4 v1.14.x or newer
   ```

### Step 2: Configure PX4 for uXRCE-DDS

In QGC, set these parameters:

```
UXRCE_DDS_CFG = 102      # TELEM2 port
SER_TEL2_BAUD = 921600   # Baud rate
MAV_1_CONFIG = Disabled  # Free up TELEM2
```

Reboot FC after changing parameters.

### Step 3: Setup Companion Computer

See detailed guide: [Raspberry Pi Setup](raspberry-pi.md)

**Quick version:**

```bash
# Install ROS2 Humble
sudo apt update
sudo apt install -y ros-humble-desktop

# Install uXRCE-DDS Agent
pip3 install --user uxrce_dds_agent

# Install px4_msgs
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/PX4/px4_msgs.git -b release/1.14
cd ~/ros2_ws && colcon build
source install/setup.bash

# Install UAV Research Platform
cd ~
git clone https://github.com/yourusername/uavresearchproject.git
cd uavresearchproject
pip3 install -e ".[ros]"
```

### Step 4: Start uXRCE-DDS Agent

**Manual start:**
```bash
MicroXRCEAgent serial --dev /dev/ttyACM0 -b 921600
```

**As systemd service (recommended):**

```bash
# Create service file
sudo nano /etc/systemd/system/uxrce-agent.service
```

```ini
[Unit]
Description=Micro XRCE-DDS Agent
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/home/pi/.local/bin/MicroXRCEAgent serial --dev /dev/ttyACM0 -b 921600
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable uxrce-agent
sudo systemctl start uxrce-agent
```

### Step 5: Verify Connection

```bash
# Check ROS2 topics
ros2 topic list | grep fmu

# Should see:
# /fmu/out/vehicle_status
# /fmu/out/vehicle_local_position
# /fmu/out/vehicle_attitude
# etc.

# Echo a topic
ros2 topic echo /fmu/out/vehicle_status
```

### Step 6: Connect from Ground Station

1. **Launch UI:**
   ```bash
   python -m tools.ui
   ```

2. **Go to ROS2 tab**

3. **Enter namespace:** `px4_0` (or your namespace)

4. **Click "Connect"**

5. **Verify telemetry** is updating in Dashboard

## Connection Types

### USB Connection (Easiest)

**Pros:** Simple, no wiring, high speed
**Cons:** Cable can disconnect in flight

```bash
# Find device
ls /dev/ttyACM*

# Start agent
MicroXRCEAgent serial --dev /dev/ttyACM0 -b 921600
```

### Serial/UART Connection (Recommended)

**Pros:** Reliable, no USB cable
**Cons:** Requires wiring

**Wiring:**
- FC TELEM2 TX → Companion RX
- FC TELEM2 RX → Companion TX
- FC GND → Companion GND

```bash
# Find device
ls /dev/ttyS*  # or /dev/ttyUSB* for USB-to-Serial

# Start agent
MicroXRCEAgent serial --dev /dev/ttyS0 -b 921600
```

### UDP/WiFi Connection

**Pros:** Wireless
**Cons:** Requires WiFi telemetry module

```bash
# On companion
MicroXRCEAgent udp4 -p 8888

# On FC (via MAVLink shell)
uxrce_dds_client start -t udp -h <companion_ip> -p 8888
```

## Multi-Vehicle Setup

For multiple drones:

1. **On each FC**, set unique namespace:
   ```bash
   # In QGC MAVLink Console
   uxrce_dds_client start -t serial -d /dev/ttyACM0 -b 921600 -n uav_1
   # For second drone: -n uav_2, etc.
   ```

2. **On companion**, start one agent per drone:
   ```bash
   # Terminal 1 (Drone 1)
   MicroXRCEAgent serial --dev /dev/ttyACM0 -b 921600

   # Terminal 2 (Drone 2)
   MicroXRCEAgent serial --dev /dev/ttyACM1 -b 921600
   ```

3. **In UI**, connect to each namespace separately

## Troubleshooting

### No ROS2 Topics

**Check agent:**
```bash
sudo systemctl status uxrce-agent
journalctl -u uxrce-agent -f
```

**Check PX4 client:**
```bash
# In QGC MAVLink Console
uxrce_dds_client status
# Should show: Running
```

### Connection Timeout

**Check network:**
```bash
ping <companion_ip>
```

**Check firewall:**
```bash
sudo ufw allow 7400:7500/udp
sudo ufw allow 7400:7500/tcp
```

### Serial Permission Denied

```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

## Safety Considerations

⚠️ **IMPORTANT SAFETY RULES:**

1. **Always remove propellers** when testing indoors
2. **Use a kill switch** or have QGC ready to disarm
3. **Test in open area** for first flights
4. **Monitor battery voltage** - low voltage causes crashes
5. **Have manual RC control** as backup
6. **Check GPS lock** before autonomous flight
7. **Set geofence** in QGC for safety
8. **Never fly over people**
9. **Follow local regulations**

## Next Steps

- [Mission Upload](px4-mission-upload.md) - Upload waypoint missions
- [Mission Monitoring](px4-mission-monitoring.md) - Track mission progress
- [Frame Visualization](px4-frame-visualization.md) - Debug coordinate frames

## Related Documentation

- [PX4 User Guide](https://docs.px4.io/main/en/)
- [PX4 ROS2 Guide](https://docs.px4.io/main/en/ros2/user_guide.html)
- [uXRCE-DDS](https://docs.px4.io/main/en/middleware/uxrce_dds.html)
- [ROS2 Humble Docs](https://docs.ros.org/en/humble/)