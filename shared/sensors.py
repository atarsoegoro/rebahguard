"""Physical sensor acquisition (Android Termux:API) and realistic posture simulator.

'--source android' (DEFAULT) reads real physical accelerometer + gyroscope via Termux:API
with WakeLock and batch multi-sample JSON parsing.
'--source simulator' generates realistic synthetic sensor windows for testing.
"""

import atexit
import json
import math
import random
import shutil
import subprocess
import time
from typing import Any, Protocol

from shared.processing import SensorSample

SIMULATOR_SCENARIOS = (
    "duduk_sehat",
    "landscape_game",
    "telungkup_meja",
    "rebahan_main",
    "ortu_shake",
)


class SensorSource(Protocol):
    def read(self) -> SensorSample: ...
    def read_window(self, samples_count: int = 6, delay_ms: int = 100) -> list[SensorSample]: ...
    def close(self) -> None: ...


def parse_termux_sensor_stream(
    raw_output: str, accel_name: str, gyro_name: str, base_time: float | None = None, step_sec: float = 0.1
) -> list[SensorSample]:
    """Parse one or more JSON objects emitted by `termux-sensor -n N`."""
    decoder = json.JSONDecoder()
    idx = 0
    length = len(raw_output)
    objects: list[dict[str, Any]] = []

    while idx < length:
        while idx < length and raw_output[idx].isspace():
            idx += 1
        if idx >= length:
            break
        try:
            obj, next_idx = decoder.raw_decode(raw_output, idx)
            idx = next_idx
            if isinstance(obj, dict):
                objects.append(obj)
            elif isinstance(obj, list):
                objects.extend(item for item in obj if isinstance(item, dict))
        except json.JSONDecodeError:
            idx += 1

    now = base_time if base_time is not None else time.monotonic()
    samples: list[SensorSample] = []
    last_accel: tuple[float, float, float] | None = None
    last_gyro: tuple[float, float, float] | None = None

    for i, data in enumerate(objects):
        if accel_name in data and isinstance(data[accel_name], dict):
            vals = data[accel_name].get("values", [])
            if len(vals) >= 3:
                last_accel = (float(vals[0]), float(vals[1]), float(vals[2]))
        if gyro_name in data and isinstance(data[gyro_name], dict):
            vals = data[gyro_name].get("values", [])
            if len(vals) >= 3:
                last_gyro = (float(vals[0]), float(vals[1]), float(vals[2]))
        if last_accel is not None and last_gyro is not None:
            samples.append(SensorSample(now + i * step_sec, last_accel, last_gyro))

    return samples


class Simulator:
    def __init__(self, scenario: str = "duduk_sehat", seed: int = 42) -> None:
        if scenario not in SIMULATOR_SCENARIOS:
            raise ValueError(f"Unknown simulator scenario: {scenario}. Choose from {SIMULATOR_SCENARIOS}")
        self.scenario = scenario
        self.started = time.monotonic()
        self.random = random.Random(seed)
        self._step = 0

    def read(self) -> SensorSample:
        self._step += 1
        t = time.monotonic() - self.started
        n = lambda scale: self.random.gauss(0.0, scale)

        if self.scenario == "duduk_sehat":
            # Duduk tegak normal: az positif (~6.2), ay ~7.5 -> overhead_deg ~50 deg
            accel = (0.2 + n(0.08), 7.5 + n(0.08), 6.2 + n(0.12))
            gyro = (0.04 + n(0.02), 0.03 + n(0.02), n(0.01))
        elif self.scenario == "landscape_game":
            # Duduk main game landscape: ax ~9.81, ay ~0.0, az ~2.0 -> overhead_deg ~78 deg, roll ~78 deg
            accel = (9.81 + n(0.15), 0.1 + n(0.12), 2.0 + n(0.15))
            gyro = (0.08 + n(0.03), 0.06 + n(0.03), 0.05 + n(0.02))
        elif self.scenario == "telungkup_meja":
            # HP ditaruh telungkup diam di meja (dengan sedikit bias kalibrasi statis -9.58)
            accel = (0.0, 0.0, -9.58)
            gyro = (0.0, 0.0, 0.0)
        elif self.scenario == "rebahan_main":
            # Rebahan telentang: az negatif (~-8.5) -> overhead_deg ~150 deg + micro-movement tangan
            wave = 0.28 * math.sin(3.5 * (t + self._step * 0.1))
            accel = (0.3 + n(0.06), 4.6 + n(0.06), -8.5 + wave)
            gyro = (0.12 + n(0.03), 0.09 + n(0.03), 0.05 + n(0.02))
        elif self.scenario == "ortu_shake":
            # HP Orang Tua digoyangkan kuat (Shake-to-Scold)
            direction = 1.0 if (self._step % 2 == 0) else -1.0
            accel = (3.5 * direction + n(0.2), 2.0 * direction + n(0.2), 9.5 + 3.2 * direction)
            gyro = (2.1 * direction, 1.4 * direction, 0.8 * direction)
        else:
            accel = (0.0, 7.5, 6.2)
            gyro = (0.0, 0.0, 0.0)

        return SensorSample(time.monotonic(), accel, gyro)

    def read_window(self, samples_count: int = 6, delay_ms: int = 100) -> list[SensorSample]:
        count = max(2, samples_count)
        delay_sec = max(0.01, delay_ms / 1000.0)
        samples: list[SensorSample] = []
        for i in range(count):
            samples.append(self.read())
            if i < count - 1:
                time.sleep(delay_sec)
        return samples

    def close(self) -> None:
        pass


