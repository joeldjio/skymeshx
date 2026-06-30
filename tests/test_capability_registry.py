from __future__ import annotations

import pytest

from skymeshx.models.capabilities import (
    DroneCapabilities,
    apply_manual_overrides,
    check_mode_requirements,
    detect_capabilities,
)


class FakeObservationBackend:
    def get_telemetry_snapshot(self):
        return {
            "droneType": "observation",
            "cameraResolution": "1920x1080",
            "cameraFov": [90.0, 60.0],
        }


def test_detect_capabilities_from_fake_observation_backend():
    caps = detect_capabilities(FakeObservationBackend())

    assert caps.has_camera is True
    assert caps.has_gimbal is True
    assert caps.has_live_stream is True
    assert caps.has_recording is True
    assert caps.camera_resolution == (1920, 1080)
    assert caps.camera_fov == (90.0, 60.0)
    assert caps.gimbal_axes == ["pitch", "yaw"]


def test_solar_inspection_requirements_satisfied_with_warning_for_no_thermal():
    caps = DroneCapabilities(
        has_camera=True,
        has_gimbal=True,
        has_thermal_camera=False,
        has_mission_upload=True,
        has_gps=True,
    )

    result = check_mode_requirements("solar_inspection", caps)

    assert result["satisfied"] is True
    assert result["missing"] == []
    assert any("Thermal camera" in warning for warning in result["warnings"])


def test_solar_inspection_missing_required_camera_and_gimbal():
    caps = DroneCapabilities(has_camera=False, has_gimbal=False)

    result = check_mode_requirements("solar", caps)

    assert result["satisfied"] is False
    assert any("Camera required" in item for item in result["missing"])
    assert any("Gimbal required" in item for item in result["missing"])


def test_seeding_requirements_need_dispenser_but_camera_is_optional_warning():
    caps = DroneCapabilities(
        has_dispenser=False,
        has_camera=False,
        has_mission_upload=True,
        has_gps=True,
    )

    result = check_mode_requirements("seeding", caps)

    assert result["satisfied"] is False
    assert any("Seed dispenser" in item for item in result["missing"])
    assert any("Camera not detected" in item for item in result["warnings"])


def test_seeding_requirements_satisfied_with_dispenser():
    caps = DroneCapabilities(has_dispenser=True, dispenser_type="servo")

    result = check_mode_requirements("seeding", caps)

    assert result["satisfied"] is True
    assert result["missing"] == []


def test_mapping_requirements_camera_required_gimbal_optional():
    caps = DroneCapabilities(has_camera=True, has_gimbal=False)

    result = check_mode_requirements("mapping", caps)

    assert result["satisfied"] is True
    assert result["missing"] == []
    assert any("Gimbal not detected" in warning for warning in result["warnings"])


def test_manual_capability_override_for_testing():
    caps = detect_capabilities(
        {"droneType": "generic", "hasCamera": False},
        overrides={"hasCamera": True, "hasDispenser": True, "dispenserType": "servo"},
    )

    assert caps.has_camera is True
    assert caps.has_dispenser is True
    assert caps.dispenser_type == "servo"
    assert caps.manual_overrides["has_camera"] is True


def test_capability_to_dict_is_qml_friendly():
    caps = DroneCapabilities(
        has_camera=True,
        camera_resolution=(3840, 2160),
        camera_fov=(84.0, 56.0),
        gimbal_axes=["pitch"],
    )

    data = caps.to_dict()

    assert data["hasCamera"] is True
    assert data["cameraResolution"] == "3840x2160"
    assert data["cameraFov"] == [84.0, 56.0]
    assert data["gimbalAxes"] == ["pitch"]


def test_unknown_mode_raises_value_error():
    with pytest.raises(ValueError):
        check_mode_requirements("unknown", DroneCapabilities())


def test_apply_manual_overrides_accepts_snake_and_camel_case():
    caps = DroneCapabilities()

    apply_manual_overrides(caps, {"hasCamera": True, "has_dispenser": True})

    assert caps.has_camera is True
    assert caps.has_dispenser is True

