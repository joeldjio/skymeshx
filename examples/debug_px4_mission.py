#!/usr/bin/env python3
"""
Debug script: mission navigation diagnostics.

Executes a simple waypoint mission and logs all telemetry changes.
"""
import argparse
import time
import json
from skymeshx.sdk.drone import Drone

def main():
    parser = argparse.ArgumentParser(description="PX4 mission debug")
    parser.add_argument("--port", default="udp:127.0.0.1:14550", help="Connection string")
    parser.add_argument("--lat-offset", type=float, default=0.00005, help="Lat offset from home (degrees)")
    parser.add_argument("--lon-offset", type=float, default=0.00005, help="Lon offset from home (degrees)")
    parser.add_argument("--altitude", type=float, default=15.0, help="Waypoint altitude (m)")
    args = parser.parse_args()

    print(f"[DEBUG] Connecting to {args.port}...")
    drone = Drone(args.port, drone_id="mission_debug")
    ok = drone.connect(timeout=10.0)
    if not ok:
        print("[ERROR] Failed to connect.")
        return 1

    print("[DEBUG] Connected.")
    tel = drone.telemetry
    home_lat = tel.lat
    home_lon = tel.lon
    print(f"[DEBUG] Home location: {home_lat:.8f}, {home_lon:.8f}")

    print("[DEBUG] Arming...")
    drone.arm(timeout=10.0)
    time.sleep(1.0)

    print(f"[DEBUG] Takeoff to {args.altitude}m...")
    drone.takeoff(altitude=args.altitude, timeout=30.0)
    time.sleep(2.0)

    # Define 3 waypoints
    wp1_lat = home_lat + args.lat_offset
    wp1_lon = home_lon + args.lon_offset
    wp2_lat = home_lat + args.lat_offset * 2
    wp2_lon = home_lon
    wp3_lat = home_lat
    wp3_lon = home_lon + args.lon_offset

    waypoints = [
        {"lat": wp1_lat, "lon": wp1_lon, "alt": args.altitude},
        {"lat": wp2_lat, "lon": wp2_lon, "alt": args.altitude},
        {"lat": wp3_lat, "lon": wp3_lon, "alt": args.altitude},
    ]

    print(f"\n[DEBUG] Waypoints:")
    for i, wp in enumerate(waypoints, 1):
        print(f"  WP{i}: {wp['lat']:.8f}, {wp['lon']:.8f} @ {wp['alt']}m")

    print(f"\n[DEBUG] Starting mission with {len(waypoints)} waypoints...")
    start_time = time.time()
    
    for i, wp in enumerate(waypoints, 1):
        print(f"\n[DEBUG] Navigating to WP{i}...")
        wp_start = time.time()
        
        try:
            drone.goto(wp["lat"], wp["lon"], wp["alt"], timeout=120.0)
        except Exception as e:
            print(f"[ERROR] goto failed: {e}")
            break
        
        wp_elapsed = time.time() - wp_start
        tel = drone.telemetry
        print(f"  Reached (or timed out after {wp_elapsed:.1f}s)")
        print(f"  Current: {tel.lat:.8f}, {tel.lon:.8f} @ {tel.alt_rel:.1f}m")
        
        # Measure distance to waypoint
        dlat = (wp["lat"] - tel.lat) * 111320.0
        dlon = (wp["lon"] - tel.lon) * 111320.0
        dist = (dlat**2 + dlon**2) ** 0.5
        print(f"  Distance to WP: {dist:.1f}m")
        
        time.sleep(1.0)

    total_elapsed = time.time() - start_time
    print(f"\n[DEBUG] Mission complete (total {total_elapsed:.1f}s)")
    
    tel = drone.telemetry
    print(f"[DEBUG] Final position: {tel.lat:.8f}, {tel.lon:.8f} @ {tel.alt_rel:.1f}m")

    print("\n[DEBUG] Landing...")
    drone.land(timeout=30.0)
    
    print("[DEBUG] Disconnecting...")
    drone.disconnect()
    print("[DEBUG] Done.")
    return 0

if __name__ == "__main__":
    exit(main())
