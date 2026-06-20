"""
Tests for Solar Park Inspection Planning.

Validates waypoint generation, gimbal control, camera triggering,
and mission planning for solar panel inspection operations.
"""

import pytest
import math

from skymeshx.control.solar_inspection import (
    SolarParkInspectionPlanner,
    PanelRow,
    InspectionConfig
)
from skymeshx.control.mission import Waypoint


class TestPanelRow:
    """Test PanelRow dataclass validation."""
    
    def test_valid_panel_row(self):
        """Valid panel row should be created successfully."""
        row = PanelRow(
            start=(48.137, 11.575),
            end=(48.138, 11.575),
            width=2.0
        )
        assert row.start == (48.137, 11.575)
        assert row.end == (48.138, 11.575)
        assert row.width == 2.0
    
    def test_panel_row_same_start_end(self):
        """Panel row with same start and end should raise ValueError."""
        with pytest.raises(ValueError, match="start and end must be different"):
            PanelRow(
                start=(48.137, 11.575),
                end=(48.137, 11.575)
            )
    
    def test_panel_row_negative_width(self):
        """Panel row with negative width should raise ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            PanelRow(
                start=(48.137, 11.575),
                end=(48.138, 11.575),
                width=-1.0
            )


class TestInspectionConfig:
    """Test InspectionConfig dataclass validation."""
    
    def test_valid_config(self):
        """Valid inspection config should be created successfully."""
        config = InspectionConfig(
            altitude=15.0,
            gimbal_pitch=-90.0,
            overlap=0.3,
            speed=3.0
        )
        assert config.altitude == 15.0
        assert config.gimbal_pitch == -90.0
        assert config.overlap == 0.3
        assert config.speed == 3.0
    
    def test_config_negative_altitude(self):
        """Config with negative altitude should raise ValueError."""
        with pytest.raises(ValueError, match="Altitude must be positive"):
            InspectionConfig(altitude=-5.0)
    
    def test_config_invalid_overlap(self):
        """Config with invalid overlap should raise ValueError."""
        with pytest.raises(ValueError, match="Overlap must be between 0 and 1"):
            InspectionConfig(overlap=1.5)
        
        with pytest.raises(ValueError, match="Overlap must be between 0 and 1"):
            InspectionConfig(overlap=-0.1)
    
    def test_config_negative_speed(self):
        """Config with negative speed should raise ValueError."""
        with pytest.raises(ValueError, match="Speed must be positive"):
            InspectionConfig(speed=-1.0)
    
    def test_config_invalid_gimbal_pitch(self):
        """Config with invalid gimbal pitch should raise ValueError."""
        with pytest.raises(ValueError, match="Gimbal pitch must be between -90 and 90"):
            InspectionConfig(gimbal_pitch=-95.0)
        
        with pytest.raises(ValueError, match="Gimbal pitch must be between -90 and 90"):
            InspectionConfig(gimbal_pitch=95.0)


class TestSolarParkInspectionPlanner:
    """Test SolarParkInspectionPlanner functionality."""
    
    def test_planner_initialization(self):
        """Planner should initialize successfully."""
        planner = SolarParkInspectionPlanner()
        assert planner._home_position is None
    
    def test_set_home_position(self):
        """Setting home position should work correctly."""
        planner = SolarParkInspectionPlanner()
        planner.set_home_position(48.137, 11.575)
        assert planner._home_position == (48.137, 11.575)
    
    def test_plan_inspection_empty_rows(self):
        """Planning with empty rows should raise ValueError."""
        planner = SolarParkInspectionPlanner()
        config = InspectionConfig()
        
        with pytest.raises(ValueError, match="At least one panel row required"):
            planner.plan_inspection([], config)
    
    def test_plan_inspection_single_row(self):
        """Planning inspection for single row should generate waypoints."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(
                start=(48.137, 11.575),
                end=(48.138, 11.575)
            )
        ]
        config = InspectionConfig(
            altitude=15.0,
            gimbal_pitch=-90.0,
            trigger_distance=5.0
        )
        
        waypoints = planner.plan_inspection(rows, config, add_rtl=False)
        
        # Should have navigation waypoints + gimbal + camera triggers
        assert len(waypoints) > 0
        
        # Check first waypoint is navigation
        assert waypoints[0].cmd == 16  # MAV_CMD_NAV_WAYPOINT
        assert waypoints[0].alt == 15.0
        
        # Check gimbal control waypoint exists
        gimbal_waypoints = [wp for wp in waypoints if wp.cmd == 205]
        assert len(gimbal_waypoints) > 0
        assert gimbal_waypoints[0].param1 == -90.0  # Pitch
        
        # Check camera trigger waypoints exist
        camera_waypoints = [wp for wp in waypoints if wp.cmd == 203]
        assert len(camera_waypoints) > 0
        assert camera_waypoints[0].param5 == 1.0  # Trigger
    
    def test_plan_inspection_multiple_rows(self):
        """Planning inspection for multiple rows should generate waypoints."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575)),
            PanelRow(start=(48.137, 11.576), end=(48.138, 11.576))
        ]
        config = InspectionConfig(trigger_distance=10.0)
        
        waypoints = planner.plan_inspection(rows, config, add_rtl=False)
        
        # Should have waypoints for both rows
        assert len(waypoints) > 0
        
        # Count gimbal control commands (one per row)
        gimbal_count = sum(1 for wp in waypoints if wp.cmd == 205)
        assert gimbal_count == 2  # One per row
    
    def test_plan_inspection_with_rtl(self):
        """Planning with RTL should add return-to-launch waypoint."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575))
        ]
        config = InspectionConfig()
        
        waypoints = planner.plan_inspection(rows, config, add_rtl=True)
        
        # Last waypoint should be RTL
        assert waypoints[-1].cmd == 20  # MAV_CMD_NAV_RETURN_TO_LAUNCH
    
    def test_interpolate_row(self):
        """Row interpolation should generate correct waypoints."""
        planner = SolarParkInspectionPlanner()
        row = PanelRow(
            start=(48.137, 11.575),
            end=(48.138, 11.575)
        )
        config = InspectionConfig(trigger_distance=50.0)
        
        waypoints = planner._interpolate_row(row, config)
        
        # Should have at least 2 waypoints (start and end)
        assert len(waypoints) >= 2
        
        # First waypoint should be at start
        assert waypoints[0] == row.start
        
        # Last waypoint should be at end
        assert waypoints[-1] == row.end
    
    def test_haversine_distance(self):
        """Haversine distance calculation should be accurate."""
        planner = SolarParkInspectionPlanner()
        
        # Test known distance (approximately 1 degree latitude ≈ 111 km)
        lat1, lon1 = 48.0, 11.0
        lat2, lon2 = 49.0, 11.0
        
        distance = planner._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 111 km (111000 meters)
        assert 110000 < distance < 112000
    
    def test_haversine_distance_same_point(self):
        """Distance between same point should be zero."""
        planner = SolarParkInspectionPlanner()
        
        distance = planner._haversine_distance(48.137, 11.575, 48.137, 11.575)
        
        assert distance == 0.0
    
    def test_calculate_coverage_area(self):
        """Coverage area calculation should be reasonable."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575))
        ]
        config = InspectionConfig(
            altitude=15.0,
            camera_fov_horizontal=60.0
        )
        
        area = planner.calculate_coverage_area(rows, config)
        
        # Area should be positive
        assert area > 0
        
        # For a single row ~111m long with 15m altitude and 60° FOV,
        # coverage width ≈ 2 * 15 * tan(30°) ≈ 17.3m
        # Total area ≈ 111 * 17.3 ≈ 1920 m²
        assert 1000 < area < 3000
    
    def test_estimate_mission_time(self):
        """Mission time estimation should be reasonable."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575)),
            PanelRow(start=(48.137, 11.576), end=(48.138, 11.576))
        ]
        config = InspectionConfig(speed=3.0)
        
        mission_time = planner.estimate_mission_time(rows, config)
        
        # Mission time should be positive
        assert mission_time > 0
        
        # For two rows ~111m each at 3 m/s: ~74 seconds + 10s transition
        assert 70 < mission_time < 100
    
    def test_gimbal_angles_in_waypoints(self):
        """Gimbal angles should be correctly set in waypoints."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575))
        ]
        config = InspectionConfig(
            gimbal_pitch=-45.0,
            gimbal_roll=5.0,
            gimbal_yaw=10.0
        )
        
        waypoints = planner.plan_inspection(rows, config, add_rtl=False)
        
        # Find gimbal control waypoint
        gimbal_wp = next(wp for wp in waypoints if wp.cmd == 205)
        
        assert gimbal_wp.param1 == -45.0  # Pitch
        assert gimbal_wp.param2 == 5.0    # Roll
        assert gimbal_wp.param3 == 10.0   # Yaw
        assert gimbal_wp.param7 == 2.0    # MAV_MOUNT_MODE_MAVLINK_TARGETING
    
    def test_camera_trigger_spacing(self):
        """Camera triggers should be spaced according to config."""
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575))
        ]
        config = InspectionConfig(trigger_distance=20.0)
        
        waypoints = planner.plan_inspection(rows, config, add_rtl=False)
        
        # Count camera trigger commands
        camera_triggers = [wp for wp in waypoints if wp.cmd == 203]
        
        # Should have multiple triggers along the row
        assert len(camera_triggers) > 1
        
        # Row is ~111m, with 20m spacing should have ~6 triggers
        assert 4 <= len(camera_triggers) <= 8


class TestIntegration:
    """Integration tests for complete inspection workflow."""
    
    def test_complete_inspection_workflow(self):
        """Complete workflow from planning to waypoint generation."""
        # Initialize planner
        planner = SolarParkInspectionPlanner()
        planner.set_home_position(48.137, 11.575)
        
        # Define solar panel rows
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575), width=2.0),
            PanelRow(start=(48.137, 11.576), end=(48.138, 11.576), width=2.0),
            PanelRow(start=(48.137, 11.577), end=(48.138, 11.577), width=2.0)
        ]
        
        # Configure inspection
        config = InspectionConfig(
            altitude=15.0,
            gimbal_pitch=-90.0,
            overlap=0.3,
            speed=3.0,
            trigger_distance=10.0
        )
        
        # Generate waypoints
        waypoints = planner.plan_inspection(rows, config, add_rtl=True)
        
        # Validate results
        assert len(waypoints) > 0
        
        # Check waypoint types
        nav_waypoints = [wp for wp in waypoints if wp.cmd == 16]
        gimbal_waypoints = [wp for wp in waypoints if wp.cmd == 205]
        camera_waypoints = [wp for wp in waypoints if wp.cmd == 203]
        rtl_waypoints = [wp for wp in waypoints if wp.cmd == 20]
        
        assert len(nav_waypoints) > 0
        assert len(gimbal_waypoints) == 3  # One per row
        assert len(camera_waypoints) > 0
        assert len(rtl_waypoints) == 1
        
        # Calculate mission metrics
        coverage_area = planner.calculate_coverage_area(rows, config)
        mission_time = planner.estimate_mission_time(rows, config)
        
        assert coverage_area > 0
        assert mission_time > 0
        
        print(f"Mission Summary:")
        print(f"  Total waypoints: {len(waypoints)}")
        print(f"  Coverage area: {coverage_area:.1f} m²")
        print(f"  Estimated time: {mission_time:.1f} seconds")
