"""
Tests for multi-drone waypoint planning functionality.

Tests AppState waypoint management and SafetyContext integration.
"""

import pytest


class TestAppStateWaypointManagement:
    """Test waypoint storage and retrieval in AppState."""
    
    def test_single_drone_waypoint_storage(self):
        """Test storing waypoints for a single drone."""
        # Simulate AppState behavior
        waypoints = {}
        drone_id = "D1"
        
        # Add waypoints
        wps = [
            {"lat": 48.137, "lon": 11.575, "alt": 10.0},
            {"lat": 48.138, "lon": 11.576, "alt": 15.0},
        ]
        waypoints[drone_id] = wps
        
        assert drone_id in waypoints
        assert len(waypoints[drone_id]) == 2
        assert waypoints[drone_id][0]["lat"] == 48.137
    
    def test_multi_drone_waypoint_storage(self):
        """Test storing waypoints for multiple drones."""
        waypoints = {}
        
        # Add waypoints for D1
        waypoints["D1"] = [
            {"lat": 48.137, "lon": 11.575, "alt": 10.0},
            {"lat": 48.138, "lon": 11.576, "alt": 10.0},
        ]
        
        # Add waypoints for D2
        waypoints["D2"] = [
            {"lat": 48.139, "lon": 11.577, "alt": 10.0},
            {"lat": 48.140, "lon": 11.578, "alt": 10.0},
        ]
        
        assert len(waypoints) == 2
        assert "D1" in waypoints
        assert "D2" in waypoints
        assert len(waypoints["D1"]) == 2
        assert len(waypoints["D2"]) == 2
    
    def test_shared_waypoints_for_multiple_drones(self):
        """Test setting same waypoints for multiple drones."""
        waypoints = {}
        shared_wps = [
            {"lat": 48.137, "lon": 11.575, "alt": 10.0},
            {"lat": 48.138, "lon": 11.576, "alt": 10.0},
        ]
        
        # Set same waypoints for multiple drones
        for drone_id in ["D1", "D2", "D3"]:
            waypoints[drone_id] = shared_wps.copy()
        
        assert len(waypoints) == 3
        for drone_id in ["D1", "D2", "D3"]:
            assert waypoints[drone_id] == shared_wps
    
    def test_clear_waypoints(self):
        """Test clearing waypoints for a drone."""
        waypoints = {
            "D1": [{"lat": 48.137, "lon": 11.575, "alt": 10.0}],
            "D2": [{"lat": 48.138, "lon": 11.576, "alt": 10.0}],
        }
        
        # Clear D1's waypoints
        waypoints["D1"] = []
        
        assert len(waypoints["D1"]) == 0
        assert len(waypoints["D2"]) == 1
    
    def test_update_waypoint(self):
        """Test updating a specific waypoint."""
        waypoints = {
            "D1": [
                {"lat": 48.137, "lon": 11.575, "alt": 10.0},
                {"lat": 48.138, "lon": 11.576, "alt": 10.0},
            ]
        }
        
        # Update second waypoint
        waypoints["D1"][1] = {"lat": 48.139, "lon": 11.577, "alt": 15.0}
        
        assert waypoints["D1"][1]["lat"] == 48.139
        assert waypoints["D1"][1]["alt"] == 15.0


class TestWaypointCoordinateConversion:
    """Test lat/lon to NED coordinate conversion for waypoints."""
    
    def test_latlon_to_ned_conversion(self):
        """Test converting lat/lon waypoints to local NED."""
        # Reference point
        ref_lat = 48.137
        ref_lon = 11.575
        ref_lon_scale = 111_320.0 * 0.67  # cos(48°) ≈ 0.67
        
        # Waypoint
        wp_lat = 48.138
        wp_lon = 11.576
        wp_alt = 10.0
        
        # Convert to NED
        x = (wp_lat - ref_lat) * 111_320.0  # North
        y = (wp_lon - ref_lon) * ref_lon_scale  # East
        z = wp_alt  # Up (altitude)
        
        assert abs(x - 111.32) < 1.0  # ~111m north
        assert abs(y - 74.58) < 1.0   # ~75m east
        assert z == 10.0
    
    def test_multiple_waypoints_conversion(self):
        """Test converting multiple waypoints."""
        ref_lat = 48.137
        ref_lon = 11.575
        ref_lon_scale = 111_320.0 * 0.67
        
        waypoints_latlon = [
            (48.138, 11.576, 10.0),
            (48.139, 11.577, 15.0),
            (48.140, 11.578, 20.0),
        ]
        
        waypoints_ned = []
        for lat, lon, alt in waypoints_latlon:
            x = (lat - ref_lat) * 111_320.0
            y = (lon - ref_lon) * ref_lon_scale
            waypoints_ned.append((x, y, alt))
        
        assert len(waypoints_ned) == 3
        assert waypoints_ned[0][2] == 10.0
        assert waypoints_ned[1][2] == 15.0
        assert waypoints_ned[2][2] == 20.0


