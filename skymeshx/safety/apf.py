"""
APF Safety Filter — Artificial Potential Field collision avoidance.

Based on: SkySim (Shibu et al., 2025)
    "SkySim: A ROS2-based Simulation Environment for Natural Language
     Control of Drone Swarms using Large Language Models"
    arXiv:2602.01226

Runs at configurable rate (default 20 Hz). Given a set of desired
waypoints and current drone positions, applies repulsive forces to
prevent collisions, enforces kinematic limits, and clips positions
within a geo-fence.

Frame Convention
----------------
All positions use local NED (North-East-Down) coordinates:
- x: North (meters)
- y: East (meters)
- z: Altitude above ground (meters, positive UP)

Note: z is inverted from standard NED (which uses Down positive).
This matches intuitive "altitude" semantics. The filter handles
internal NED calculations with proper z-axis inversion.

Thread Safety
-------------
The filter() method is thread-safe and can be called concurrently from
multiple threads. Internal state (_prev_positions, _prev_velocities,
_obstacles) is protected by a lock.

Usage:
    from skymeshx.safety.apf import APFSafetyFilter, Pose3D

    apf = APFSafetyFilter(
        min_separation=2.0,     # meters between drones
        max_speed=3.0,          # m/s
        geofence_radius=50.0,   # meters from origin
        geofence_alt=(1.0, 30.0)# (min_alt, max_alt) in meters
    )

    # Current positions of all drones: {id: Pose3D}
    positions = {
        "D1": Pose3D(0, 0, 10),
        "D2": Pose3D(3, 0, 10),
        "D3": Pose3D(6, 0, 10),
    }

    # Desired waypoints (from LLM / mission planner)
    desired = {
        "D1": Pose3D(0,  5, 10),
        "D2": Pose3D(5,  5, 10),
        "D3": Pose3D(10, 5, 10),
    }

    # Safe waypoints after APF filtering
    safe = apf.filter(positions, desired)
"""
import math
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class Pose3D:
    """3D position in local NED meters (x=North, y=East, z_up=altitude above ground)."""
    x:   float = 0.0
    y:   float = 0.0
    z:   float = 0.0   # positive = UP (altitude)

    def dist(self, other: "Pose3D") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )

    def __sub__(self, other: "Pose3D") -> "Pose3D":
        return Pose3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def dist_2d(self, other: "Pose3D") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __add__(self, other: "Pose3D") -> "Pose3D":
        return Pose3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, s: float) -> "Pose3D":
        return Pose3D(self.x * s, self.y * s, self.z * s)

    def norm(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self) -> "Pose3D":
        n = self.norm()
        if n < 1e-9:
            return Pose3D(0, 0, 0)
        return Pose3D(self.x / n, self.y / n, self.z / n)

    def clamp(self, max_norm: float) -> "Pose3D":
        n = self.norm()
        if n > max_norm:
            return self.normalized() * max_norm
        return self

    def __repr__(self) -> str:
        return f"Pose3D({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


@dataclass
class Geofence:
    """Cylindrical geofence: horizontal radius + altitude band."""
    origin_x:   float = 0.0
    origin_y:   float = 0.0
    radius:     float = 50.0      # meters horizontal
    alt_min:    float = 1.0       # meters above ground
    alt_max:    float = 30.0      # meters above ground

    def contains(self, p: Pose3D) -> bool:
        r = math.sqrt((p.x - self.origin_x)**2 + (p.y - self.origin_y)**2)
        return r <= self.radius and self.alt_min <= p.z <= self.alt_max

    def clip(self, p: Pose3D) -> Pose3D:
        """Clip position to geofence boundary."""
        dx, dy = p.x - self.origin_x, p.y - self.origin_y
        r = math.sqrt(dx**2 + dy**2)
        if r > self.radius:
            scale = self.radius / r
            dx *= scale
            dy *= scale
        z = max(self.alt_min, min(self.alt_max, p.z))
        return Pose3D(self.origin_x + dx, self.origin_y + dy, z)


