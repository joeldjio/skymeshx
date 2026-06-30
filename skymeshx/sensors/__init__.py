"""
Sensor integration modules for UAV perception.

Modules:
    depth_camera   : ROS2 depth camera/point cloud subscriber
    thermal_camera : ROS2 thermal camera subscriber for solar inspection
"""
from __future__ import annotations

__all__ = []

# Optional ROS2 depth camera support
try:
    from skymeshx.sensors.depth_camera import DepthCameraSubscriber
    __all__.append("DepthCameraSubscriber")
    _DEPTH_CAMERA_OK = True
except ImportError:
    _DEPTH_CAMERA_OK = False

# Optional ROS2 thermal camera support
try:
    from skymeshx.sensors.thermal_camera import (
        ThermalCameraSubscriber,
        ThermalHotspotDetector
    )
    __all__.extend(["ThermalCameraSubscriber", "ThermalHotspotDetector"])
    _THERMAL_CAMERA_OK = True
except ImportError:
    _THERMAL_CAMERA_OK = False
