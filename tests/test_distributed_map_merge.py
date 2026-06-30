"""
Tests for DistributedOccupancyMap merging operations.

Verifies map data sharing, merging, cleanup, and query operations.
"""
import time
import pytest
from skymeshx.mapping import DistributedOccupancyMap


def test_basic_update_and_query():
    """Basic voxel update and query."""
    map1 = DistributedOccupancyMap(voxel_size=1.0)
    
    # Update voxel
    success = map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    assert success
    
    # Query voxel
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    assert occ == 0.8
    assert abs(conf - 0.9) < 0.01  # Allow small decay


def test_update_out_of_bounds():
    """Updates outside bounds should fail."""
    map1 = DistributedOccupancyMap(
        voxel_size=1.0,
        bounds=((-10, 10), (-10, 10), (0, 20))
    )
    
    # In bounds
    assert map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8)
    
    # Out of bounds
    assert not map1.update_voxel(x=50.0, y=5.0, z=10.0, occupancy=0.8)
    assert not map1.update_voxel(x=5.0, y=50.0, z=10.0, occupancy=0.8)
    assert not map1.update_voxel(x=5.0, y=5.0, z=50.0, occupancy=0.8)


def test_query_nonexistent_voxel():
    """Query of non-existent voxel should return None."""
    map1 = DistributedOccupancyMap(voxel_size=1.0)
    
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    assert occ is None
    assert conf is None


def test_get_map_data():
    """get_map_data should return all voxels."""
    map1 = DistributedOccupancyMap(voxel_size=1.0)
    
    # Add multiple voxels
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    map1.update_voxel(x=10.0, y=10.0, z=15.0, occupancy=0.6, confidence=0.7)
    
    map_data = map1.get_map_data()
    
    assert len(map_data) == 2
    assert (5, 5, 10) in map_data
    assert (10, 10, 15) in map_data


def test_merge_new_voxels():
    """Merging should add new voxels from remote."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Local has voxel A
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Remote has voxel B
    remote_data = {
        (10, 10, 15): (0.6, 0.7, time.time())
    }
    
    merged = map1.merge_remote("D2", remote_data)
    
    assert merged == 1
    
    # Both voxels should exist
    occ_a, _ = map1.get_occupancy(5.0, 5.0, 10.0)
    occ_b, _ = map1.get_occupancy(10.0, 10.0, 15.0)
    
    assert occ_a == 0.8
    assert occ_b == 0.6


def test_merge_returns_count():
    """merge_remote should return number of voxels merged."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    remote_data = {
        (5, 5, 10): (0.8, 0.9, time.time()),
        (10, 10, 15): (0.6, 0.7, time.time()),
        (15, 15, 20): (0.4, 0.5, time.time()),
    }
    
    merged = map1.merge_remote("D2", remote_data)
    
    assert merged == 3


def test_merge_skips_old_data():
    """Merge should skip data older than max_age."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, max_age=10.0)
    
    # Remote data from 20 seconds ago (too old)
    old_time = time.time() - 20.0
    remote_data = {
        (5, 5, 10): (0.8, 0.9, old_time)
    }
    
    merged = map1.merge_remote("D2", remote_data)
    
    assert merged == 0
    
    # Voxel should not exist
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    assert occ is None


def test_merge_skips_low_confidence():
    """Merge should skip data below min_confidence after decay."""
    map1 = DistributedOccupancyMap(
        voxel_size=1.0,
        decay_rate=1.0,
        min_confidence=0.3,
    )
    
    # Remote data from 2 seconds ago with confidence 0.5
    # After decay: 0.5 * exp(-1.0 * 2) ≈ 0.068 < 0.3
    old_time = time.time() - 2.0
    remote_data = {
        (5, 5, 10): (0.8, 0.5, old_time)
    }
    
    merged = map1.merge_remote("D2", remote_data)
    
    assert merged == 0


def test_cleanup_old_voxels():
    """cleanup_old_voxels should remove expired data."""
    map1 = DistributedOccupancyMap(
        voxel_size=1.0,
        decay_rate=1.0,
        min_confidence=0.3,
    )
    
    # Add voxel
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.5)
    
    # Wait for decay
    time.sleep(2.0)
    
    # Cleanup should remove it
    removed = map1.cleanup_old_voxels()
    
    assert removed == 1
    
    # Voxel should be gone
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    assert occ is None


def test_cleanup_keeps_fresh_data():
    """cleanup_old_voxels should keep fresh data."""
    map1 = DistributedOccupancyMap(
        voxel_size=1.0,
        decay_rate=0.1,
        min_confidence=0.3,
    )
    
    # Add fresh voxel
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Cleanup immediately
    removed = map1.cleanup_old_voxels()
    
    assert removed == 0
    
    # Voxel should still exist
    occ, conf = map1.get_occupancy(5.0, 5.0, 10.0)
    assert occ == 0.8


def test_get_occupied_voxels():
    """get_occupied_voxels should return occupied positions."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Add occupied voxel
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.9, confidence=0.8)
    
    # Add free voxel
    map1.update_voxel(x=10.0, y=10.0, z=15.0, occupancy=0.1, confidence=0.8)
    
    # Add low confidence voxel
    map1.update_voxel(x=15.0, y=15.0, z=20.0, occupancy=0.9, confidence=0.1)
    
    occupied = map1.get_occupied_voxels(threshold=0.5, min_confidence=0.3)
    
    # Should only include first voxel (occupied + high confidence)
    assert len(occupied) == 1
    x, y, z = occupied[0]
    assert abs(x - 5.5) < 0.1  # Voxel center
    assert abs(y - 5.5) < 0.1
    assert abs(z - 10.5) < 0.1


