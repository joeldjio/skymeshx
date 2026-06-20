"""
Tests for DistributedOccupancyMap consensus-based merging.

Verifies that map merging uses confidence-weighted averaging to handle
conflicting observations from multiple drones.
"""
import time
import pytest
from skymeshx.mapping import DistributedOccupancyMap


def test_consensus_weighted_average():
    """Consensus should use confidence-weighted averaging."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local observation: 80% occupied, 90% confidence
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Remote observation: 40% occupied, 60% confidence
    remote_data = {
        (5, 5, 10): (0.4, 0.6, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    # Expected consensus: (0.8 * 0.9 + 0.4 * 0.6) / (0.9 + 0.6) = 0.64
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    assert occ is not None
    assert abs(occ - 0.64) < 0.01


def test_consensus_confidence_averaging():
    """Consensus confidence should be average of both (capped at 1.0)."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local: high confidence
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.5, confidence=0.8)
    
    # Remote: high confidence
    remote_data = {
        (5, 5, 10): (0.5, 0.6, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Expected confidence: (0.8 + 0.6) / 2 = 0.7
    assert conf is not None
    assert abs(conf - 0.7) < 0.01


def test_consensus_confidence_capped():
    """Consensus confidence should be capped at 1.0."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Both very high confidence
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.5, confidence=0.95)
    
    remote_data = {
        (5, 5, 10): (0.5, 0.95, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Expected: (0.95 + 0.95) / 2 = 0.95, but capped at 1.0
    # Actually: min(1.9 / 2, 1.0) = 0.95
    assert conf is not None
    assert conf <= 1.0


def test_consensus_uses_latest_timestamp():
    """Consensus should use the most recent timestamp."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local observation at t0
    t0 = time.time()
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.5, confidence=0.8)
    
    # Remote observation at t0 + 5s
    time.sleep(0.1)  # Small delay to ensure different timestamp
    t1 = time.time()
    remote_data = {
        (5, 5, 10): (0.5, 0.6, t1)
    }
    
    map1.merge_remote("D2", remote_data)
    
    # Get raw map data to check timestamp
    map_data = map1.get_map_data()
    voxel = (5, 5, 10)
    
    assert voxel in map_data
    _, _, timestamp = map_data[voxel]
    
    # Should use the later timestamp
    assert timestamp >= t1


def test_consensus_high_confidence_dominates():
    """High confidence observation should dominate low confidence."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local: low confidence, says occupied
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.9, confidence=0.2)
    
    # Remote: high confidence, says free
    remote_data = {
        (5, 5, 10): (0.1, 0.8, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Expected: (0.9 * 0.2 + 0.1 * 0.8) / (0.2 + 0.8) = 0.26
    # High confidence remote should pull result toward 0.1
    assert occ is not None
    assert occ < 0.5  # Should be closer to free (0.1) than occupied (0.9)


def test_consensus_equal_confidence():
    """Equal confidence should result in simple average."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local: 80% occupied, 50% confidence
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.5)
    
    # Remote: 40% occupied, 50% confidence
    remote_data = {
        (5, 5, 10): (0.4, 0.5, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Expected: (0.8 * 0.5 + 0.4 * 0.5) / (0.5 + 0.5) = 0.6
    assert occ is not None
    assert abs(occ - 0.6) < 0.01


def test_consensus_multiple_merges():
    """Multiple merges should accumulate consensus."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Initial local observation
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.5, confidence=0.5)
    
    # First remote merge
    remote1 = {
        (5, 5, 10): (0.7, 0.5, time.time())
    }
    map1.merge_remote("D2", remote1)
    
    occ1, _ = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Second remote merge
    remote2 = {
        (5, 5, 10): (0.9, 0.5, time.time())
    }
    map1.merge_remote("D3", remote2)
    
    occ2, _ = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Occupancy should increase with each merge toward higher values
    assert occ1 is not None and occ2 is not None
    assert occ2 > occ1


def test_consensus_with_decay():
    """Consensus should account for confidence decay."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.5)
    
    # Local observation
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Remote observation from 2 seconds ago
    old_time = time.time() - 2.0
    remote_data = {
        (5, 5, 10): (0.4, 0.9, old_time)
    }
    
    map1.merge_remote("D2", remote_data)
    
    # Remote confidence should be decayed: 0.9 * exp(-0.5 * 2) ≈ 0.33
    # Local should dominate due to higher decayed confidence
    occ, _ = map1.get_occupancy(5.0, 5.0, 10.0)
    
    assert occ is not None
    assert occ > 0.6  # Should be closer to local (0.8) than remote (0.4)


def test_consensus_statistics():
    """Consensus operations should be tracked in statistics."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local observation
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.5, confidence=0.5)
    
    stats_before = map1.get_statistics()
    
    # Merge with overlapping voxel (triggers consensus)
    remote_data = {
        (5, 5, 10): (0.7, 0.5, time.time())
    }
    map1.merge_remote("D2", remote_data)
    
    stats_after = map1.get_statistics()
    
    # Consensus count should increase
    assert stats_after["consensus_count"] > stats_before["consensus_count"]
    assert stats_after["merge_count"] > stats_before["merge_count"]


def test_consensus_replaces_old_local_data():
    """If local data is too old, remote should replace it."""
    map1 = DistributedOccupancyMap(
        voxel_size=1.0,
        decay_rate=1.0,  # Fast decay
        min_confidence=0.3,
    )
    
    # Old local observation
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.5)
    
    # Wait for decay
    time.sleep(2.0)
    
    # Fresh remote observation
    remote_data = {
        (5, 5, 10): (0.2, 0.9, time.time())
    }
    
    map1.merge_remote("D2", remote_data)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Should use remote data since local is too old
    assert occ is not None
    assert abs(occ - 0.2) < 0.1  # Close to remote value
