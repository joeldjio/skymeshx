from __future__ import annotations

from tools.ui.context.capability_context import CapabilityContext


class FakeBackend:
    drone_type = "observation"

    def __init__(self, drone_type="observation", **status):
        self.drone_type = drone_type
        self._status = {"droneType": drone_type}
        self._status.update(status)

    def get_telemetry_snapshot(self):
        return dict(self._status)


class FakeSwarmBackend:
    def __init__(self, backends):
        self._backends = dict(backends)

    def get_backend(self, drone_id):
        return self._backends.get(drone_id)

    def all_backends(self):
        return dict(self._backends)


class FakeSwarmContext:
    def __init__(self, backends):
        self.backend = FakeSwarmBackend(backends)


def test_capability_context_default_check_uses_first_drone(qapp):
    ctx = CapabilityContext()
    ctx.set_swarm_context(FakeSwarmContext({
        "CAM1": FakeBackend("observation", hasThermalCamera=False),
    }))

    result = ctx.checkModeRequirements("solar")

    assert result["droneId"] == "CAM1"
    assert result["satisfied"] is True
    assert result["capabilities"]["hasCamera"] is True
    assert any("Thermal camera" in warning for warning in result["warnings"])


def test_capability_context_solar_qml_nested_capabilities_shape(qapp):
    ctx = CapabilityContext()
    ctx.set_swarm_context(FakeSwarmContext({
        "THERMAL1": FakeBackend(
            "observation",
            hasCamera=True,
            hasGimbal=True,
            hasThermalCamera=True,
        ),
    }))

    result = ctx.checkModeRequirements("solar")

    assert isinstance(result["capabilities"], dict)
    assert result["capabilities"]["hasThermalCamera"] is True
    assert result["capabilities"]["hasCamera"] is True
    assert result["capabilities"]["hasGimbal"] is True


def test_capability_context_explicit_drone_check(qapp):
    ctx = CapabilityContext()
    ctx.set_swarm_context(FakeSwarmContext({
        "GENERIC": FakeBackend("generic", hasDispenser=False),
        "SEEDER": FakeBackend("generic", hasDispenser=True, dispenserType="servo"),
    }))

    result = ctx.checkDroneModeRequirements("SEEDER", "seeding")

    assert result["droneId"] == "SEEDER"
    assert result["satisfied"] is True
    assert result["capabilities"]["hasDispenser"] is True
    assert result["capabilities"]["dispenserType"] == "servo"


def test_capability_context_get_drone_capabilities(qapp):
    ctx = CapabilityContext()
    ctx.set_swarm_context(FakeSwarmContext({
        "MAP1": FakeBackend("observation", cameraResolution="3840x2160"),
    }))

    caps = ctx.getDroneCapabilities("MAP1")

    assert caps["hasCamera"] is True
    assert caps["cameraResolution"] == "3840x2160"


def test_capability_context_manual_overrides(qapp):
    ctx = CapabilityContext()
    ctx.set_swarm_context(FakeSwarmContext({
        "GENERIC": FakeBackend("generic", hasCamera=False),
    }))

    assert ctx.setManualOverrides("GENERIC", {"hasCamera": True, "hasGimbal": True}) is True
    result = ctx.checkDroneModeRequirements("GENERIC", "solar")
    assert result["satisfied"] is True

    ctx.clearManualOverrides("GENERIC")
    result = ctx.checkDroneModeRequirements("GENERIC", "solar")
    assert result["satisfied"] is False


def test_capability_context_rejects_invalid_overrides(qapp):
    ctx = CapabilityContext()

    assert ctx.setManualOverrides("D1", ["bad"]) is False


def test_service_locator_registers_capabilities_context(qapp):
    from tools.ui.service_locator import build_default_locator

    locator = build_default_locator()
    locator.eager_init()

    assert locator.has("capabilities")
    assert isinstance(locator["capabilities"], CapabilityContext)
