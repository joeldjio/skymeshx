"""
Seeding Mission Planner for Agricultural UAV Operations.

Generates waypoint patterns with precise seed drop points using servo commands.
Integrates with FieldCoveragePlanner for efficient field coverage patterns.

Usage:
    from droneresearch.control.seeding_planner import SeedingMissionPlanner
    from droneresearch.control.field_coverage import FieldBoundary
    
    planner = SeedingMissionPlanner()
    planner.set_home_position(48.137, 11.575)
    
    boundary = FieldBoundary(corners=[
        (48.137, 11.575),
        (48.138, 11.575),
        (48.138, 11.576),
        (48.137, 11.576)
    ])
    
    waypoints = planner.plan_seeding_mission(
        boundary=boundary,
        seed_spacing=2.0,      # 2m between seeds
        row_spacing=5.0,       # 5m between rows
        altitude=10.0,         # 10m flight altitude
        servo_channel=9,       # Servo channel for seed dispenser
        servo_open_pwm=1900,   # PWM value to open dispenser
        servo_close_pwm=1100,  # PWM value to close dispenser
        drop_duration=0.5      # Seconds to keep dispenser open
    )
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from droneresearch.control.field_coverage import (
    FieldBoundary,
    FieldCoveragePlanner,
    CoverageConfig,
    CoveragePattern
)
from droneresearch.control.mission import Waypoint


# MAVLink command constants
MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_DO_SET_SERVO = 183
MAV_CMD_NAV_DELAY = 93


@dataclass
class SeedingConfig:
    """Configuration for seeding mission planning."""
    seed_spacing: float = 2.0       # meters between seeds in a row
    row_spacing: float = 5.0        # meters between rows
    altitude: float = 10.0          # meters AGL
    speed: float = 3.0              # m/s (slower for accurate drops)
    servo_channel: int = 9          # Servo channel (1-16)
    servo_open_pwm: int = 1900      # PWM value to open dispenser
    servo_close_pwm: int = 1100     # PWM value to close dispenser
    drop_duration: float = 0.5      # seconds to keep dispenser open
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.seed_spacing <= 0:
            raise ValueError("Seed spacing must be positive")
        if self.row_spacing <= 0:
            raise ValueError("Row spacing must be positive")
        if self.altitude <= 0:
            raise ValueError("Altitude must be positive")
        if self.speed <= 0:
            raise ValueError("Speed must be positive")
        if not 1 <= self.servo_channel <= 16:
            raise ValueError("Servo channel must be between 1 and 16")
        if not 900 <= self.servo_open_pwm <= 2100:
            raise ValueError("Servo open PWM must be between 900 and 2100")
        if not 900 <= self.servo_close_pwm <= 2100:
            raise ValueError("Servo close PWM must be between 900 and 2100")
        if self.drop_duration <= 0:
            raise ValueError("Drop duration must be positive")


class SeedingMissionPlanner:
    """
    Generate seeding missions with precise drop points.
    
    Uses FieldCoveragePlanner to generate efficient coverage patterns,
    then inserts servo commands at calculated seed drop intervals.
    """
    
    def __init__(self):
        """Initialize seeding mission planner."""
        self._coverage_planner = FieldCoveragePlanner()
        self._home_position: Optional[Tuple[float, float]] = None
    
    def set_home_position(self, lat: float, lon: float) -> None:
        """
        Set home position for coordinate conversions.
        
        Args:
            lat: Home latitude (degrees)
            lon: Home longitude (degrees)
        """
        self._home_position = (lat, lon)
        self._coverage_planner.set_home_position(lat, lon)
    
    def plan_seeding_mission(
        self,
        boundary: FieldBoundary,
        seed_spacing: float = 2.0,
        row_spacing: float = 5.0,
        altitude: float = 10.0,
        speed: float = 3.0,
        servo_channel: int = 9,
        servo_open_pwm: int = 1900,
        servo_close_pwm: int = 1100,
        drop_duration: float = 0.5,
        add_rtl: bool = True
    ) -> List[Waypoint]:
        """
        Generate waypoints for seeding mission with servo commands.
        
        Args:
            boundary: Field boundary definition
            seed_spacing: Distance between seeds in row (meters)
            row_spacing: Distance between rows (meters)
            altitude: Flight altitude (meters AGL)
            speed: Flight speed (m/s)
            servo_channel: Servo channel for seed dispenser (1-16)
            servo_open_pwm: PWM value to open dispenser (900-2100)
            servo_close_pwm: PWM value to close dispenser (900-2100)
            drop_duration: Seconds to keep dispenser open
            add_rtl: If True, adds RTL as final waypoint
            
        Returns:
            List of Waypoint objects including navigation and servo commands
            
        Raises:
            ValueError: If home position not set or invalid configuration
        """
        if self._home_position is None:
            raise ValueError("Home position must be set before planning mission")
        
        # Create seeding configuration
        config = SeedingConfig(
            seed_spacing=seed_spacing,
            row_spacing=row_spacing,
            altitude=altitude,
            speed=speed,
            servo_channel=servo_channel,
            servo_open_pwm=servo_open_pwm,
            servo_close_pwm=servo_close_pwm,
            drop_duration=drop_duration
        )
        
        # Generate base coverage pattern
        coverage_config = CoverageConfig(
            pattern=CoveragePattern.PARALLEL_LINES,
            altitude=altitude,
            line_spacing=row_spacing,
            speed=speed,
            heading=0.0  # North-South lines
        )
        
        base_waypoints = self._coverage_planner.generate_coverage_waypoints(
            boundary=boundary,
            config=coverage_config,
            add_rtl=False  # We'll add RTL manually if needed
        )
        
        # Convert to Waypoint objects and insert seed drop commands
        mission_waypoints = self._insert_seed_drops(
            base_waypoints,
            config
        )
        
        # Add RTL waypoint at the end
        if add_rtl and self._home_position:
            home_lat, home_lon = self._home_position
            mission_waypoints.append(Waypoint(
                lat=home_lat,
                lon=home_lon,
                alt=altitude,
                speed=speed,
                cmd=MAV_CMD_NAV_WAYPOINT
            ))
        
        return mission_waypoints
    
    def _insert_seed_drops(
        self,
        base_waypoints: List[Tuple[float, float, float]],
        config: SeedingConfig
    ) -> List[Waypoint]:
        """
        Insert seed drop commands between navigation waypoints.
        
        Args:
            base_waypoints: List of (lat, lon, alt) tuples from coverage planner
            config: Seeding configuration
            
        Returns:
            List of Waypoint objects with seed drop commands inserted
        """
        mission_waypoints = []
        
        for i, (lat, lon, alt) in enumerate(base_waypoints):
            # Add navigation waypoint
            mission_waypoints.append(Waypoint(
                lat=lat,
                lon=lon,
                alt=alt,
                speed=config.speed,
                cmd=MAV_CMD_NAV_WAYPOINT
            ))
            
            # Calculate if we should drop a seed at this waypoint
            # Drop seeds along the rows (not at turn points)
            if i > 0 and self._should_drop_seed(i, base_waypoints, config):
                # Add servo open command
                mission_waypoints.append(Waypoint(
                    lat=lat,
                    lon=lon,
                    alt=alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    # Use hold field for servo channel (param1)
                    # Use radius field for PWM value (param2)
                    hold=float(config.servo_channel),
                    radius=float(config.servo_open_pwm)
                ))
                
                # Add delay command to keep dispenser open
                mission_waypoints.append(Waypoint(
                    lat=lat,
                    lon=lon,
                    alt=alt,
                    cmd=MAV_CMD_NAV_DELAY,
                    hold=config.drop_duration
                ))
                
                # Add servo close command
                mission_waypoints.append(Waypoint(
                    lat=lat,
                    lon=lon,
                    alt=alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    hold=float(config.servo_channel),
                    radius=float(config.servo_close_pwm)
                ))
        
        return mission_waypoints
    
    def _should_drop_seed(
        self,
        index: int,
        waypoints: List[Tuple[float, float, float]],
        config: SeedingConfig
    ) -> bool:
        """
        Determine if a seed should be dropped at this waypoint.
        
        Args:
            index: Current waypoint index
            waypoints: List of all waypoints
            config: Seeding configuration
            
        Returns:
            True if seed should be dropped at this waypoint
        """
        if index == 0:
            return False
        
        # Calculate distance from previous waypoint
        prev_lat, prev_lon, _ = waypoints[index - 1]
        curr_lat, curr_lon, _ = waypoints[index]
        
        distance = self._calculate_distance(
            (prev_lat, prev_lon),
            (curr_lat, curr_lon)
        )
        
        # Drop seed if we've traveled at least seed_spacing meters
        # This is a simplified approach - in practice, you'd track
        # cumulative distance along the row
        return distance >= config.seed_spacing
    
    def _calculate_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        
        Args:
            pos1: (lat, lon) tuple
            pos2: (lat, lon) tuple
            
        Returns:
            Distance in meters
        """
        lat1, lon1 = pos1
        lat2, lon2 = pos2
        
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = (math.sin(dphi/2)**2 + 
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def estimate_mission_stats(
        self,
        boundary: FieldBoundary,
        config: SeedingConfig
    ) -> dict:
        """
        Estimate mission statistics without generating full waypoint list.
        
        Args:
            boundary: Field boundary definition
            config: Seeding configuration
            
        Returns:
            Dictionary with estimated stats:
                - total_distance: Total flight distance (meters)
                - estimated_time: Estimated mission time (seconds)
                - seed_count: Estimated number of seeds to be dropped
                - row_count: Number of rows to be flown
        """
        # Calculate field area (simplified bounding box)
        lats = [lat for lat, lon in boundary.corners]
        lons = [lon for lat, lon in boundary.corners]
        
        # Convert to local meters for area calculation
        lat_range = (max(lats) - min(lats)) * 111320  # degrees to meters
        lon_range = (max(lons) - min(lons)) * 111320 * math.cos(math.radians(sum(lats)/len(lats)))
        
        field_area = lat_range * lon_range
        row_count = int(lon_range / config.row_spacing) + 1
        total_distance = row_count * lat_range
        
        # Estimate seed count
        seeds_per_row = int(lat_range / config.seed_spacing)
        seed_count = seeds_per_row * row_count
        
        # Estimate time (flight time + drop time)
        flight_time = total_distance / config.speed
        drop_time = seed_count * config.drop_duration
        estimated_time = flight_time + drop_time
        
        return {
            "total_distance": total_distance,
            "estimated_time": estimated_time,
            "seed_count": seed_count,
            "row_count": row_count,
            "field_area": field_area
        }


__all__ = ["SeedingMissionPlanner", "SeedingConfig"]

# Made with Bob
