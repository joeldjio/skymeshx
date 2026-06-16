"""
Distributed 3D Occupancy Map with Consensus-Based Merging.

Provides a collaborative mapping system where each drone maintains a local
3D occupancy grid and shares updates with the swarm. Maps are merged using
confidence-weighted consensus to handle conflicting observations.

Based on: ESCAPE Framework (Shibu et al., 2025)
    "SkySim: A ROS2-based Simulation Environment for Natural Language
     Control of Drone Swarms using Large Language Models"
    arXiv:2602.01226

Frame Convention
----------------
All positions use local NED (North-East-Down) coordinates:
- x: North (meters)
- y: East (meters)
- z: Altitude above ground (meters, positive UP)

Voxel Grid
----------
3D space is discretized into voxels (volumetric pixels).
Each voxel stores:
- occupancy: probability [0.0, 1.0] (0=free, 1=occupied)
- confidence: reliability [0.0, 1.0]
- timestamp: last update time (seconds since epoch)

Usage:
    from droneresearch.mapping import DistributedOccupancyMap
    
    # Create local map
    map = DistributedOccupancyMap(
        voxel_size=0.5,      # 0.5m voxels
        bounds=((-50, 50), (-50, 50), (0, 30)),  # x, y, z ranges
        decay_rate=0.1,      # confidence decay per second
    )
    
    # Update from sensor observations
    map.update_voxel(x=10, y=5, z=15, occupancy=0.9, confidence=0.8)
    
    # Share with other drones
    map_data = map.get_map_data()
    
    # Merge remote map
    map.merge_remote("D2", remote_map_data)
    
    # Query occupancy
    occ, conf = map.get_occupancy(x=10, y=5, z=15)
"""
import math
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class VoxelData:
    """Data stored in each voxel of the occupancy map."""
    occupancy: float   # [0.0, 1.0] - probability of occupancy
    confidence: float  # [0.0, 1.0] - reliability of measurement
    timestamp: float   # seconds since epoch
    
    def __post_init__(self):
        """Validate voxel data ranges."""
        self.occupancy = max(0.0, min(1.0, self.occupancy))
        self.confidence = max(0.0, min(1.0, self.confidence))


