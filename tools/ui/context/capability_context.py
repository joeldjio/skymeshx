"""
CapabilityContext - QML-facing hardware capability checks.

This wraps the pure-Python capability registry so QML wizards can ask whether
the selected drone satisfies Solar, Seeding, or Mapping requirements.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QObject, Signal, Slot

from skymeshx.models.capabilities import (
    DroneCapabilities,
    check_mode_requirements,
    detect_capabilities,
)


class CapabilityContext(QObject):
    """Expose drone capabilities and mode requirement checks to QML."""

    capabilitiesChanged = Signal()
    logMessage = Signal(str, str, arguments=["level", "text"])

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swarm_context: Optional[Any] = None
        self._manual_overrides: dict[str, dict] = {}

    def set_swarm_context(self, swarm_context: Any) -> None:
        self._swarm_context = swarm_context
        self.capabilitiesChanged.emit()

    @Slot(str, result="QVariant")
    def checkModeRequirements(self, mode: str):
        drone_id = self._default_drone_id()
        caps = self._capabilities_for_drone(drone_id)
        result = check_mode_requirements(mode, caps)
        result["droneId"] = drone_id
        result["capabilities"] = caps.to_dict()
        return result

    @Slot(str, str, result="QVariant")
    def checkDroneModeRequirements(self, drone_id: str, mode: str):
        caps = self._capabilities_for_drone(drone_id)
        result = check_mode_requirements(mode, caps)
        result["droneId"] = drone_id
        result["capabilities"] = caps.to_dict()
        return result

    @Slot(str, result="QVariant")
    def getDroneCapabilities(self, drone_id: str):
        return self._capabilities_for_drone(drone_id).to_dict()

    @Slot(str, "QVariant", result=bool)
    def setManualOverrides(self, drone_id: str, overrides) -> bool:
        if not isinstance(overrides, dict):
            self.logMessage.emit("ERROR", "[CAPABILITIES] Overrides must be an object")
            return False
        self._manual_overrides[str(drone_id or "")] = dict(overrides)
        self.capabilitiesChanged.emit()
        return True

    @Slot(str)
    def clearManualOverrides(self, drone_id: str) -> None:
        self._manual_overrides.pop(str(drone_id or ""), None)
        self.capabilitiesChanged.emit()

    def _capabilities_for_drone(self, drone_id: str) -> DroneCapabilities:
        source = self._backend_for_drone(drone_id)
        overrides = self._manual_overrides.get(drone_id) or self._manual_overrides.get("")
        return detect_capabilities(source, overrides=overrides)

    def _backend_for_drone(self, drone_id: str):
        if self._swarm_context is None or not hasattr(self._swarm_context, "backend"):
            return None
        backend = self._swarm_context.backend
        if drone_id:
            return backend.get_backend(drone_id)
        for candidate in backend.all_backends().values():
            return candidate
        return None

    def _default_drone_id(self) -> str:
        if self._swarm_context is None or not hasattr(self._swarm_context, "backend"):
            return ""
        for drone_id in self._swarm_context.backend.all_backends().keys():
            return drone_id
        return ""

