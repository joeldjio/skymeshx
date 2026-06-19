"""
Distributed mapping module for swarm coordination.

Provides consensus-based 3D occupancy mapping where each drone maintains
a local map and shares updates with the swarm for collaborative environment
understanding.
"""
from skymeshx.mapping.distributed_map import DistributedOccupancyMap

__all__ = ["DistributedOccupancyMap"]

# Made with Bob
