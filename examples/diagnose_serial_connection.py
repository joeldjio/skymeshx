#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose serial connection issues with flight controller.

Usage:
    python examples/diagnose_serial_connection.py COM5 57600
    python examples/diagnose_serial_connection.py COM5 115200
"""
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from pymavlink import mavutil
    print("[OK] pymavlink is installed")
except ImportError:
    print("[ERROR] pymavlink not found. Install with: pip install pymavlink")
    sys.exit(1)

try:
    import serial
    print("[OK] pyserial is installed")
except ImportError:
    print("[ERROR] pyserial not found. Install with: pip install pyserial")
    sys.exit(1)


def test_serial_port(port: str, baud: int):
    """Test if we can open the serial port at all."""
    print(f"\n{'='*60}")
    print(f"Testing {port} at {baud} baud")
    print(f"{'='*60}")
    
    # Step 1: Can we open the port with pyserial?
    print(f"\n[1/4] Testing raw serial port access...")
    try:
        ser = serial.Serial(port, baud, timeout=2)
        print(f"    [OK] Port {port} opened successfully")
        ser.close()
    except serial.SerialException as e:
        print(f"    [ERROR] Failed to open {port}: {e}")
        print(f"\n    Possible causes:")
        print(f"    - Port is already in use by another program")
        print(f"    - Insufficient permissions (try running as admin)")
        print(f"    - Wrong port number (check Device Manager)")
        return False
    
    # Step 2: Try MAVLink connection
    print(f"\n[2/4] Testing MAVLink connection...")
    # pymavlink on Windows: just COMx, baud is passed separately
    print(f"    Connection string: {port} (baud: {baud})")
    
    try:
        mav = mavutil.mavlink_connection(
            port,
            baud=baud,
            source_system=255
        )
        print(f"    [OK] MAVLink connection object created")
    except Exception as e:
        print(f"    [ERROR] Failed to create connection: {e}")
        return False
    
    # Step 3: Wait for heartbeat
    print(f"\n[3/4] Waiting for heartbeat (30 second timeout)...")
    print(f"    Make sure your flight controller is:")
    print(f"    - Powered on")
    print(f"    - Fully booted (wait for LED patterns)")
    print(f"    - Not connected to other software (Mission Planner, QGC, etc.)")
    
    start = time.time()
    hb = mav.wait_heartbeat(timeout=30.0)
    elapsed = time.time() - start
    
    if hb is None:
        print(f"    [ERROR] No heartbeat received after {elapsed:.1f}s")
        print(f"\n    Troubleshooting:")
        print(f"    - Try different baud rate (57600, 115200, 921600)")
        print(f"    - Check if FC is sending MAVLink (not MSP or other protocol)")
        print(f"    - Verify USB cable supports data (not just charging)")
        print(f"    - Try different USB port on your computer")
        print(f"    - Check FC parameters: SERIAL0_PROTOCOL, SERIAL0_BAUD")
        mav.close()
        return False
    
    print(f"    [OK] Heartbeat received after {elapsed:.1f}s!")
    print(f"    System ID: {hb.get_srcSystem()}")
    print(f"    Component ID: {hb.get_srcComponent()}")
    print(f"    MAV Type: {hb.type}")
    print(f"    Autopilot: {hb.autopilot}")
    print(f"    Base Mode: {hb.base_mode}")
    print(f"    Custom Mode: {hb.custom_mode}")
    
    # Step 4: Request a few messages to verify communication
    print(f"\n[4/4] Testing bidirectional communication...")
    
    # Request data streams
    mav.mav.request_data_stream_send(
        hb.get_srcSystem(),
        hb.get_srcComponent(),
        mavutil.mavlink.MAV_DATA_STREAM_ALL,
        4,  # 4 Hz
        1   # start
    )
    print(f"    Requested data streams...")
    
    # Wait for a few messages
    msg_count = 0
    msg_types = set()
    timeout = time.time() + 5.0
    
    while time.time() < timeout and msg_count < 10:
        msg = mav.recv_match(blocking=True, timeout=1.0)
        if msg:
            msg_count += 1
            msg_types.add(msg.get_type())
    
    if msg_count > 0:
        print(f"    [OK] Received {msg_count} messages")
        print(f"    Message types: {', '.join(sorted(msg_types))}")
    else:
        print(f"    [WARN] No messages received (heartbeat only)")
    
    mav.close()
    print(f"\n{'='*60}")
    print(f"[SUCCESS] Connection test PASSED for {port} at {baud} baud")
    print(f"{'='*60}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python diagnose_serial_connection.py PORT BAUD")
        print("Example: python diagnose_serial_connection.py COM5 57600")
        sys.exit(1)
    
    port = sys.argv[1]
    baud = int(sys.argv[2])
    
    print(f"SkyMeshX Serial Connection Diagnostic Tool")
    print(f"Testing connection to {port} at {baud} baud")
    
    success = test_serial_port(port, baud)
    
    if success:
        print(f"\n[SUCCESS] Your flight controller is working correctly!")
        print(f"\nYou can now use:")
        if port.upper().startswith('COM'):
            print(f"  skymeshx connect --port {port} --baud {baud}")
            print(f"  skymeshx status --port {port} --baud {baud}")
            print(f"\nNote: On Windows, you may need to use the format:")
            print(f"  skymeshx connect --port serial:{port}:{baud}")
        else:
            print(f"  skymeshx connect --port {port}:{baud}")
            print(f"  skymeshx status --port {port}:{baud}")
        sys.exit(0)
    else:
        print(f"\n[FAILED] Connection test failed. See troubleshooting steps above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