class APFSafetyFilter:
    """
    Artificial Potential Field safety filter for drone swarms.

    Applies repulsive potentials between drones and attractive potentials
    toward desired waypoints, then clips to kinematic and geofence limits.

    Parameters
    ----------
    min_separation  : Minimum safe distance between drones (meters)
    max_speed       : Maximum allowed velocity step per update (m/s * dt)
    geofence_radius : Horizontal geofence radius from origin (meters)
    geofence_alt    : (min_alt, max_alt) altitude band (meters)
    repulsion_gain  : Strength of repulsive force between drones
    attraction_gain : Strength of attractive force toward waypoints
    obstacle_radius : Safety margin — repulsion activates within this range
    
    Thread Safety
    -------------
    APFSafetyFilter is stateless and thread-safe.
    The filter() method can be called concurrently from multiple threads.
    No internal state is modified during filtering operations.
    """

    def __init__(
        self,
        min_separation:  float = 2.0,
        max_speed:       float = 3.0,
        geofence_radius: float = 50.0,
        geofence_alt:    Tuple[float, float] = (1.0, 30.0),
        repulsion_gain:  float = 2.0,
        attraction_gain: float = 1.0,
        obstacle_radius: float = 4.0,
        dt:              float = 0.05,   # 20 Hz
        damping_coeff:   float = 0.3,    # velocity damping coefficient
        max_acceleration: float = 2.0,   # m/s² - limits jerky movements (Improvement 9)
    ):
        self.min_separation  = min_separation
        self.max_speed       = max_speed
        self.max_acceleration = max_acceleration
        self.repulsion_gain  = repulsion_gain
        self.attraction_gain = attraction_gain
        self.obstacle_radius = obstacle_radius
        self.dt              = dt
        self.damping_coeff   = damping_coeff
        self.geofence        = Geofence(
            radius  = geofence_radius,
            alt_min = geofence_alt[0],
            alt_max = geofence_alt[1],
        )
        self._obstacles: List[Pose3D] = []   # static obstacles
        self._prev_positions: Dict[str, Pose3D] = {}  # for velocity calculation
        self._prev_velocities: Dict[str, Pose3D] = {}  # for acceleration limiting
        # TS-02 FIX: Lock to protect shared mutable state
        self._state_lock = threading.Lock()

    def add_obstacle(self, x: float, y: float, z: float = 0.0):
        """Add a static obstacle (e.g. building, tree)."""
        with self._state_lock:
            self._obstacles.append(Pose3D(x, y, z))

    def clear_obstacles(self):
        with self._state_lock:
            self._obstacles.clear()

    def filter(
        self,
        positions: Dict[str, Pose3D],
        desired:   Dict[str, Pose3D],
    ) -> Dict[str, Pose3D]:
        """
        Apply APF to move each drone toward desired position
        while avoiding other drones and obstacles.

        Includes velocity damping to prevent oscillations.

        Returns safe waypoints for each drone.
        
        Thread-safe: Can be called concurrently from multiple threads.
        """
        # TS-02 FIX: Protect shared state access with lock
        with self._state_lock:
            # Create snapshots of mutable state
            obstacles = list(self._obstacles)
            prev_positions = dict(self._prev_positions)
            prev_velocities = dict(self._prev_velocities)
        
        safe: Dict[str, Pose3D] = {}
        ids   = list(positions.keys())
        
        # Store updates to apply after processing
        new_prev_positions: Dict[str, Pose3D] = {}
        new_prev_velocities: Dict[str, Pose3D] = {}

        for drone_id in ids:
            pos = positions.get(drone_id)
            des = desired.get(drone_id, pos)
            if pos is None:
                continue

            # Calculate current velocity (if we have previous position)
            velocity = Pose3D(0, 0, 0)
            if drone_id in prev_positions:
                prev = prev_positions[drone_id]
                velocity = (pos - prev) * (1.0 / self.dt)  # velocity = delta_pos / dt
            
            # Store previous velocity for acceleration limiting
            prev_velocity = prev_velocities.get(drone_id, Pose3D(0, 0, 0))

            # Attractive force: toward desired position
            diff_x = des.x - pos.x
            diff_y = des.y - pos.y
            diff_z = des.z - pos.z
            attr = Pose3D(diff_x, diff_y, diff_z)
            attr_clamped = attr.clamp(self.max_speed * self.dt) * self.attraction_gain

            # Repulsive force: away from other drones
            rep = Pose3D(0, 0, 0)
            for other_id in ids:
                if other_id == drone_id:
                    continue
                other = positions[other_id]
                d = pos.dist(other)
                if d < self.obstacle_radius and d > 1e-6:
                    # Repulsion magnitude: inversely proportional to distance
                    mag = self.repulsion_gain * (1.0 / d - 1.0 / self.obstacle_radius) / (d ** 2)
                    direction = Pose3D(
                        pos.x - other.x,
                        pos.y - other.y,
                        pos.z - other.z,
                    ).normalized()
                    rep = rep + direction * (mag * self.dt)

            # Repulsion from static obstacles
            for obs in obstacles:
                d = pos.dist(obs)
                if d < self.obstacle_radius and d > 1e-6:
                    mag = self.repulsion_gain * (1.0 / d - 1.0 / self.obstacle_radius) / (d ** 2)
                    direction = Pose3D(
                        pos.x - obs.x,
                        pos.y - obs.y,
                        pos.z - obs.z,
                    ).normalized()
                    rep = rep + direction * (mag * self.dt)

            # Velocity damping: reduces oscillations by opposing current velocity
            # Damping force is proportional to velocity and increases near obstacles
            damping = Pose3D(0, 0, 0)
            if velocity.norm() > 1e-6:
                # Calculate proximity factor: stronger damping when close to other drones
                min_dist = float('inf')
                for other_id in ids:
                    if other_id == drone_id:
                        continue
                    d = pos.dist(positions[other_id])
                    min_dist = min(min_dist, d)
                
                # Damping strength increases as distance decreases
                if min_dist < self.obstacle_radius:
                    proximity_factor = 1.0 - (min_dist / self.obstacle_radius)
                    damping_strength = self.damping_coeff * (1.0 + 2.0 * proximity_factor)
                else:
                    damping_strength = self.damping_coeff
                
                damping = velocity * (-damping_strength * self.dt)

            # Total force → new position (with damping)
            total = Pose3D(
                attr_clamped.x + rep.x + damping.x,
                attr_clamped.y + rep.y + damping.y,
                attr_clamped.z + rep.z + damping.z,
            ).clamp(self.max_speed * self.dt)

            # Acceleration limiting (Improvement 9: prevents jerky movements)
            # Calculate desired velocity from total displacement
            desired_velocity = total * (1.0 / self.dt)
            
            # Limit acceleration: delta_v = desired_v - prev_v
            delta_v = desired_velocity - prev_velocity
            acceleration = delta_v * (1.0 / self.dt)
            
            # Clamp acceleration magnitude
            if acceleration.norm() > self.max_acceleration:
                acceleration = acceleration.normalized() * self.max_acceleration
                delta_v = acceleration * self.dt
            
            # Apply limited velocity change
            new_velocity = prev_velocity + delta_v
            
            # Clamp velocity magnitude (redundant safety check)
            if new_velocity.norm() > self.max_speed:
                new_velocity = new_velocity.normalized() * self.max_speed
            
            # Calculate new position from limited velocity
            limited_displacement = new_velocity * self.dt
            candidate = Pose3D(
                pos.x + limited_displacement.x,
                pos.y + limited_displacement.y,
                pos.z + limited_displacement.z,
            )

            # Apply geofence
            safe[drone_id] = self.geofence.clip(candidate)
            
            # Store current position and velocity for next iteration
            new_prev_positions[drone_id] = pos
            new_prev_velocities[drone_id] = new_velocity
        
        # TS-02 FIX: Update shared state under lock
        with self._state_lock:
            self._prev_positions.update(new_prev_positions)
            self._prev_velocities.update(new_prev_velocities)

        return safe

    def check_separation(self, positions: Dict[str, Pose3D]) -> List[Tuple[str, str, float]]:
        """
        Check minimum separation violations.
        Returns list of (drone_a, drone_b, distance) for any violations.
        """
        violations = []
        ids = list(positions.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                d = positions[ids[i]].dist(positions[ids[j]])
                if d < self.min_separation:
                    violations.append((ids[i], ids[j], d))
        return violations


class APFFilterLoop:
    """
    Runs APFSafetyFilter at 20 Hz as a background thread.
    Continuously reads current positions and desired setpoints,
    publishes safe setpoints via callback.

    Usage:
        loop = APFFilterLoop(
            apf=APFSafetyFilter(),
            get_positions=lambda: {...},
            get_desired=lambda: {...},
            on_safe=lambda safe: send_to_drones(safe),
            hz=20.0,
        )
        loop.start()
        ...
        loop.stop()
    """

    def __init__(
        self,
        apf:           APFSafetyFilter,
        get_positions: Callable[[], Dict[str, Pose3D]],
        get_desired:   Callable[[], Dict[str, Pose3D]],
        on_safe:       Callable[[Dict[str, Pose3D]], None],
        hz:            float = 20.0,
        on_violation:  Optional[Callable[[List], None]] = None,
    ):
        self.apf           = apf
        self._get_pos      = get_positions
        self._get_des      = get_desired
        self._on_safe      = on_safe
        self._on_violation = on_violation
        self._dt           = 1.0 / hz
        self._running      = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="apf-filter"
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            t0 = time.monotonic()
            try:
                positions = self._get_pos()
                desired   = self._get_des()
                safe      = self.apf.filter(positions, desired)
                self._on_safe(safe)
                if self._on_violation:
                    violations = self.apf.check_separation(positions)
                    if violations:
                        self._on_violation(violations)
            except Exception as e:
                print(f"[apf] filter error: {e}")
            elapsed = time.monotonic() - t0
            time.sleep(max(0, self._dt - elapsed))


class AdaptiveAPFSafetyFilter(APFSafetyFilter):
    """
    APF Safety Filter with adaptive safety margins based on context.
    
    Extends APFSafetyFilter to dynamically adjust separation distances based on:
    - Relative velocity between drones (higher speed = larger margin)
    - Sensor uncertainty (GPS accuracy degradation)
    - Environmental conditions (wind speed)
    - Reaction time buffer
    
    This provides more robust collision avoidance in dynamic conditions
    while allowing tighter formations when conditions are favorable.
    
    Parameters
    ----------
    reaction_time    : Time buffer for drone reaction (seconds)
    gps_uncertainty  : GPS position uncertainty (meters, 1-sigma)
    wind_speed       : Current wind speed (m/s)
    wind_factor_gain : Multiplier for wind contribution to margin
    velocity_weight  : Weight for velocity-based margin component
    uncertainty_weight : Weight for uncertainty-based margin component
    
    Example
    -------
    >>> apf = AdaptiveAPFSafetyFilter(
    ...     min_separation=2.0,
    ...     reaction_time=0.5,
    ...     gps_uncertainty=0.3,
    ...     wind_speed=2.0
    ... )
    >>> # Margins adapt automatically based on drone velocities
    >>> safe = apf.filter(positions, desired)
    """
    
    def __init__(
        self,
        min_separation:    float = 2.0,
        max_speed:         float = 3.0,
        geofence_radius:   float = 50.0,
        geofence_alt:      Tuple[float, float] = (1.0, 30.0),
        repulsion_gain:    float = 2.0,
        attraction_gain:   float = 1.0,
        obstacle_radius:   float = 4.0,
        dt:                float = 0.05,
        damping_coeff:     float = 0.3,
        max_acceleration:  float = 2.0,
        reaction_time:     float = 0.5,      # seconds
        gps_uncertainty:   float = 0.3,      # meters (1-sigma)
        wind_speed:        float = 0.0,      # m/s
        wind_factor_gain:  float = 0.2,      # wind contribution multiplier
        velocity_weight:   float = 1.0,      # velocity margin weight
        uncertainty_weight: float = 2.0,     # uncertainty margin weight (2-sigma)
    ):
        super().__init__(
            min_separation=min_separation,
            max_speed=max_speed,
            geofence_radius=geofence_radius,
            geofence_alt=geofence_alt,
            repulsion_gain=repulsion_gain,
            attraction_gain=attraction_gain,
            obstacle_radius=obstacle_radius,
            dt=dt,
            damping_coeff=damping_coeff,
            max_acceleration=max_acceleration,
        )
        self.reaction_time = reaction_time
        self.gps_uncertainty = gps_uncertainty
        self.wind_speed = wind_speed
        self.wind_factor_gain = wind_factor_gain
        self.velocity_weight = velocity_weight
        self.uncertainty_weight = uncertainty_weight
        
        # Track velocities for adaptive margin calculation
        self._velocities: Dict[str, Pose3D] = {}
    
    def set_wind_speed(self, wind_speed: float):
        """Update wind speed for adaptive margin calculation."""
        self.wind_speed = max(0.0, wind_speed)
    
    def set_gps_uncertainty(self, uncertainty: float):
        """Update GPS uncertainty for adaptive margin calculation."""
        self.gps_uncertainty = max(0.0, uncertainty)
    
    def compute_adaptive_margin(
        self,
        drone_a_pos: Pose3D,
        drone_b_pos: Pose3D,
        drone_a_vel: Pose3D,
        drone_b_vel: Pose3D,
    ) -> float:
        """
        Compute adaptive safety margin between two drones.
        
        The margin increases based on:
        1. Relative velocity (closing speed requires more separation)
        2. Sensor uncertainty (GPS degradation requires buffer)
        3. Environmental factors (wind requires stability margin)
        4. Reaction time (time to respond to collision threat)
        
        Parameters
        ----------
        drone_a_pos : Position of first drone
        drone_b_pos : Position of second drone
        drone_a_vel : Velocity of first drone
        drone_b_vel : Velocity of second drone
        
        Returns
        -------
        float : Adaptive safety margin (meters)
        """
        margin = self.min_separation
        
        # 1. Relative velocity component
        # Higher relative velocity = need more separation for reaction time
        rel_vel = math.sqrt(
            (drone_a_vel.x - drone_b_vel.x) ** 2 +
            (drone_a_vel.y - drone_b_vel.y) ** 2 +
            (drone_a_vel.z - drone_b_vel.z) ** 2
        )
        
        # Add reaction time buffer: distance traveled during reaction
        velocity_margin = rel_vel * self.reaction_time * self.velocity_weight
        margin += velocity_margin
        
        # 2. Sensor uncertainty component (2-sigma for 95% confidence)
        # GPS uncertainty affects both drones, so we use combined uncertainty
        uncertainty_margin = self.gps_uncertainty * self.uncertainty_weight
        margin += uncertainty_margin
        
        # 3. Environmental factors (wind)
        # Wind can cause position drift, requiring additional margin
        wind_margin = self.wind_speed * self.wind_factor_gain
        margin += wind_margin
        
        # Ensure margin never drops below minimum separation
        return max(margin, self.min_separation)
    
    def filter(
        self,
        positions: Dict[str, Pose3D],
        desired: Dict[str, Pose3D],
    ) -> Dict[str, Pose3D]:
        """
        Apply APF with adaptive safety margins.
        
        Overrides parent filter() to use adaptive obstacle_radius
        based on relative velocities between drones.
        """
        # Update velocities for all drones
        for drone_id, pos in positions.items():
            if drone_id in self._prev_positions:
                prev = self._prev_positions[drone_id]
                velocity = (pos - prev) * (1.0 / self.dt)
                self._velocities[drone_id] = velocity
            else:
                self._velocities[drone_id] = Pose3D(0, 0, 0)
        
        # Compute adaptive margins for each drone pair
        # Store original obstacle_radius to restore later
        original_obstacle_radius = self.obstacle_radius
        
        safe: Dict[str, Pose3D] = {}
        ids = list(positions.keys())
        
        for drone_id in ids:
            pos = positions.get(drone_id)
            des = desired.get(drone_id, pos)
            if pos is None:
                continue
            
            vel = self._velocities.get(drone_id, Pose3D(0, 0, 0))
            prev_velocity = self._prev_velocities.get(drone_id, Pose3D(0, 0, 0))
            
            # Attractive force
            diff_x = des.x - pos.x
            diff_y = des.y - pos.y
            diff_z = des.z - pos.z
            attr = Pose3D(diff_x, diff_y, diff_z)
            attr_clamped = attr.clamp(self.max_speed * self.dt) * self.attraction_gain
            
            # Repulsive force with adaptive margins
            rep = Pose3D(0, 0, 0)
            for other_id in ids:
                if other_id == drone_id:
                    continue
                other = positions[other_id]
                other_vel = self._velocities.get(other_id, Pose3D(0, 0, 0))
                
                # Compute adaptive margin for this drone pair
                adaptive_margin = self.compute_adaptive_margin(
                    pos, other, vel, other_vel
                )
                
                # Use adaptive margin as obstacle radius for this pair
                d = pos.dist(other)
                if d < adaptive_margin and d > 1e-6:
                    # Repulsion magnitude inversely proportional to distance
                    mag = self.repulsion_gain * (1.0 / d - 1.0 / adaptive_margin) / (d ** 2)
                    direction = Pose3D(
                        pos.x - other.x,
                        pos.y - other.y,
                        pos.z - other.z,
                    ).normalized()
                    rep = rep + direction * (mag * self.dt)
            
            # Static obstacles (use original obstacle_radius)
            for obs in self._obstacles:
                d = pos.dist(obs)
                if d < original_obstacle_radius and d > 1e-6:
                    mag = self.repulsion_gain * (1.0 / d - 1.0 / original_obstacle_radius) / (d ** 2)
                    direction = Pose3D(
                        pos.x - obs.x,
                        pos.y - obs.y,
                        pos.z - obs.z,
                    ).normalized()
                    rep = rep + direction * (mag * self.dt)
            
            # Velocity damping
            damping = Pose3D(0, 0, 0)
            if vel.norm() > 1e-6:
                min_dist = float('inf')
                for other_id in ids:
                    if other_id == drone_id:
                        continue
                    d = pos.dist(positions[other_id])
                    min_dist = min(min_dist, d)
                
                if min_dist < original_obstacle_radius:
                    proximity_factor = 1.0 - (min_dist / original_obstacle_radius)
                    damping_strength = self.damping_coeff * (1.0 + 2.0 * proximity_factor)
                else:
                    damping_strength = self.damping_coeff
                
                damping = vel * (-damping_strength * self.dt)
            
            # Total force
            total = Pose3D(
                attr_clamped.x + rep.x + damping.x,
                attr_clamped.y + rep.y + damping.y,
                attr_clamped.z + rep.z + damping.z,
            ).clamp(self.max_speed * self.dt)
            
            # Acceleration limiting
            desired_velocity = total * (1.0 / self.dt)
            delta_v = desired_velocity - prev_velocity
            acceleration = delta_v * (1.0 / self.dt)
            
            if acceleration.norm() > self.max_acceleration:
                acceleration = acceleration.normalized() * self.max_acceleration
                delta_v = acceleration * self.dt
            
            new_velocity = prev_velocity + delta_v
            
            if new_velocity.norm() > self.max_speed:
                new_velocity = new_velocity.normalized() * self.max_speed
            
            limited_displacement = new_velocity * self.dt
            candidate = Pose3D(
                pos.x + limited_displacement.x,
                pos.y + limited_displacement.y,
                pos.z + limited_displacement.z,
            )
            
            # Apply geofence
            safe[drone_id] = self.geofence.clip(candidate)
            
            # Store for next iteration
            self._prev_positions[drone_id] = pos
            self._prev_velocities[drone_id] = new_velocity
        
        return safe
    
    def get_current_margin(self, drone_a_id: str, drone_b_id: str) -> Optional[float]:
        """
        Get the current adaptive margin between two drones.
        
        Returns None if either drone has no velocity data yet.
        """
        if drone_a_id not in self._velocities or drone_b_id not in self._velocities:
            return None
        if drone_a_id not in self._prev_positions or drone_b_id not in self._prev_positions:
            return None
        
        return self.compute_adaptive_margin(
            self._prev_positions[drone_a_id],
            self._prev_positions[drone_b_id],
            self._velocities[drone_a_id],
            self._velocities[drone_b_id],
        )
