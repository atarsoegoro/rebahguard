"""DATA PROCESSING (used by BOTH edge devices).

Processing A: Gravity Orientation Smoothing (overhead_deg & roll_deg).
Processing B: Mean-Centered Dynamic Motion RMS (calibration-bias-free motion_rms).
Processing C: Gyroscope Micro-Activity RMS (gyro_rms).
"""

from dataclasses import dataclass
from math import acos, atan2, degrees, sqrt


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class SensorSample:
    seconds: float
    acceleration: tuple[float, float, float]
    gyroscope: tuple[float, float, float]


@dataclass(frozen=True)
class Features:
    overhead_deg: float
    roll_deg: float
    motion_rms: float
    gyro_rms: float
    raw_accel_mean: tuple[float, float, float] = (0.0, 0.0, 0.0)
    raw_gyro_last: tuple[float, float, float] = (0.0, 0.0, 0.0)


def extract_features(samples: list[SensorSample]) -> Features:
    if len(samples) < 2:
        raise ValueError("At least 2 sensor samples are required")

    n = len(samples)

    # Processing A: Gravity Orientation Smoothing
    ax_mean = sum(s.acceleration[0] for s in samples) / n
    ay_mean = sum(s.acceleration[1] for s in samples) / n
    az_mean = sum(s.acceleration[2] for s in samples) / n

    g_norm = max(1e-6, sqrt(ax_mean * ax_mean + ay_mean * ay_mean + az_mean * az_mean))
    overhead_deg = degrees(acos(_clamp(az_mean / g_norm, -1.0, 1.0)))
    roll_deg = degrees(atan2(abs(ax_mean), sqrt(ay_mean * ay_mean + az_mean * az_mean)))

    # Processing B: Mean-Centered Dynamic Motion RMS (bebas bias kalibrasi statis 9.81)
    magnitudes = [
        sqrt(s.acceleration[0] ** 2 + s.acceleration[1] ** 2 + s.acceleration[2] ** 2)
        for s in samples
    ]
    mean_mag = sum(magnitudes) / n
    motion_rms = sqrt(sum((m - mean_mag) ** 2 for m in magnitudes) / n)

    # Processing C: Gyroscope Micro-Activity RMS
    gyro_sq_sum = sum(
        s.gyroscope[0] ** 2 + s.gyroscope[1] ** 2 + s.gyroscope[2] ** 2
        for s in samples
    )
    gyro_rms = sqrt(gyro_sq_sum / n)

    last_gx, last_gy, last_gz = samples[-1].gyroscope

    return Features(
        overhead_deg=round(overhead_deg, 4),
        roll_deg=round(roll_deg, 4),
        motion_rms=round(motion_rms, 4),
        gyro_rms=round(gyro_rms, 4),
        raw_accel_mean=(round(ax_mean, 4), round(ay_mean, 4), round(az_mean, 4)),
        raw_gyro_last=(round(last_gx, 4), round(last_gy, 4), round(last_gz, 4)),
    )