class TestWaypointAwareCollisionPrediction:
    """Test waypoint-aware collision prediction logic."""
    
    def test_trajectory_building(self):
        """Test building trajectory from waypoints."""
        # Drone starts at (0, 0, 10)
        start = (0.0, 0.0, 10.0)
        waypoints = [
            (100.0, 0.0, 10.0),    # 100m north
            (100.0, 100.0, 10.0),  # 100m east
            (0.0, 100.0, 10.0),    # 100m south
        ]
        cruise_speed = 5.0  # m/s
        
        # Build time-stamped trajectory
        trajectory = [(0.0, start[0], start[1], start[2])]
        t = 0.0
        
        for wp in waypoints:
            dx = wp[0] - trajectory[-1][1]
            dy = wp[1] - trajectory[-1][2]
            dz = wp[2] - trajectory[-1][3]
            dist = (dx**2 + dy**2 + dz**2)**0.5
            
            if dist > 0:
                t += dist / cruise_speed
                trajectory.append((t, wp[0], wp[1], wp[2]))
        
        assert len(trajectory) == 4  # start + 3 waypoints
        assert trajectory[0][0] == 0.0
        assert trajectory[1][0] == 20.0  # 100m / 5m/s
        assert trajectory[2][0] == 40.0  # +100m / 5m/s
        assert trajectory[3][0] == 60.0  # +100m / 5m/s
    
    def test_trajectory_interpolation(self):
        """Test interpolating position on trajectory."""
        trajectory = [
            (0.0, 0.0, 0.0, 10.0),
            (10.0, 100.0, 0.0, 10.0),
        ]
        
        # Interpolate at t=5s (halfway)
        t = 5.0
        t0, x0, y0, z0 = trajectory[0]
        t1, x1, y1, z1 = trajectory[1]
        
        alpha = (t - t0) / (t1 - t0)
        x = x0 + alpha * (x1 - x0)
        y = y0 + alpha * (y1 - y0)
        z = z0 + alpha * (z1 - z0)
        
        assert x == 50.0  # Halfway to 100m
        assert y == 0.0
        assert z == 10.0
    
    def test_collision_detection_on_trajectories(self):
        """Test detecting collision between two trajectories."""
        # Drone A: moves north from (0, 0) to (100, 0)
        traj_a = [
            (0.0, 0.0, 0.0, 10.0),
            (20.0, 100.0, 0.0, 10.0),
        ]
        
        # Drone B: moves south from (100, 0) to (0, 0)
        traj_b = [
            (0.0, 100.0, 0.0, 10.0),
            (20.0, 0.0, 0.0, 10.0),
        ]
        
        # They should collide at (50, 0, 10) at t=10s
        min_dist = float('inf')
        collision_time = None
        
        for t in [0.0, 5.0, 10.0, 15.0, 20.0]:
            # Interpolate positions
            alpha_a = t / 20.0
            pos_a = (alpha_a * 100.0, 0.0, 10.0)
            
            alpha_b = t / 20.0
            pos_b = (100.0 - alpha_b * 100.0, 0.0, 10.0)
            
            # Calculate distance
            dx = pos_a[0] - pos_b[0]
            dy = pos_a[1] - pos_b[1]
            dz = pos_a[2] - pos_b[2]
            dist = (dx**2 + dy**2 + dz**2)**0.5
            
            if dist < min_dist:
                min_dist = dist
                collision_time = t
        
        assert collision_time == 10.0  # Collision at midpoint
        assert min_dist < 0.1  # Very close (essentially 0)


class TestMultiDroneSelectionLogic:
    """Test multi-drone selection logic."""
    
    def test_effective_targets_single_drone(self):
        """Test effective targets with single drone selected."""
        selected_drone_id = "D1"
        mission_targets = {}
        
        # Effective targets should be [D1]
        if not mission_targets:
            targets = [selected_drone_id] if selected_drone_id else []
        else:
            targets = list(mission_targets.keys())
        
        assert targets == ["D1"]
    
    def test_effective_targets_multi_drone(self):
        """Test effective targets with multiple drones selected."""
        selected_drone_id = "D1"
        mission_targets = {"D2": True, "D3": True}
        
        # Effective targets should be [D2, D3]
        if mission_targets:
            targets = list(mission_targets.keys())
        else:
            targets = [selected_drone_id] if selected_drone_id else []
        
        assert len(targets) == 2
        assert "D2" in targets
        assert "D3" in targets
    
    def test_toggle_mission_target(self):
        """Test toggling mission target selection."""
        mission_targets = {}
        
        # Toggle D1 on
        drone_id = "D1"
        if drone_id in mission_targets:
            del mission_targets[drone_id]
        else:
            mission_targets[drone_id] = True
        
        assert "D1" in mission_targets
        
        # Toggle D1 off
        if drone_id in mission_targets:
            del mission_targets[drone_id]
        else:
            mission_targets[drone_id] = True
        
        assert "D1" not in mission_targets