def test_voxel_quantization():
    """Multiple positions in same voxel should map to same voxel."""
    map1 = DistributedOccupancyMap(voxel_size=1.0)
    
    # Update same voxel from different positions
    map1.update_voxel(x=5.1, y=5.2, z=10.3, occupancy=0.8, confidence=0.9)
    map1.update_voxel(x=5.7, y=5.8, z=10.9, occupancy=0.6, confidence=0.7)
    
    # Should overwrite (same voxel)
    map_data = map1.get_map_data()
    assert len(map_data) == 1
    
    # Last update should win
    occ, conf = map1.get_occupancy(5.5, 5.5, 10.5)
    assert occ == 0.6
    assert abs(conf - 0.7) < 0.01  # Allow small decay


def test_statistics():
    """Statistics should track operations."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 0
    assert stats["update_count"] == 0
    assert stats["merge_count"] == 0
    
    # Update
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 1
    assert stats["update_count"] == 1
    
    # Merge
    remote_data = {
        (10, 10, 15): (0.6, 0.7, time.time())
    }
    map1.merge_remote("D2", remote_data)
    
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 2
    assert stats["merge_count"] == 1


def test_clear():
    """clear should remove all data."""
    map1 = DistributedOccupancyMap(voxel_size=1.0)
    
    # Add data
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    map1.update_voxel(x=10.0, y=10.0, z=15.0, occupancy=0.6, confidence=0.7)
    
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 2
    
    # Clear
    map1.clear()
    
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 0
    assert stats["update_count"] == 0
    assert stats["merge_count"] == 0


def test_confidence_decay_over_time():
    """Confidence should decay over time."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.5)
    
    # Add voxel
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Immediate query
    _, conf0 = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Wait 1 second
    time.sleep(1.0)
    
    # Query again
    _, conf1 = map1.get_occupancy(5.0, 5.0, 10.0)
    
    # Confidence should have decayed
    assert conf1 < conf0
    
    # Expected: 0.9 * exp(-0.5 * 1) ≈ 0.546
    assert abs(conf1 - 0.546) < 0.05


def test_multi_drone_merge():
    """Multiple drones can merge their maps."""
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    map2 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    map3 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    # Each drone observes different area
    map1.update_voxel(x=5.0, y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    map2.update_voxel(x=10.0, y=10.0, z=15.0, occupancy=0.6, confidence=0.7)
    map3.update_voxel(x=15.0, y=15.0, z=20.0, occupancy=0.4, confidence=0.5)
    
    # Share maps
    map1.merge_remote("D2", map2.get_map_data())
    map1.merge_remote("D3", map3.get_map_data())
    
    # Map1 should have all observations
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 3
    
    # All voxels should be queryable
    occ1, _ = map1.get_occupancy(5.0, 5.0, 10.0)
    occ2, _ = map1.get_occupancy(10.0, 10.0, 15.0)
    occ3, _ = map1.get_occupancy(15.0, 15.0, 20.0)
    
    assert occ1 == 0.8
    assert occ2 == 0.6
    assert occ3 == 0.4


def test_thread_safety():
    """Map operations should be thread-safe."""
    import threading
    
    map1 = DistributedOccupancyMap(voxel_size=1.0, decay_rate=0.0)
    
    def update_worker(start_x):
        for i in range(10):
            x = start_x + i
            map1.update_voxel(x=float(x), y=5.0, z=10.0, occupancy=0.8, confidence=0.9)
    
    # Multiple threads updating
    threads = [
        threading.Thread(target=update_worker, args=(0,)),
        threading.Thread(target=update_worker, args=(10,)),
        threading.Thread(target=update_worker, args=(20,)),
    ]
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    # Should have 30 voxels
    stats = map1.get_statistics()
    assert stats["voxel_count"] == 30
