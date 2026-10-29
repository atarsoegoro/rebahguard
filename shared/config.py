"""Centralized configuration for RebahGuard posture & interaction detection."""

from dataclasses import asdict, dataclass, fields
import math
from typing import Any


@dataclass(frozen=True)
class DetectorConfig:
    overhead_enter_deg: float = 120.0
    overhead_exit_deg: float = 105.0
    face_down_deg: float = 145.0
    still_motion_max: float = 0.05
    still_gyro_max: float = 0.015
    use_roll: bool = False
    roll_enter_deg: float = 60.0
    roll_exit_deg: float = 45.0
    lying_limit_sec: float = 10.0
    max_window_dt_sec: float = 3.0
    shake_motion_min: float = 2.0
    shake_gyro_min: float = 1.6
    shake_confirm_windows: int = 2
    shake_cooldown_sec: float = 5.0
    alert_cooldown_sec: float = 8.0
    nag_interval_sec: float = 2.5
    edge_timeout_sec: float = 8.0
    stale_message_ms: int = 30_000
    snooze_duration_sec: float = 30.0

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if type(self.use_roll) is not bool:
            raise ValueError("use_roll must be a boolean")

        int_fields = ("shake_confirm_windows", "stale_message_ms")
        for name in int_fields:
            val = getattr(self, name)
            if type(val) is not int or val <= 0:
                raise ValueError(f"{name} must be a positive integer")

        float_fields = (
            "overhead_enter_deg",
            "overhead_exit_deg",
            "face_down_deg",
            "still_motion_max",
            "still_gyro_max",
            "roll_enter_deg",
            "roll_exit_deg",
            "lying_limit_sec",
            "max_window_dt_sec",
            "shake_motion_min",
            "shake_gyro_min",
            "shake_cooldown_sec",
            "alert_cooldown_sec",
            "nag_interval_sec",
            "edge_timeout_sec",
            "snooze_duration_sec",
        )
        for name in float_fields:
            val = getattr(self, name)
            if type(val) not in (int, float) or not math.isfinite(val) or val <= 0:
                raise ValueError(f"{name} must be a positive finite number")
            object.__setattr__(self, name, float(val))

        for deg_field in ("overhead_enter_deg", "overhead_exit_deg", "face_down_deg", "roll_enter_deg", "roll_exit_deg"):
            deg = getattr(self, deg_field)
            if deg > 180.0:
                raise ValueError(f"{deg_field} must be <= 180.0")

        if self.overhead_exit_deg >= self.overhead_enter_deg:
            raise ValueError("overhead_exit_deg must be strictly less than overhead_enter_deg")

        if self.roll_exit_deg >= self.roll_enter_deg:
            raise ValueError("roll_exit_deg must be strictly less than roll_enter_deg")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectorConfig":
        if not isinstance(data, dict):
            raise ValueError("Config data must be a dictionary")
        return cls().merged_with(data)

    def merged_with(self, partial_dict: dict[str, Any]) -> "DetectorConfig":
        if not isinstance(partial_dict, dict):
            raise ValueError("partial_dict must be a dictionary")
        valid_keys = {f.name for f in fields(self)}
        unknown = set(partial_dict.keys()) - valid_keys
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")

        merged = self.to_dict()
        for key, value in partial_dict.items():
            if key in ("shake_confirm_windows", "stale_message_ms"):
                if type(value) is float and value.is_integer():
                    value = int(value)
            merged[key] = value
        return DetectorConfig(**merged)