class AndroidTermux:
    def __init__(self) -> None:
        self._wake_locked = False
        if not shutil.which("termux-sensor"):
            raise RuntimeError("termux-sensor is missing. Install Termux:API and run: pkg install termux-api")

        self._acquire_wake_lock()
        atexit.register(self.close)

        names_output = subprocess.run(
            ["termux-sensor", "-l"], capture_output=True, text=True, timeout=10, check=True
        ).stdout
        names = json.loads(names_output)
        if isinstance(names, dict):
            names = names.get("sensors", [])
        if not isinstance(names, list):
            raise RuntimeError("Unexpected sensor listing. Run termux-sensor -l and inspect the result")

        self.accel_name = next(
            (
                name
                for name in names
                if ("accelerometer" in name.lower() or "acceleration sensor" in name.lower())
                and "uncalibrated" not in name.lower()
            ),
            None,
        )
        self.gyro_name = next(
            (
                name
                for name in names
                if "gyroscope" in name.lower() and "uncalibrated" not in name.lower()
            ),
            None,
        )
        if not self.accel_name or not self.gyro_name:
            raise RuntimeError(
                f"Accelerometer + gyroscope belum terdeteksi. Daftar: {names}. "
                "Pastikan kedua sensor ada di HP dan Termux:API terpasang."
            )
        print(f"[SENSOR] Accelerometer: {self.accel_name}")
        print(f"[SENSOR] Gyroscope: {self.gyro_name}")

    def _acquire_wake_lock(self) -> None:
        if shutil.which("termux-wake-lock"):
            try:
                subprocess.run(["termux-wake-lock"], capture_output=True, timeout=5, check=False)
                self._wake_locked = True
                print("[SENSOR] termux-wake-lock aktif (mencegah sensor mati saat layar redup)")
            except (OSError, subprocess.SubprocessError):
                pass

    def close(self) -> None:
        if self._wake_locked and shutil.which("termux-wake-unlock"):
            try:
                subprocess.run(["termux-wake-unlock"], capture_output=True, timeout=5, check=False)
                print("[SENSOR] termux-wake-unlock dilepaskan")
            except (OSError, subprocess.SubprocessError):
                pass
            finally:
                self._wake_locked = False

    def read(self) -> SensorSample:
        try:
            output = subprocess.run(
                [
                    "termux-sensor",
                    "-s",
                    f"{self.accel_name},{self.gyro_name}",
                    "-d",
                    "100",
                    "-n",
                    "1",
                ],
                capture_output=True,
                text=True,
                timeout=12,
                check=True,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(
                "Termux:API gagal membaca sensor. Uji: termux-sensor -l "
                "dan termux-sensor -a -d 100 -n 1; cek instalasi/izin Termux:API."
            ) from exc

        samples = parse_termux_sensor_stream(output, self.accel_name, self.gyro_name)
        if not samples:
            raise RuntimeError(f"Cannot read Termux sensor output: {output[:300]}")
        return samples[-1]

    def read_window(self, samples_count: int = 6, delay_ms: int = 100) -> list[SensorSample]:
        count = max(2, int(samples_count))
        delay = max(20, int(delay_ms))
        timeout_sec = max(12.0, (count * delay) / 1000.0 + 8.0)

        try:
            output = subprocess.run(
                [
                    "termux-sensor",
                    "-s",
                    f"{self.accel_name},{self.gyro_name}",
                    "-d",
                    str(delay),
                    "-n",
                    str(count),
                ],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=True,
            ).stdout
            samples = parse_termux_sensor_stream(
                output, self.accel_name, self.gyro_name, step_sec=delay / 1000.0
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            samples = []

        # Fallback ke pembacaan satu-per-satu (-n 1) jika versi Termux hanya mengeluarkan < 2 sampel
        while len(samples) < count:
            samples.append(self.read())
            if len(samples) < count:
                time.sleep(delay / 1000.0)

        return samples


def select_source(name: str, scenario: str = "duduk_sehat") -> SensorSource:
    if name == "android":
        return AndroidTermux()
    if name == "simulator":
        return Simulator(scenario)
    raise ValueError(f"Unknown sensor source: {name}")
