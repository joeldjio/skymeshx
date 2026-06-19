#!/usr/bin/env python3
"""
PX4 parameter & environment diagnostic.

Checks for known altitude/simulation limits that might prevent flight.
"""
import subprocess
import sys

def check_px4_nsh():
    """Try to connect to PX4 nsh console and query parameters."""
    print("\n=== PX4 nsh Console Parameters ===")
    print("(Requires pxh> prompt accessible, e.g. via serial or MAVLink nsh forwarding)")
    print("\nIf you have access to the nsh prompt in PX4, run these commands:")
    print("  param show *MAX*")
    print("  param show *GEO*")
    print("  param show *ALT*")
    print("\nLook for:")
    print("  - MPC_Z_MAX (max climb rate, should be >1)")
    print("  - MPC_ALT_MODE (altitude reference, should be 0=relative)")
    print("  - GEO_FENCE_* (geofence parameters)")
    print("  - COM_DISARM_PREFLT (preflight disarm timeout)")

def check_gazebo_world():
    """Check if Gazebo world is available and what models exist."""
    print("\n=== Gazebo / Ignition Environment ===")
    try:
        result = subprocess.run(
            ["gz", "model", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            models = result.stdout.strip().split('\n') if result.stdout.strip() else []
            print(f"Models in Gazebo world: {models}")
            if "x500" in str(models).lower():
                print("  ✓ x500 (PX4 default) found")
            else:
                print("  ⚠ x500 NOT found — check if gz_x500 world is loaded")
        else:
            print(f"Error listing models: {result.stderr}")
    except Exception as e:
        print(f"Could not check Gazebo: {e}")
        print("Make sure 'gz' is installed and Gazebo is running.")

def check_ignition_version():
    """Check Ignition/Gazebo version."""
    print("\n=== Ignition / Gazebo Version ===")
    try:
        result = subprocess.run(
            ["gz", "gui", "--versions"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(result.stdout)
    except Exception as e:
        print(f"Could not check version: {e}")

def main():
    print("PX4 SITL Diagnostic Report")
    print("=" * 50)
    
    check_ignition_version()
    check_gazebo_world()
    check_px4_nsh()
    
    print("\n=== Recommended Steps ===")
    print("1. If Gazebo shows no models:")
    print("   $ cd ~/Firmware")
    print("   $ export PX4_UXRCE_DDS_NS=uav_1")
    print("   $ make px4_sitl gz_x500")
    print("")
    print("2. Check PX4 health (in nsh or QGC):")
    print("   - GPS fix (should be 3 or 4)")
    print("   - Preflight checks passing")
    print("   - No motor/actuator errors")
    print("")
    print("3. If takeoff stops at 5m:")
    print("   - Check geofence limits: param show | grep GEO")
    print("   - Check max altitude: param show | grep ALT")
    print("   - Check preflight timeout: param show | grep COM_DISARM")
    print("")
    print("4. Run the debug script:")
    print("   $ python3 examples/debug_px4_takeoff.py --altitude 20")
    print("")
    print("5. Check MAVLink telemetry in real-time:")
    print("   $ python3 -c 'from skymeshx.sdk.drone import Drone;")
    print("     d = Drone(\"tcp:127.0.0.1:14550\"); d.connect(); ")
    print("     import time; [print(f\"{d.telemetry.alt_rel:.2f}m\") or time.sleep(0.1) for _ in range(100)]'")

if __name__ == "__main__":
    main()
