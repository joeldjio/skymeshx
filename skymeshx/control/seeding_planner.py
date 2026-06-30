"""
Seeding Mission Planner for Agricultural UAV Operations.

Generates waypoint patterns with precise seed drop points using servo commands.
Integrates with FieldCoveragePlanner for efficient field coverage patterns.

Usage:
    from skymeshx.control.seeding_planner import SeedingMissionPlanner
    from skymeshx.control.field_coverage import FieldBoundary
    
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

from skymeshx.control.field_coverage import (
    FieldBoundary,
    FieldCoveragePlanner,
    CoverageConfig,
    CoveragePattern
)
from skymeshx.control.mission import Waypoint


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


@dataclass
class DispenserCalibration:
    """Dispenser calibration and capacity data used for preview validation."""
    seed_capacity: int = 500
    seed_weight_g: float = 0.05
    tank_capacity_kg: float = 1.0
    seeds_per_drop: int = 1
    max_drop_rate: float = 2.0

    def __post_init__(self):
        if self.seed_capacity <= 0:
            raise ValueError("Seed capacity must be positive")
        if self.seed_weight_g <= 0:
            raise ValueError("Seed weight must be positive")
        if self.tank_capacity_kg <= 0:
            raise ValueError("Tank capacity must be positive")
        if self.seeds_per_drop <= 0:
            raise ValueError("Seeds per drop must be positive")
        if self.max_drop_rate <= 0:
            raise ValueError("Max drop rate must be positive")


@dataclass
class SeedingDropPoint:
    """Seed drop point metadata for mission preview."""
    lat: float
    lon: float
    alt: float
    seed_count: int
    expected_drop_id: str


@dataclass
class SeedingMissionPreview:
    """Complete seeding preview data for UI and validation."""
    waypoints: List[Waypoint]
    waypoint_list: List[dict]
    flight_path: List[dict]
    flight_rows: List[dict]
    drop_points: List[SeedingDropPoint]
    exclusion_zones: List[dict]
    estimated_seed_usage: int
    estimated_seed_weight_kg: float
    estimated_duration: float
    estimated_battery_usage: float
    estimated_distance: float
    field_area: float
    estimated_waypoint_count: int
    warnings: List[str]

    def to_dict(self) -> dict:
        return {
            "waypoints": self.waypoint_list,
            "flightPath": self.flight_path,
            "flightRows": self.flight_rows,
            "dropPoints": [
                {
                    "lat": point.lat,
                    "lon": point.lon,
                    "alt": point.alt,
                    "seedCount": point.seed_count,
                    "expectedDropId": point.expected_drop_id,
                }
                for point in self.drop_points
            ],
            "exclusionZones": list(self.exclusion_zones),
            "estimatedSeedUsage": self.estimated_seed_usage,
            "estimatedSeedWeightKg": self.estimated_seed_weight_kg,
            "estimatedDuration": self.estimated_duration,
            "estimatedBatteryUsage": self.estimated_battery_usage,
            "estimatedDistance": self.estimated_distance,
            "fieldArea": self.field_area,
            "estimatedWaypointCount": self.estimated_waypoint_count,
            "warnings": list(self.warnings),
        }


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
        
        # Estimate total waypoints before generation
        total_distance = self._estimate_total_distance(base_waypoints)
        estimated_seeds = int(total_distance / seed_spacing)
        estimated_waypoints = len(base_waypoints) + (estimated_seeds * 4)  # NAV + open + delay + close
        
        # Do not reject large fields here. Some autopilots have practical
        # upload limits, but field definition and preview generation must not
        # be blocked by a fixed vehicle-specific waypoint threshold.
        
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

    def generate_seeding_mission_with_preview(
        self,
        boundary: FieldBoundary,
        config: SeedingConfig,
        calibration: Optional[DispenserCalibration] = None,
        exclusion_zones: Optional[List[dict]] = None,
        add_rtl: bool = True,
    ) -> SeedingMissionPreview:
        """
        Generate seeding waypoints plus UI-ready preview metadata.

        The preview is hardware-free and does not upload or execute a mission.
        """
        calibration = calibration or DispenserCalibration()
        exclusion_zones = list(exclusion_zones or [])
        # Validate first so a bad config raises a structured error before
        # plan_seeding_mission is called (which would raise an unguarded exception
        # if home position is unset or boundary is invalid).
        validation = self.validate_seeding_mission(
            boundary,
            config,
            calibration=calibration,
            exclusion_zones=exclusion_zones,
        )
        waypoints = self.plan_seeding_mission(
            boundary=boundary,
            seed_spacing=config.seed_spacing,
            row_spacing=config.row_spacing,
            altitude=config.altitude,
            speed=config.speed,
            servo_channel=config.servo_channel,
            servo_open_pwm=config.servo_open_pwm,
            servo_close_pwm=config.servo_close_pwm,
            drop_duration=config.drop_duration,
            add_rtl=add_rtl,
        )
        stats = self.estimate_mission_stats(boundary, config)
        drop_points = self._build_drop_points(waypoints, calibration)

        return SeedingMissionPreview(
            waypoints=waypoints,
            waypoint_list=[
                {"lat": wp.lat, "lon": wp.lon, "alt": wp.alt, "cmd": wp.cmd}
                for wp in waypoints
            ],
            flight_path=[
                {"lat": wp.lat, "lon": wp.lon, "alt": wp.alt}
                for wp in waypoints
                if wp.cmd == MAV_CMD_NAV_WAYPOINT
            ],
            flight_rows=self._build_flight_rows(boundary, config),
            drop_points=drop_points,
            exclusion_zones=exclusion_zones,
            estimated_seed_usage=sum(point.seed_count for point in drop_points),
            estimated_seed_weight_kg=self._estimate_seed_weight_kg(drop_points, calibration),
            estimated_duration=stats["estimated_time"],
            estimated_battery_usage=self._estimate_battery_usage(
                stats["estimated_time"], stats["total_distance"]
            ),
            estimated_distance=stats["total_distance"],
            field_area=stats["field_area"],
            estimated_waypoint_count=validation["estimatedWaypointCount"],
            warnings=validation["warnings"],
        )

    def validate_seeding_mission(
        self,
        boundary: FieldBoundary,
        config: SeedingConfig,
        calibration: Optional[DispenserCalibration] = None,
        exclusion_zones: Optional[List[dict]] = None,
        battery_available_percent: float = 100.0,
    ) -> dict:
        """Validate seeding mission parameters and return actionable warnings."""
        calibration = calibration or DispenserCalibration()
        exclusion_zones = list(exclusion_zones or [])
        warnings: List[str] = []
        errors: List[str] = []

        if self._home_position is None:
            errors.append("Home position must be set before planning mission")
            return {"valid": False, "warnings": warnings, "errors": errors}

        stats = self.estimate_mission_stats(boundary, config)
        estimated_waypoints = self._estimate_waypoint_count(stats["total_distance"], config)
        estimated_seed_usage = stats["seed_count"] * calibration.seeds_per_drop
        estimated_seed_weight_kg = (
            estimated_seed_usage * calibration.seed_weight_g / 1000.0
        )
        drop_rate = config.speed / config.seed_spacing
        battery_required = self._estimate_battery_usage(
            stats["estimated_time"], stats["total_distance"]
        )

        if estimated_waypoints > 700:
            warnings.append(
                f"Mission would generate about {estimated_waypoints} waypoints "
                "(above the common 700-waypoint vehicle limit). Upload may need "
                "mission splitting, but preview remains valid."
            )

        if estimated_seed_usage > calibration.seed_capacity:
            warnings.append("Estimated seed usage exceeds dispenser seed capacity")
        elif estimated_seed_usage > calibration.seed_capacity * 0.8:
            warnings.append("Estimated seed usage is near dispenser seed capacity")

        if estimated_seed_weight_kg > calibration.tank_capacity_kg:
            warnings.append("Estimated seed weight exceeds tank capacity")

        if drop_rate > calibration.max_drop_rate:
            warnings.append("Flight speed is too high for calibrated dispenser drop rate")

        if config.drop_duration > config.seed_spacing / config.speed:
            warnings.append("Drop duration may overlap before the next seed point")

        if exclusion_zones:
            warnings.append("Exclusion zones are included in preview but not carved from path")

        if battery_required > battery_available_percent:
            warnings.append("Estimated battery requirement exceeds available battery")
        elif battery_required > 80.0:
            warnings.append("Mission may require high battery usage - consider splitting field")

        return {
            "valid": not errors,
            "warnings": warnings,
            "errors": errors,
            "estimatedSeedUsage": estimated_seed_usage,
            "estimatedSeedWeightKg": estimated_seed_weight_kg,
            "estimatedBatteryUsage": battery_required,
            "estimatedWaypointCount": estimated_waypoints,
            "dropRate": drop_rate,
            "fieldArea": stats["field_area"],
        }
    
    def _insert_seed_drops(
        self,
        base_waypoints: List[Tuple[float, float, float]],
        config: SeedingConfig
    ) -> List[Waypoint]:
        """
        Insert seed drop commands between navigation waypoints.
        
        Interpolates additional waypoints between coverage waypoints based on seed_spacing,
        ensuring seeds are dropped at regular intervals along each row.
        
        Args:
            base_waypoints: List of (lat, lon, alt) tuples from coverage planner
            config: Seeding configuration
            
        Returns:
            List of Waypoint objects with seed drop commands inserted
        """
        mission_waypoints = []
        
        # Process each pair of consecutive base waypoints
        for i in range(len(base_waypoints) - 1):
            curr_lat, curr_lon, curr_alt = base_waypoints[i]
            next_lat, next_lon, next_alt = base_waypoints[i + 1]
            
            # Calculate distance between waypoints
            distance = self._calculate_distance(
                (curr_lat, curr_lon),
                (next_lat, next_lon)
            )
            
            # Skip if waypoints are too close (< 1m)
            if distance < 1.0:
                continue
            
            # Calculate number of seed drops needed
            num_seeds = int(distance / config.seed_spacing)
            
            # If no seeds fit, add a single waypoint at midpoint
            if num_seeds == 0:
                mid_lat = (curr_lat + next_lat) / 2
                mid_lon = (curr_lon + next_lon) / 2
                mid_alt = (curr_alt + next_alt) / 2
                
                mission_waypoints.append(Waypoint(
                    lat=mid_lat,
                    lon=mid_lon,
                    alt=mid_alt,
                    speed=config.speed,
                    hold=config.drop_duration,
                    cmd=MAV_CMD_NAV_WAYPOINT
                ))
                
                # Add servo commands
                mission_waypoints.append(Waypoint(
                    lat=mid_lat, lon=mid_lon, alt=mid_alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    hold=float(config.servo_channel),
                    radius=float(config.servo_open_pwm)
                ))
                mission_waypoints.append(Waypoint(
                    lat=mid_lat,
                    lon=mid_lon,
                    alt=mid_alt,
                    cmd=MAV_CMD_NAV_DELAY,
                    hold=config.drop_duration
                ))
                mission_waypoints.append(Waypoint(
                    lat=mid_lat, lon=mid_lon, alt=mid_alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    hold=float(config.servo_channel),
                    radius=float(config.servo_close_pwm)
                ))
                continue
            
            # Interpolate seed drop waypoints
            for j in range(1, num_seeds + 1):
                # Calculate interpolation factor
                t = (j * config.seed_spacing) / distance
                
                # Interpolate position
                seed_lat = curr_lat + t * (next_lat - curr_lat)
                seed_lon = curr_lon + t * (next_lon - curr_lon)
                seed_alt = curr_alt + t * (next_alt - curr_alt)
                
                # Add navigation waypoint with hold time
                mission_waypoints.append(Waypoint(
                    lat=seed_lat,
                    lon=seed_lon,
                    alt=seed_alt,
                    speed=config.speed,
                    hold=config.drop_duration,
                    cmd=MAV_CMD_NAV_WAYPOINT
                ))
                
                # Add servo open command
                mission_waypoints.append(Waypoint(
                    lat=seed_lat,
                    lon=seed_lon,
                    alt=seed_alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    hold=float(config.servo_channel),
                    radius=float(config.servo_open_pwm)
                ))
                
                # Hold dispenser open for calibrated drop duration
                mission_waypoints.append(Waypoint(
                    lat=seed_lat,
                    lon=seed_lon,
                    alt=seed_alt,
                    cmd=MAV_CMD_NAV_DELAY,
                    hold=config.drop_duration
                ))
                
                # Add servo close command
                mission_waypoints.append(Waypoint(
                    lat=seed_lat,
                    lon=seed_lon,
                    alt=seed_alt,
                    cmd=MAV_CMD_DO_SET_SERVO,
                    hold=float(config.servo_channel),
                    radius=float(config.servo_close_pwm)
                ))
        
        return mission_waypoints

    def _build_drop_points(
        self,
        waypoints: List[Waypoint],
        calibration: DispenserCalibration,
    ) -> List[SeedingDropPoint]:
        points: List[SeedingDropPoint] = []
        for index, waypoint in enumerate(waypoints, start=1):
            if waypoint.cmd == MAV_CMD_NAV_WAYPOINT and waypoint.hold > 0:
                points.append(
                    SeedingDropPoint(
                        lat=waypoint.lat,
                        lon=waypoint.lon,
                        alt=waypoint.alt,
                        seed_count=calibration.seeds_per_drop,
                        expected_drop_id=f"seed-{index:04d}",
                    )
                )
        return points

    def _build_flight_rows(
        self,
        boundary: FieldBoundary,
        config: SeedingConfig,
    ) -> List[dict]:
        coverage_config = CoverageConfig(
            pattern=CoveragePattern.PARALLEL_LINES,
            altitude=config.altitude,
            line_spacing=config.row_spacing,
            speed=config.speed,
            heading=0.0,
        )
        base_waypoints = self._coverage_planner.generate_coverage_waypoints(
            boundary=boundary,
            config=coverage_config,
            add_rtl=False,
        )
        rows = []
        for idx in range(len(base_waypoints) - 1):
            start_lat, start_lon, start_alt = base_waypoints[idx]
            end_lat, end_lon, end_alt = base_waypoints[idx + 1]
            if self._calculate_distance((start_lat, start_lon), (end_lat, end_lon)) < 1.0:
                continue
            rows.append({
                "index": len(rows) + 1,
                "start": {"lat": start_lat, "lon": start_lon, "alt": start_alt},
                "end": {"lat": end_lat, "lon": end_lon, "alt": end_alt},
            })
        return rows

    def _estimate_waypoint_count(self, total_distance: float, config: SeedingConfig) -> int:
        estimated_seeds = int(total_distance / config.seed_spacing)
        return estimated_seeds * 4

    def _estimate_seed_weight_kg(
        self,
        drop_points: List[SeedingDropPoint],
        calibration: DispenserCalibration,
    ) -> float:
        seed_count = sum(point.seed_count for point in drop_points)
        return seed_count * calibration.seed_weight_g / 1000.0

    def _estimate_battery_usage(self, mission_time: float, distance: float) -> float:
        time_component = mission_time / 60.0 * 1.8
        distance_component = distance / 1000.0 * 4.0
        return min(100.0, max(0.0, time_component + distance_component))
    
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
    
    def _estimate_total_distance(
        self,
        waypoints: List[Tuple[float, float, float]]
    ) -> float:
        """
        Estimate total distance covered by waypoint path.
        
        Args:
            waypoints: List of (lat, lon, alt) tuples
            
        Returns:
            Total distance in meters
        """
        total = 0.0
        for i in range(len(waypoints) - 1):
            lat1, lon1, _ = waypoints[i]
            lat2, lon2, _ = waypoints[i + 1]
            total += self._calculate_distance((lat1, lon1), (lat2, lon2))
        return total
    
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


__all__ = [
    "SeedingMissionPlanner",
    "SeedingConfig",
    "DispenserCalibration",
    "SeedingDropPoint",
    "SeedingMissionPreview",
]