class DistributedOccupancyMap:
    """
    Distributed 3D occupancy map with consensus-based merging.
    
    Each drone maintains a local map and shares updates with the swarm.
    When receiving remote map data, uses confidence-weighted averaging
    to merge conflicting observations.
    
    Parameters
    ----------
    voxel_size : Size of each voxel in meters (default 0.5m)
    bounds : ((x_min, x_max), (y_min, y_max), (z_min, z_max)) in meters
    decay_rate : Confidence decay rate per second (default 0.1)
    min_confidence : Minimum confidence threshold for keeping voxels (default 0.1)
    max_age : Maximum age in seconds before voxel is removed (default 30.0)
    
    Thread Safety
    -------------
    All public methods are thread-safe using internal locking.
    """
    
    def __init__(
        self,
        voxel_size: float = 0.5,
        bounds: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]] = (
            (-50.0, 50.0),  # x: North
            (-50.0, 50.0),  # y: East
            (0.0, 30.0),    # z: altitude
        ),
        decay_rate: float = 0.1,
        min_confidence: float = 0.1,
        max_age: float = 30.0,
    ):
        self.voxel_size = voxel_size
        self.bounds = bounds
        self.decay_rate = decay_rate
        self.min_confidence = min_confidence
        self.max_age = max_age
        
        # Local map: {(ix, iy, iz): VoxelData}
        self._local_map: Dict[Tuple[int, int, int], VoxelData] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self._merge_count = 0
        self._update_count = 0
        self._consensus_count = 0
    
    def _world_to_voxel(self, x: float, y: float, z: float) -> Tuple[int, int, int]:
        """Convert world coordinates to voxel indices."""
        ix = int(math.floor(x / self.voxel_size))
        iy = int(math.floor(y / self.voxel_size))
        iz = int(math.floor(z / self.voxel_size))
        return (ix, iy, iz)
    
    def _voxel_to_world(self, ix: int, iy: int, iz: int) -> Tuple[float, float, float]:
        """Convert voxel indices to world coordinates (voxel center)."""
        x = (ix + 0.5) * self.voxel_size
        y = (iy + 0.5) * self.voxel_size
        z = (iz + 0.5) * self.voxel_size
        return (x, y, z)
    
    def _is_in_bounds(self, x: float, y: float, z: float) -> bool:
        """Check if world coordinates are within map bounds."""
        (x_min, x_max), (y_min, y_max), (z_min, z_max) = self.bounds
        return (x_min <= x <= x_max and
                y_min <= y <= y_max and
                z_min <= z <= z_max)
    
    def update_voxel(
        self,
        x: float,
        y: float,
        z: float,
        occupancy: float,
        confidence: float = 1.0,
    ) -> bool:
        """
        Update a single voxel with new observation.
        
        Parameters
        ----------
        x, y, z : World coordinates (meters)
        occupancy : Occupancy probability [0.0, 1.0]
        confidence : Measurement confidence [0.0, 1.0]
        
        Returns
        -------
        bool : True if update successful, False if out of bounds
        """
        if not self._is_in_bounds(x, y, z):
            return False
        
        voxel = self._world_to_voxel(x, y, z)
        timestamp = time.time()
        
        with self._lock:
            self._local_map[voxel] = VoxelData(occupancy, confidence, timestamp)
            self._update_count += 1
        
        return True
    
    def get_occupancy(
        self,
        x: float,
        y: float,
        z: float,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Get occupancy and confidence at world coordinates.
        
        Returns
        -------
        (occupancy, confidence) : Both None if voxel not in map
        """
        if not self._is_in_bounds(x, y, z):
            return (None, None)
        
        voxel = self._world_to_voxel(x, y, z)
        
        with self._lock:
            if voxel not in self._local_map:
                return (None, None)
            
            data = self._local_map[voxel]
            
            # Apply confidence decay
            age = time.time() - data.timestamp
            decayed_confidence = data.confidence * math.exp(-self.decay_rate * age)
            
            return (data.occupancy, decayed_confidence)
    
    def get_map_data(self) -> Dict[Tuple[int, int, int], Tuple[float, float, float]]:
        """
        Get current map data for sharing with other drones.
        
        Returns
        -------
        Dict mapping voxel indices to (occupancy, confidence, timestamp)
        """
        with self._lock:
            return {
                voxel: (data.occupancy, data.confidence, data.timestamp)
                for voxel, data in self._local_map.items()
            }
    
    def merge_remote(
        self,
        drone_id: str,
        map_data: Dict[Tuple[int, int, int], Tuple[float, float, float]],
    ) -> int:
        """
        Merge remote map data using confidence-weighted consensus.
        
        For each voxel:
        - If only in local map: keep local
        - If only in remote map: add remote
        - If in both: compute weighted average based on confidence
        
        Parameters
        ----------
        drone_id : ID of drone providing map data
        map_data : Dict mapping voxel to (occupancy, confidence, timestamp)
        
        Returns
        -------
        int : Number of voxels merged
        """
        merged_count = 0
        current_time = time.time()
        
        with self._lock:
            for voxel, (remote_occ, remote_conf, remote_time) in map_data.items():
                # Skip if remote data is too old
                age = current_time - remote_time
                if age > self.max_age:
                    continue
                
                # Apply decay to remote confidence
                decayed_remote_conf = remote_conf * math.exp(-self.decay_rate * age)
                
                if decayed_remote_conf < self.min_confidence:
                    continue
                
                if voxel in self._local_map:
                    # Consensus: weighted average
                    local_data = self._local_map[voxel]
                    local_age = current_time - local_data.timestamp
                    decayed_local_conf = local_data.confidence * math.exp(-self.decay_rate * local_age)
                    
                    if decayed_local_conf < self.min_confidence:
                        # Local data too old, replace with remote
                        self._local_map[voxel] = VoxelData(
                            remote_occ,
                            decayed_remote_conf,
                            remote_time,
                        )
                    else:
                        # Weighted consensus
                        total_conf = decayed_local_conf + decayed_remote_conf
                        consensus_occ = (
                            local_data.occupancy * decayed_local_conf +
                            remote_occ * decayed_remote_conf
                        ) / total_conf
                        
                        # Consensus confidence: average of both (capped at 1.0)
                        consensus_conf = min(total_conf / 2.0, 1.0)
                        
                        # Use most recent timestamp
                        consensus_time = max(local_data.timestamp, remote_time)
                        
                        self._local_map[voxel] = VoxelData(
                            consensus_occ,
                            consensus_conf,
                            consensus_time,
                        )
                        self._consensus_count += 1
                else:
                    # New voxel from remote
                    self._local_map[voxel] = VoxelData(
                        remote_occ,
                        decayed_remote_conf,
                        remote_time,
                    )
                
                merged_count += 1
            
            self._merge_count += 1
        
        return merged_count
    
    def cleanup_old_voxels(self) -> int:
        """
        Remove voxels with low confidence or old age.
        
        Returns
        -------
        int : Number of voxels removed
        """
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            voxels_to_remove = []
            
            for voxel, data in self._local_map.items():
                age = current_time - data.timestamp
                decayed_conf = data.confidence * math.exp(-self.decay_rate * age)
                
                if decayed_conf < self.min_confidence or age > self.max_age:
                    voxels_to_remove.append(voxel)
            
            for voxel in voxels_to_remove:
                del self._local_map[voxel]
                removed_count += 1
        
        return removed_count
    
    def get_occupied_voxels(
        self,
        threshold: float = 0.5,
        min_confidence: float = 0.3,
    ) -> List[Tuple[float, float, float]]:
        """
        Get list of occupied voxel centers in world coordinates.
        
        Parameters
        ----------
        threshold : Occupancy threshold [0.0, 1.0]
        min_confidence : Minimum confidence threshold
        
        Returns
        -------
        List of (x, y, z) world coordinates
        """
        current_time = time.time()
        occupied = []
        
        with self._lock:
            for voxel, data in self._local_map.items():
                age = current_time - data.timestamp
                decayed_conf = data.confidence * math.exp(-self.decay_rate * age)
                
                if data.occupancy >= threshold and decayed_conf >= min_confidence:
                    x, y, z = self._voxel_to_world(*voxel)
                    occupied.append((x, y, z))
        
        return occupied
    
    def get_statistics(self) -> Dict[str, int]:
        """Get map statistics."""
        with self._lock:
            return {
                "voxel_count": len(self._local_map),
                "update_count": self._update_count,
                "merge_count": self._merge_count,
                "consensus_count": self._consensus_count,
            }
    
    def clear(self):
        """Clear all map data."""
        with self._lock:
            self._local_map.clear()
            self._update_count = 0
            self._merge_count = 0
            self._consensus_count = 0

# Made with Bob
