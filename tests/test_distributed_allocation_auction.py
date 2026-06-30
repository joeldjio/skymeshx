"""
Test DistributedTaskAllocator auction functionality.

Tests:
- Bid computation
- Task announcement
- Auction process
- Task assignment
- Multi-drone coordination
"""
import time

import pytest

from skymeshx.exploration.distributed_allocation import DistributedTaskAllocator
from skymeshx.safety.apf import Pose3D


def test_allocator_initialization():
    """Test allocator initialization."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0
    )
    
    assert allocator.drone_id == "drone_1"
    assert len(allocator.get_my_tasks()) == 0


def test_bid_computation():
    """Test bid computation with different scenarios."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0
    )
    
    # Close task
    bid1 = allocator.compute_bid("T1", Pose3D(5, 0, 10))
    
    # Far task
    bid2 = allocator.compute_bid("T2", Pose3D(50, 0, 10))
    
    # Close task should have lower bid (better)
    assert bid1 < bid2


def test_low_battery_bid():
    """Test that low battery results in high bid."""
    # High battery
    allocator_high = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 80.0
    )
    
    # Low battery
    allocator_low = DistributedTaskAllocator(
        drone_id="drone_2",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 15.0
    )
    
    task_loc = Pose3D(10, 0, 10)
    
    bid_high = allocator_high.compute_bid("T1", task_loc)
    bid_low = allocator_low.compute_bid("T1", task_loc)
    
    # Low battery should have much higher bid (worse)
    assert bid_low > bid_high * 5


def test_task_announcement():
    """Test task announcement."""
    broadcasts = []
    
    def broadcast_callback(msg_type, data):
        broadcasts.append((msg_type, data))
    
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0
    )
    allocator.set_broadcast_callback(broadcast_callback)
    
    # Announce task
    result = allocator.announce_task("T1", Pose3D(10, 10, 10))
    assert result is True
    
    # Should have broadcast task announcement and bid
    assert len(broadcasts) == 2
    assert broadcasts[0][0] == "task_announce"
    assert broadcasts[1][0] == "bid"


def test_task_assignment():
    """Test task assignment after auction."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5  # Short timeout for testing
    )
    
    # Announce task
    allocator.announce_task("T1", Pose3D(10, 10, 10))
    
    # Wait for auction to complete
    time.sleep(0.6)
    
    # Task should be assigned to drone_1 (only bidder)
    assignment = allocator.get_task_assignment("T1")
    assert assignment == "drone_1"
    
    # Should be in my tasks
    my_tasks = allocator.get_my_tasks()
    assert "T1" in my_tasks


def test_multi_drone_auction():
    """Test auction with multiple drones."""
    # Drone 1: close to task
    d1 = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(5, 5, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    # Drone 2: far from task
    d2 = DistributedTaskAllocator(
        drone_id="drone_2",
        get_position=lambda: Pose3D(50, 50, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    # Drone 3: medium distance
    d3 = DistributedTaskAllocator(
        drone_id="drone_3",
        get_position=lambda: Pose3D(20, 20, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    task_loc = Pose3D(10, 10, 10)
    
    # Drone 1 announces task
    d1.announce_task("T1", task_loc)
    
    # Simulate other drones receiving announcement
    d2.on_message("drone_1", "task_announce", {
        "task_id": "T1",
        "location": {"x": 10.0, "y": 10.0, "z": 10.0}
    }, time.time())
    
    d3.on_message("drone_1", "task_announce", {
        "task_id": "T1",
        "location": {"x": 10.0, "y": 10.0, "z": 10.0}
    }, time.time())
    
    # Simulate bid exchange
    bid1 = d1.compute_bid("T1", task_loc)
    bid2 = d2.compute_bid("T1", task_loc)
    bid3 = d3.compute_bid("T1", task_loc)
    
    # Share bids
    d1.on_message("drone_2", "bid", {"task_id": "T1", "bid": bid2}, time.time())
    d1.on_message("drone_3", "bid", {"task_id": "T1", "bid": bid3}, time.time())
    
    # Wait for assignment
    time.sleep(0.6)
    
    # Drone 1 should win (closest)
    assignment = d1.get_task_assignment("T1")
    assert assignment == "drone_1"
    
    # Verify bid order (lower is better)
    assert bid1 < bid3 < bid2


def test_task_completion():
    """Test marking task as completed."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    # Announce and assign task
    allocator.announce_task("T1", Pose3D(10, 10, 10))
    time.sleep(0.6)
    
    # Task should be in my tasks
    assert "T1" in allocator.get_my_tasks()
    
    # Complete task
    result = allocator.complete_task("T1")
    assert result is True
    
    # Should no longer be in my tasks
    assert "T1" not in allocator.get_my_tasks()


def test_workload_affects_bid():
    """Test that workload affects bid computation."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    task_loc = Pose3D(10, 10, 10)
    
    # Bid with no workload
    bid1 = allocator.compute_bid("T1", task_loc)
    
    # Assign some tasks
    allocator.announce_task("T1", task_loc)
    time.sleep(0.6)
    allocator.announce_task("T2", Pose3D(15, 15, 10))
    time.sleep(0.6)
    
    # Bid with workload
    bid2 = allocator.compute_bid("T3", task_loc)
    
    # Bid should be higher with workload
    assert bid2 > bid1


def test_statistics():
    """Test statistics tracking."""
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0,
        bid_timeout=0.5
    )
    
    # Announce tasks
    allocator.announce_task("T1", Pose3D(10, 10, 10))
    allocator.announce_task("T2", Pose3D(20, 20, 10))
    
    time.sleep(1.0)
    
    stats = allocator.get_statistics()
    assert stats["tasks_announced"] == 2
    assert stats["bids_sent"] == 2
    assert stats["tasks_won"] == 2
    assert stats["active_tasks"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
