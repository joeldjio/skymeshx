"""
DroneResearch — ROS2-based UAV Research Middleware Platform.

Core API:
    from droneresearch import Drone, Swarm
    from droneresearch.autopilot import get_backend
    from droneresearch.models import GenericUAVModel, CoordinatorUAVModel
    from droneresearch.simulation import SITLInstance, SITLCluster, TelemetryReplay
    from droneresearch.experiment import Scenario, ScenarioRunner, MetricsCollector
    from droneresearch.safety import APFSafetyFilter, Pose3D
    from droneresearch.llm import SwarmCommander

Autopilot backends:
    mavlink   → ArduPilot + PX4 via MAVLink (pymavlink)
    ardupilot → ArduPilot-specific extensions
    px4       → PX4 native via uXRCE-DDS (ROS2)
"""
from droneresearch.sdk.drone import Drone
from droneresearch.sdk.swarm_api import Swarm

# Export common exceptions for convenience
from droneresearch.exceptions import (
    DroneResearchError,
    ConnectionError,
    HeartbeatTimeoutError,
    InvalidConnectionStringError,
    CommandError,
    CommandRejectedError,
    CommandTimeoutError,
    MissionError,
    MissionUploadError,
    StateTransitionError,
    ConfigurationError,
    InvalidParameterError,
    ROS2Error,
    ROS2NotAvailableError,
    SafetyViolationError,
    GeofenceBreachError,
    CollisionRiskError,
    BatteryLowError,
    DependencyError,
    TimeoutError,
)

__version__ = "0.2.0"
__all__ = [
    "Drone",
    "Swarm",
    # Exceptions
    "DroneResearchError",
    "ConnectionError",
    "HeartbeatTimeoutError",
    "InvalidConnectionStringError",
    "CommandError",
    "CommandRejectedError",
    "CommandTimeoutError",
    "MissionError",
    "MissionUploadError",
    "StateTransitionError",
    "ConfigurationError",
    "InvalidParameterError",
    "ROS2Error",
    "ROS2NotAvailableError",
    "SafetyViolationError",
    "GeofenceBreachError",
    "CollisionRiskError",
    "BatteryLowError",
    "DependencyError",
    "TimeoutError",
]

# Lazy imports — avoids hard dependencies at import time
def get_backend(autopilot: str = "mavlink"):
    from droneresearch.autopilot import get_backend as _get
    return _get(autopilot)

def get_sitl(**kwargs):
    from droneresearch.simulation import SITLInstance
    return SITLInstance(**kwargs)

def get_coordinator(**kwargs):
    from droneresearch.models import CoordinatorUAVModel
    return CoordinatorUAVModel(**kwargs)

def get_swarm_commander(**kwargs):
    from droneresearch.llm import SwarmCommander
    return SwarmCommander(**kwargs)
