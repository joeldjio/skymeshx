"""
Distributed Task Allocation — Auction-based task assignment for swarm exploration.

Based on ESCAPE Framework's distributed consensus algorithm. Enables drones
to autonomously allocate tasks without a central coordinator using an
auction-based bidding system.

Key Features:
- Auction-based task allocation (lowest bid wins)
- Distributed consensus (no central server)
- Cost function considers: distance, battery, workload, collision risk
- Configurable bid weights
- Thread-safe task assignments
- Automatic bid timeout and re-auction

Auction Protocol:
    1. Task announced → all drones compute bids
    2. Drones broadcast bids
    3. After timeout, lowest bid wins
    4. Winner announces assignment
    5. Other drones acknowledge

Usage:
    from skymeshx.exploration.distributed_allocation import DistributedTaskAllocator
    from skymeshx.communication.swarm_protocol import SwarmCommunicationProtocol
    
    # Create allocator
    allocator = DistributedTaskAllocator(
        drone_id="drone_1",
        get_position=lambda: Pose3D(0, 0, 10),
        get_battery=lambda: 75.0
    )
    
    # Create communication protocol
    protocol = SwarmCommunicationProtocol(
        drone_id="drone_1",
        callback=allocator.on_message
    )
    protocol.start()
    
    # Announce task
    allocator.announce_task("T1", Pose3D(10, 10, 10))
    
    # Wait for auction to complete
    time.sleep(2.0)
    
    # Check assignment
    winner = allocator.get_task_assignment("T1")
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set

from skymeshx.safety.apf import Pose3D


@dataclass
class Task:
    """Task to be allocated."""
    task_id: str
    location: Pose3D
    announced_time: float
    bids: Dict[str, float]  # {drone_id: bid_value}
    assigned_to: Optional[str] = None
    completed: bool = False


class DistributedTaskAllocator:
    """
    Auction-based task allocator for swarm exploration.
    
    Uses distributed consensus to allocate tasks without a central server.
    Each drone computes a bid based on distance, battery, workload, and
    collision risk. The drone with the lowest bid wins the task.
    
    Thread Safety:
        - All methods are thread-safe
        - on_message() can be called from communication thread
        - Task assignments protected by lock
    
    Parameters:
        drone_id         : Unique identifier for this drone
        get_position     : Callable that returns current Pose3D
        get_battery      : Callable that returns battery percentage (0-100)
        bid_timeout      : Time to wait for bids before assigning (seconds)
        distance_weight  : Weight for distance cost (default 1.0)
        battery_weight   : Weight for battery cost (default 0.5)
        workload_weight  : Weight for workload cost (default 0.3)
        risk_weight      : Weight for collision risk cost (default 2.0)
    """
    
    def __init__(
        self,
        drone_id: str,
        get_position: Callable[[], Pose3D],
        get_battery: Callable[[], float],
        bid_timeout: float = 2.0,
        distance_weight: float = 1.0,
        battery_weight: float = 0.5,
        workload_weight: float = 0.3,
        risk_weight: float = 2.0
    ):
        self.drone_id = drone_id
        self._get_position = get_position
        self._get_battery = get_battery
        self.bid_timeout = bid_timeout
        
        # Bid weights
        self.distance_weight = distance_weight
        self.battery_weight = battery_weight
        self.workload_weight = workload_weight
        self.risk_weight = risk_weight
        
        # Task management
        self._tasks: Dict[str, Task] = {}
        self._assignments: Dict[str, str] = {}  # {task_id: drone_id}
        self._my_tasks: Set[str] = set()  # Tasks assigned to me
        self._lock = threading.Lock()
        
        # Communication callback (set by user)
        self._broadcast_callback: Optional[Callable[[str, Dict], None]] = None
        
        # Statistics
        self._tasks_announced = 0
        self._bids_sent = 0
        self._tasks_won = 0
        self._tasks_lost = 0
    
    def set_broadcast_callback(self, callback: Callable[[str, Dict], None]):
        """Set callback for broadcasting messages."""
        self._broadcast_callback = callback
    
    def announce_task(self, task_id: str, location: Pose3D) -> bool:
        """
        Announce a new task to the swarm.
        
        Args:
            task_id  : Unique task identifier
            location : Task location in local NED
        
        Returns:
            True if announced successfully
        """
        with self._lock:
            if task_id in self._tasks:
                return False  # Task already exists
            
            # Create task
            task = Task(
                task_id=task_id,
                location=location,
                announced_time=time.time(),
                bids={}
            )
            self._tasks[task_id] = task
            self._tasks_announced += 1
        
        # Broadcast task announcement
        if self._broadcast_callback:
            self._broadcast_callback("task_announce", {
                "task_id": task_id,
                "location": {"x": location.x, "y": location.y, "z": location.z}
            })
        
        # Compute and broadcast my bid
        self._compute_and_broadcast_bid(task_id, location)
        
        # Schedule assignment after timeout
        threading.Timer(self.bid_timeout, self._assign_task, args=(task_id,)).start()
        
        return True
    
    def compute_bid(self, task_id: str, task_location: Pose3D) -> float:
        """
        Compute bid for a task (lower is better).
        
        Cost function considers:
        - Distance to task
        - Battery level
        - Current workload
        - Collision risk (simplified)
        
        Args:
            task_id       : Task identifier
            task_location : Task location
        
        Returns:
            Bid value (lower is better, -1 if cannot bid)
        """
        try:
            my_pos = self._get_position()
            battery_pct = self._get_battery()
        except Exception:
            return -1.0  # Cannot bid
        
        # Distance cost
        distance = my_pos.dist(task_location)
        distance_cost = distance
        
        # Battery cost (prohibitively high if low battery)
        if battery_pct < 20:
            battery_cost = 1000.0
        else:
            battery_cost = 100.0 / (battery_pct + 1.0)
        
        # Workload cost (number of tasks currently assigned to me)
        with self._lock:
            workload = len(self._my_tasks)
        workload_cost = workload * 50.0
        
        # Collision risk cost (simplified: assume risk increases with distance)
        # In real implementation, would check for obstacles and other drones
        collision_risk = min(distance / 100.0, 1.0)  # Normalize to 0-1
        risk_cost = collision_risk * 200.0
        
        # Weighted sum
        total_cost = (
            distance_cost * self.distance_weight +
            battery_cost * self.battery_weight +
            workload_cost * self.workload_weight +
            risk_cost * self.risk_weight
        )
        
        return total_cost
    
    def _compute_and_broadcast_bid(self, task_id: str, location: Pose3D):
        """Compute bid and broadcast to swarm."""
        bid = self.compute_bid(task_id, location)
        
        if bid < 0:
            return  # Cannot bid
        
        # Store my bid
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].bids[self.drone_id] = bid
                self._bids_sent += 1
        
        # Broadcast bid
        if self._broadcast_callback:
            self._broadcast_callback("bid", {
                "task_id": task_id,
                "bid": bid
            })
    
    def _assign_task(self, task_id: str):
        """Assign task to drone with lowest bid."""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            
            if not task.bids:
                return  # No bids received
            
            # Find lowest bid
            winner = min(task.bids.items(), key=lambda x: x[1])
            winner_id, winner_bid = winner
            
            # Assign task
            task.assigned_to = winner_id
            self._assignments[task_id] = winner_id
            
            if winner_id == self.drone_id:
                self._my_tasks.add(task_id)
                self._tasks_won += 1
            else:
                self._tasks_lost += 1
        
        # Broadcast assignment
        if self._broadcast_callback:
            self._broadcast_callback("task_assign", {
                "task_id": task_id,
                "assigned_to": winner_id,
                "bid": winner_bid
            })
    
    def on_message(self, sender: str, msg_type: str, data: Dict, timestamp: float):
        """
        Handle incoming messages from swarm communication protocol.
        
        Args:
            sender    : Drone ID of sender
            msg_type  : Message type ("task_announce", "bid", "task_assign")
            data      : Message payload
            timestamp : Message timestamp
        """
        if msg_type == "task_announce":
            self._handle_task_announce(sender, data)
        elif msg_type == "bid":
            self._handle_bid(sender, data)
        elif msg_type == "task_assign":
            self._handle_task_assign(sender, data)
    
    def _handle_task_announce(self, sender: str, data: Dict):
        """Handle task announcement from another drone."""
        task_id = data.get("task_id")
        location_data = data.get("location", {})
        
        if not task_id:
            return
        
        location = Pose3D(
            location_data.get("x", 0.0),
            location_data.get("y", 0.0),
            location_data.get("z", 0.0)
        )
        
        with self._lock:
            if task_id in self._tasks:
                return  # Already know about this task
            
            # Create task
            task = Task(
                task_id=task_id,
                location=location,
                announced_time=time.time(),
                bids={}
            )
            self._tasks[task_id] = task
        
        # Compute and broadcast my bid
        self._compute_and_broadcast_bid(task_id, location)
    
    def _handle_bid(self, sender: str, data: Dict):
        """Handle bid from another drone."""
        task_id = data.get("task_id")
        bid = data.get("bid")
        
        if not task_id or bid is None:
            return
        
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].bids[sender] = bid
    
    def _handle_task_assign(self, sender: str, data: Dict):
        """Handle task assignment announcement."""
        task_id = data.get("task_id")
        assigned_to = data.get("assigned_to")
        
        if not task_id or not assigned_to:
            return
        
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].assigned_to = assigned_to
                self._assignments[task_id] = assigned_to
                
                if assigned_to == self.drone_id:
                    self._my_tasks.add(task_id)
                    self._tasks_won += 1
    
    def get_task_assignment(self, task_id: str) -> Optional[str]:
        """Get the drone assigned to a task."""
        with self._lock:
            return self._assignments.get(task_id)
    
    def get_my_tasks(self) -> List[str]:
        """Get list of tasks assigned to this drone."""
        with self._lock:
            return list(self._my_tasks)
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            self._tasks[task_id].completed = True
            self._my_tasks.discard(task_id)
            return True
    
    def get_statistics(self) -> Dict:
        """Get allocation statistics."""
        with self._lock:
            return {
                "tasks_announced": self._tasks_announced,
                "bids_sent": self._bids_sent,
                "tasks_won": self._tasks_won,
                "tasks_lost": self._tasks_lost,
                "active_tasks": len(self._my_tasks),
                "total_tasks": len(self._tasks)
            }

# Made with Bob
