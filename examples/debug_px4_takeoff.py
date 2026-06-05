#!/usr/bin/env python3
"""
Debug script: diagnose PX4 SITL takeoff & altitude limits.

This script:
1. Connects to PX4 (via MAVLink)
2. Prints system health, parameters, geofence
3. Arms the drone
4. Executes takeoff with live telemetry output
5. Attempts mission flight
6. Lands

Usage:
    python3 examples/debug_px4_takeoff.py --port tcp:127.0.0.1:14550
"""
import argparse
import time
from droneresearch.sdk.drone import Drone

def print_system_info(drone):
    """Print PX4 system info and parameters."""
    tel = drone.telemetry
    print("\n=== System Info ===")
    print(f"Autopilot:    {tel.autopilot}")
    print(f"Vehicle Type: {tel.vehicle_type}")
    print(f"GPS Fix:      {tel.gps_fix}")
    print(f"Satellites:   {tel.satellites}")
    print(f"System Status:{tel.system_status}")

def live_telemetry_loop(drone, duration_s=30, interval_hz=2):
    """Print live telemetry during a time window."""
    interval = 1.0 / max(interval_hz, 1)
    t_start = time.time()
    print(f"\n=== Live Telemetry ({duration_s}s @ {interval_hz} Hz) ===")
    print("Time(s) | Alt(m) | AltRel(m) | Mode       | Armed | Bat% | GndSpd(m/s)")
    print("--------|--------|-----------|------------|-------|------|------------")
    
    while time.time() - t_start < duration_s:
        tel = drone.telemetry
        elapsed = time.time() - t_start
        mode = (tel.flight_mode or "UNKNOWN")[:10]
        print(
            f"{elapsed:7.1f} | {tel.alt:6.1f} | {tel.alt_rel:9.2f} | {mode:10s} | "
            f"{'Y' if tel.armed else 'N':5s} | {tel.battery_pct:5.1f} | {tel.groundspeed:10.1f}"
        )
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="PX4 SITL takeoff debug")
    parser.add_argument("--port", default="udp:127.0.0.1:14550", help="Connection string")
    parser.add_argument("--altitude", type=float, default=10.0, help="Takeoff altitude (m)")
    parser.add_argument("--timeout", type=float, default=60.0, help="Takeoff timeout (s)")
    args = parser.parse_args()

    print(f"[DEBUG] Connecting to {args.port}...")
    drone = Drone(args.port, drone_id="debug_drone")
    ok = drone.connect(timeout=10.0)
    if not ok:
        print("[ERROR] Failed to connect.")
        return 1

    print("[DEBUG] Connected.")
    print_system_info(drone)

    print("\n[DEBUG] Arming...")
    drone.arm(timeout=10.0)
    time.sleep(1.0)

    print(f"\n[DEBUG] Taking off to {args.altitude}m (timeout: {args.timeout}s)...")
    t_start = time.time()
    drone.takeoff(altitude=args.altitude, timeout=args.timeout)
    elapsed = time.time() - t_start
    print(f"[DEBUG] Takeoff command sent (took {elapsed:.1f}s).")

    print("\n[DEBUG] Monitoring telemetry during climb...")
    live_telemetry_loop(drone, duration_s=20, interval_hz=2)

    tel = drone.telemetry
    print(f"\n[DEBUG] Final state:")
    print(f"  Alt Rel:     {tel.alt_rel:.2f}m")
    print(f"  Flight Mode: {tel.flight_mode}")
    print(f"  Armed:       {tel.armed}")

    if tel.alt_rel >= args.altitude * 0.85:
        print(f"[OK] Reached target altitude ({tel.alt_rel:.1f}m >= {args.altitude * 0.85:.1f}m).")
    else:
        print(f"[WARN] Did not reach target altitude ({tel.alt_rel:.1f}m < {args.altitude * 0.85:.1f}m).")
        print("[HINT] Check PX4 preflight, geofence, or motor limits.")

    print("\n[DEBUG] Landing...")
    drone.land(timeout=30.0)
    
    print("[DEBUG] Disconnecting...")
    drone.disconnect()
    print("[DEBUG] Done.")
    return 0

if __name__ == "__main__":
    exit(main())
