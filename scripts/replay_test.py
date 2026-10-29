"""Lab keamanan siber terkontrol: uji proteksi anti-replay RebahGuard pada namespace milik sendiri.

Mengirim dua paket Telemetry identik (boot_id & sequence sama) ke topic `rebahguard/<PROJECT_ID>/edge/edge1/telemetry`.
Posture service akan menerima paket pertama dan menolak paket kedua dengan status `REJECTED_REPLAY`.
"""

import time

from shared.messages import Telemetry
from shared.mqtt_connection import create_client, topic


def main() -> None:
    client = create_client("replay-lab")
    client.loop_start()
    message = Telemetry.make(
        device_id="edge1",
        boot_id="replay-lab",
        sequence=100,
        overhead_deg=135.0,
        roll_deg=12.0,
        motion_rms=0.22,
        gyro_rms=0.11,
    ).to_json()
    target = topic("edge/edge1/telemetry")
    try:
        for attempt in (1, 2):
            result = client.publish(target, message, qos=1, retain=False)
            result.wait_for_publish(timeout=10)
            print(f"[LAB] Mengirim pesan Telemetry identik ke {target}, percobaan #{attempt}")
            time.sleep(1.0)
        print("[LAB] Posture service RebahGuard wajib menandai pesan kedua sebagai REJECTED_REPLAY.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
