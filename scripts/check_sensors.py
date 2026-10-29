"""Diagnostik sensor fisik Android Termux untuk RebahGuard (tanpa butuh koneksi MQTT).

Jalankan di Termux Android:
    python -m scripts.check_sensors --readings 8
"""

import argparse
import math
import time

from shared.processing import extract_features
from shared.sensors import AndroidTermux


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnostik sensor gerak Android Termux untuk RebahGuard")
    parser.add_argument("--readings", type=int, default=8)
    args = parser.parse_args()
    if args.readings < 2:
        parser.error("--readings minimal 2")

    print("[CHECK] Memulai uji sensor Termux:API RebahGuard (tanpa MQTT)...", flush=True)
    source = AndroidTermux()
    samples = []
    try:
        for number in range(args.readings):
            reading = source.read()
            samples.append(reading)
            magnitude = math.sqrt(sum(axis * axis for axis in reading.acceleration))
            angular_speed = math.sqrt(sum(axis * axis for axis in reading.gyroscope))
            print(
                f"[CHECK] {number + 1}/{args.readings} "
                f"accel={tuple(round(v, 3) for v in reading.acceleration)} m/s² "
                f"| gyro={tuple(round(v, 3) for v in reading.gyroscope)} rad/s "
                f"| |a|={magnitude:.3f} | |g|={angular_speed:.3f}",
                flush=True,
            )
            if number < args.readings - 1:
                time.sleep(0.1)

        features = extract_features(samples)
        print(
            f"[PROCESSING] overhead_deg={features.overhead_deg:.2f}° | "
            f"roll_deg={features.roll_deg:.2f}° | "
            f"motion_rms={features.motion_rms:.4f} m/s² | "
            f"gyro_rms={features.gyro_rms:.4f} rad/s"
        )
        print("[CHECK] Jika nilai di atas berubah mengikuti kemiringan & gerakan HP, jalur sensor siap digunakan.")
    finally:
        source.close()


if __name__ == "__main__":
    main()
