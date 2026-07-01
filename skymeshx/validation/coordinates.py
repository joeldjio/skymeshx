"""
Coordinate and altitude validation utilities (UI-08).

Used by UI command slots, CLI, Pi API, MAVLink, and ROS2 paths
to reject obviously invalid values before they reach the flight stack.
"""
from __future__ import annotations

from typing import Tuple


class ValidationError(ValueError):
    """Raised when a coordinate or flight parameter fails validation."""


# ── Constants ──────────────────────────────────────────────────────────────────
_LAT_MIN: float = -90.0
_LAT_MAX: float = 90.0
_LON_MIN: float = -180.0
_LON_MAX: float = 180.0

# Reasonable operational limits — can be overridden per-call.
DEFAULT_MAX_ALTITUDE: float = 120.0   # metres AGL (regulatory default, e.g. EU/US)
DEFAULT_MAX_SPEED: float = 20.0       # m/s horizontal ground speed


# ── Public API ─────────────────────────────────────────────────────────────────

def validate_latitude(lat: float) -> float:
    """Return *lat* if valid, else raise :class:`ValidationError`.

    Args:
        lat: WGS-84 latitude in decimal degrees.

    Returns:
        The validated latitude unchanged.

    Raises:
        ValidationError: If *lat* is outside [-90, 90] or is not finite.
    """
    _check_finite(lat, "latitude")
    if not (_LAT_MIN <= lat <= _LAT_MAX):
        raise ValidationError(
            f"Latitude {lat!r} out of range [{_LAT_MIN}, {_LAT_MAX}]"
        )
    return lat


def validate_longitude(lon: float) -> float:
    """Return *lon* if valid, else raise :class:`ValidationError`.

    Args:
        lon: WGS-84 longitude in decimal degrees.

    Returns:
        The validated longitude unchanged.

    Raises:
        ValidationError: If *lon* is outside [-180, 180] or is not finite.
    """
    _check_finite(lon, "longitude")
    if not (_LON_MIN <= lon <= _LON_MAX):
        raise ValidationError(
            f"Longitude {lon!r} out of range [{_LON_MIN}, {_LON_MAX}]"
        )
    return lon


def validate_altitude(alt: float, max_alt: float = DEFAULT_MAX_ALTITUDE) -> float:
    """Return *alt* if valid, else raise :class:`ValidationError`.

    Args:
        alt:     Altitude in metres AGL (above ground level).
        max_alt: Maximum permitted altitude. Defaults to 120 m.

    Returns:
        The validated altitude unchanged.

    Raises:
        ValidationError: If *alt* is negative, exceeds *max_alt*, or is not finite.
    """
    _check_finite(alt, "altitude")
    if alt < 0:
        raise ValidationError(f"Altitude {alt!r} must not be negative")
    if alt > max_alt:
        raise ValidationError(
            f"Altitude {alt!r} m exceeds maximum {max_alt!r} m"
        )
    return alt


def validate_velocity(
    vel: Tuple[float, float, float],
    max_speed: float = DEFAULT_MAX_SPEED,
) -> Tuple[float, float, float]:
    """Return *vel* if all components are valid, else raise :class:`ValidationError`.

    Args:
        vel:       (vx, vy, vz) velocity components in m/s (NED frame).
        max_speed: Maximum absolute value for each component. Defaults to 20 m/s.

    Returns:
        The validated velocity tuple unchanged.

    Raises:
        ValidationError: If any component exceeds *max_speed* or is not finite.
    """
    if len(vel) != 3:
        raise ValidationError(f"Velocity must be a 3-tuple, got {len(vel)} elements")
    labels = ("vx", "vy", "vz")
    for v, label in zip(vel, labels):
        _check_finite(v, label)
        if abs(v) > max_speed:
            raise ValidationError(
                f"{label}={v!r} m/s exceeds maximum speed {max_speed!r} m/s"
            )
    return tuple(vel)  # type: ignore[return-value]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _check_finite(value: float, name: str) -> None:
    """Raise ValidationError if *value* is NaN or infinite."""
    import math
    if not math.isfinite(value):
        raise ValidationError(f"{name} must be a finite number, got {value!r}")
