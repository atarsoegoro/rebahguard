"""Common edge pipeline for Edge 1 (HP Anak) and Edge 2 (HP Orang Tua).

Real Android sensor (default) -> 3-stage calibration-free feature extraction -> MQTT Broker.
Also subscribes to bidirectional alert topics (`alerts/child` or `alerts/parent`).
"""

import argparse
from collections.abc import Callable
import json
import uuid

from shared.messages import Telemetry
from shared.mqtt_connection import create_client, topic
from shared.processing import extract_features
from shared.sensors import SIMULATOR_SCENARIOS, select_source

AlertHandler = Callable[[dict], None]


def _parse_args(device_id: str, argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"RebahGuard {device_id}")
    parser.add_argument(
        "--source",
        choices=["android", "simulator"],
        default="android",
        help="Default: sensor fisik Android Termux. Gunakan simulator hanya untuk pengujian.",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SIMULATOR_SCENARIOS),
        default="duduk_sehat",
        help="Skenario saat menggunakan --source simulator.",
    )
    parser.add_argument("--interval", type=float, default=0.1, help="Interval antar sampel dalam detik (default 0.1s).")
    parser.add_argument("--samples", type=int, default=6, help="Jumlah sampel per window (default 6 sampel).")
    parser.add_argument(
        "--debug-sensors",
        action="store_true",
        help="Cetak nilai mentah accelerometer & gyroscope sebelum ekstraksi fitur.",
    )
    args = parser.parse_args(argv)
    if args.interval <= 0 or args.samples < 2:
        parser.error("--interval harus positif dan --samples >= 2")
    return args


def run_edge(
    device_id: str,
    on_alert: AlertHandler | None = None,
    alert_topic_suffix: str | None = None,
    argv: list[str] | None = None,
) -> None:
    args = _parse_args(device_id, argv=argv)
    label = device_id.upper()
    source = select_source(args.source, args.scenario)
    client = create_client(device_id)

    if alert_topic_suffix is None:
        alert_topic_suffix = "alerts/child" if device_id == "edge1" else "alerts/parent"
    sub_topic = topic(alert_topic_suffix)

    if on_alert is not None:
        def on_connect(client, userdata, flags, reason_code, properties):
            if getattr(reason_code, "is_failure", False):
                print(f"[{label}] Koneksi MQTT ditolak: {reason_code}")
                return
            client.subscribe(sub_topic, qos=1)
            print(f"[{label}] Subscribed ke {sub_topic}")

        def on_message(client, userdata, message):
            try:
                alert = json.loads(message.payload)
                if not isinstance(alert, dict):
                    raise ValueError("Alert harus berupa JSON object")
            except ValueError:
                print(f"[{label}] Mengabaikan payload alert yang tidak valid")
                return
            on_alert(alert)

        client.on_connect = on_connect
        client.on_message = on_message

    client.loop_start()
    boot_id = uuid.uuid4().hex
    sequence = 0
    telemetry_topic = topic(f"edge/{device_id}/telemetry")
    delay_ms = max(20, int(args.interval * 1000))

    print(f"[{label}] Source: {args.source}" + (f" ({args.scenario})" if args.source == "simulator" else ""))
    print(f"[{label}] Publish telemetry ke: {telemetry_topic}")

    try:
        while True:
            samples = source.read_window(samples_count=args.samples, delay_ms=delay_ms)
            if args.debug_sensors:
                for s in samples:
                    print(
                        f"[{label} | RAW] accel={s.acceleration} m/s² gyro={s.gyroscope} rad/s",
                        flush=True,
                    )
            features = extract_features(samples)
            telemetry = Telemetry.make(
                device_id=device_id,
                boot_id=boot_id,
                sequence=sequence,
                overhead_deg=features.overhead_deg,
                roll_deg=features.roll_deg,
                motion_rms=features.motion_rms,
                gyro_rms=features.gyro_rms,
            )
            info = client.publish(telemetry_topic, telemetry.to_json(), qos=1, retain=False)
            info.wait_for_publish(timeout=10)
            print(
                f"[{label}] #{sequence} "
                f"overhead={features.overhead_deg:.1f}°, roll={features.roll_deg:.1f}°, "
                f"motion_rms={features.motion_rms:.4f} m/s², gyro_rms={features.gyro_rms:.4f} rad/s",
                flush=True,
            )
            sequence += 1
    except KeyboardInterrupt:
        print(f"[{label}] Dihentikan")
    finally:
        if hasattr(source, "close"):
            source.close()
        client.loop_stop()
        client.disconnect()
