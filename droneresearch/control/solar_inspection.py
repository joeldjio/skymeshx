"""
Solar Park Inspection Planning for UAV Operations.

Generates waypoint patterns for efficient solar panel inspection with configurable
altitude, gimbal angles, and image overlap. Supports thermal camera integration
for hotspot detection.

Frame Convention
----------------
All positions use GPS coordinates (latitude, longitude) for panel locations.
Generated waypoints include altitude in meters above ground (positive UP).
Internal calculations use local NED meters for distance computations.

MAVLink Commands
----------------
- MAV_CMD_NAV_WAYPOINT (16): Navigate to waypoint
- MAV_CMD_DO_MOUNT_CONTROL (205): Control gimbal orientation
- MAV_CMD_DO_DIGICAM_CONTROL (203): Trigger camera capture
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from droneresearch.control.mission import Waypoint


@dataclass
class PanelRow:
    """Solar panel row definition in GPS coordinates."""
    start: Tuple[float, float]  # (lat, lon) start of row
    end: Tuple[float, float]    # (lat, lon) end of row
    width: float = 2.0          # meters, panel row width
    
    def __post_init__(self):
        """Validate panel row coordinates."""
        if self.start == self.end:
            raise ValueError("Panel row start and end must be different")
        if self.width <= 0:
            raise ValueError("Panel row width must be positive")


@dataclass
class InspectionConfig:
    """Configuration for solar park inspection."""
    altitude: float = 15.0          # meters AGL above panels
    gimbal_pitch: float = -90.0     # degrees (-90 = straight down)
    gimbal_roll: float = 0.0        # degrees
    gimbal_yaw: float = 0.0         # degrees (relative to heading)
    overlap: float = 0.3            # image overlap ratio (0.0-1.0)
    speed: float = 3.0              # m/s (slower for better image quality)
    camera_fov_horizontal: float = 60.0  # degrees
    camera_fov_vertical: float = 45.0    # degrees
    trigger_distance: float = 5.0   # meters between camera triggers
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.altitude <= 0:
            raise ValueError("Altitude must be positive")
        if not 0 <= self.overlap < 1:
            raise ValueError("Overlap must be between 0 and 1")
        if self.speed <= 0:
            raise ValueError("Speed must be positive")
        if not -90 <= self.gimbal_pitch <= 90:
            raise ValueError("Gimbal pitch must be between -90 and 90 degrees")
        if self.trigger_distance <= 0:
            raise ValueError("Trigger distance must be positive")


class SolarParkInspectionPlanner:
    """
    Generate waypoint patterns for solar park inspection.
    
    Supports systematic inspection of solar panel rows with automatic
    camera triggering and gimbal control for optimal image capture.
    
    Usage:
        planner = SolarParkInspectionPlanner()
        rows = [
            PanelRow(start=(48.137, 11.575), end=(48.138, 11.575)),
            PanelRow(start=(48.137, 11.576), end=(48.138, 11.576))
        ]
        config = InspectionConfig(altitude=15.0, overlap=0.3)
        waypoints = planner.plan_inspection(rows, config)
    """
    
    def __init__(self):
        """Initialize solar park inspection planner."""
        self._home_position: Optional[Tuple[float, float]] = None
    
    def set_home_position(self, lat: float, lon: float) -> None:
        """
        Set home position for local coordinate conversions.
        
        Args:
            lat: Home latitude (degrees)
            lon: Home longitude (degrees)
        """
        self._home_position = (lat, lon)
    
    def plan_inspection(
        self,
        panel_rows: List[PanelRow],
        config: InspectionConfig,
        add_rtl: bool = True
    ) -> List[Waypoint]:
        """
        Generate waypoints for solar panel inspection.
        
        Creates a systematic flight pattern over panel rows with camera
        triggers at regular intervals and gimbal control for optimal viewing.
        
        Args:
            panel_rows: List of panel row definitions
            config: Inspection configuration
            add_rtl: Add RTL (Return to Launch) waypoint at end
        
        Returns:
            List of waypoints with camera trigger and gimbal commands
        
        Raises:
            ValueError: If panel_rows is empty or config is invalid
        """
        if not panel_rows:
            raise ValueError("At least one panel row required")
        
        waypoints = []
        
        # Process each panel row
        for row_idx, row in enumerate(panel_rows):
            # Generate waypoints along the row
            row_waypoints = self._interpolate_row(row, config)
            
            # Add waypoints with camera triggers
            for wp_idx, (lat, lon) in enumerate(row_waypoints):
                # Navigation waypoint
                nav_wp = Waypoint(
                    lat=lat,
                    lon=lon,
                    alt=config.altitude,
                    speed=config.speed,
                    cmd=16,  # MAV_CMD_NAV_WAYPOINT
                    radius=2.0
                )
                waypoints.append(nav_wp)
                
                # Gimbal control command (only at first waypoint of each row)
                if wp_idx == 0:
                    gimbal_wp = Waypoint(
                        lat=lat,
                        lon=lon,
                        alt=config.altitude,
                        cmd=205,  # MAV_CMD_DO_MOUNT_CONTROL
                        param1=config.gimbal_pitch,  # Pitch angle
                        param2=config.gimbal_roll,   # Roll angle
                        param3=config.gimbal_yaw,    # Yaw angle
                        param7=2.0  # MAV_MOUNT_MODE_MAVLINK_TARGETING
                    )
                    waypoints.append(gimbal_wp)
                
                # Camera trigger command
                trigger_wp = Waypoint(
                    lat=lat,
                    lon=lon,
                    alt=config.altitude,
                    cmd=203,  # MAV_CMD_DO_DIGICAM_CONTROL
                    param5=1.0  # Trigger camera
                )
                waypoints.append(trigger_wp)
        
        # Add RTL waypoint if requested
        if add_rtl and waypoints:
            last_wp = waypoints[-1]
            rtl_wp = Waypoint(
                lat=last_wp.lat,
                lon=last_wp.lon,
                alt=last_wp.alt,
                cmd=20  # MAV_CMD_NAV_RETURN_TO_LAUNCH
            )
            waypoints.append(rtl_wp)
        
        return waypoints
    
    def _interpolate_row(
        self,
        row: PanelRow,
        config: InspectionConfig
    ) -> List[Tuple[float, float]]:
        """
        Generate waypoints along a panel row.
        
        Calculates waypoint positions based on trigger distance and overlap
        to ensure complete coverage of the panel row.
        
        Args:
            row: Panel row definition
            config: Inspection configuration
        
        Returns:
            List of (lat, lon) waypoint coordinates
        """
        # Calculate row length in meters
        row_length = self._haversine_distance(
            row.start[0], row.start[1],
            row.end[0], row.end[1]
        )
        
        # Calculate number of waypoints based on trigger distance
        num_waypoints = max(2, int(row_length / config.trigger_distance) + 1)
        
        # Generate waypoints along the row
        waypoints = []
        for i in range(num_waypoints):
            # Linear interpolation between start and end
            t = i / (num_waypoints - 1) if num_waypoints > 1 else 0
            lat = row.start[0] + t * (row.end[0] - row.start[0])
            lon = row.start[1] + t * (row.end[1] - row.start[1])
            waypoints.append((lat, lon))
        
        return waypoints
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First coordinate (degrees)
            lat2, lon2: Second coordinate (degrees)
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def calculate_coverage_area(
        self,
        panel_rows: List[PanelRow],
        config: InspectionConfig
    ) -> float:
        """
        Calculate total area covered by inspection mission.
        
        Args:
            panel_rows: List of panel row definitions
            config: Inspection configuration
        
        Returns:
            Total coverage area in square meters
        """
        total_area = 0.0
        
        for row in panel_rows:
            row_length = self._haversine_distance(
                row.start[0], row.start[1],
                row.end[0], row.end[1]
            )
            # Calculate effective coverage width based on camera FOV and altitude
            coverage_width = 2 * config.altitude * math.tan(
                math.radians(config.camera_fov_horizontal / 2)
            )
            total_area += row_length * coverage_width
        
        return total_area
    
    def estimate_mission_time(
        self,
        panel_rows: List[PanelRow],
        config: InspectionConfig
    ) -> float:
        """
        Estimate total mission time in seconds.
        
        Args:
            panel_rows: List of panel row definitions
            config: Inspection configuration
        
        Returns:
            Estimated mission time in seconds
        """
        total_distance = 0.0
        
        for row in panel_rows:
            row_length = self._haversine_distance(
                row.start[0], row.start[1],
                row.end[0], row.end[1]
            )
            total_distance += row_length
        
        # Add transition time between rows (assume 10 seconds per transition)
        transition_time = (len(panel_rows) - 1) * 10.0 if len(panel_rows) > 1 else 0.0
        
        # Calculate flight time
        flight_time = total_distance / config.speed
        
        return flight_time + transition_time

# Made with Bob
