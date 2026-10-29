"""CLI cepat untuk mengirim perintah kontrol RebahGuard ke topic `rebahguard/<PROJECT_ID>/control`.

Contoh penggunaan:
  python -m scripts.send_control SCOLD
  python -m scripts.send_control SNOOZE
  python -m scripts.send_control ARM
  python -m scripts.send_control DISARM
  python -m scripts.send_control RESET
  python -m scripts.send_control --set-limit 5
"""

import argparse

from shared.messages import ControlCommand
from shared.mqtt_connection import create_client, topic


def build_control_from_args(argv: list[str] | None = None) -> ControlCommand:
    parser = argparse.ArgumentParser(description="Kirim perintah kontrol RebahGuard via MQTT")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["ARM", "DISARM", "SCOLD", "SNOOZE", "RESET"],
        help="Perintah kontrol langsung (ARM, DISARM, SCOLD, SNOOZE, RESET)",
    )
    parser.add_argument(
        "--set-limit",
        type=float,
        dest="set_limit",
        help="Ubah lying_limit_sec secara live melalui UPDATE_CONFIG (contoh: --set-limit 5)",
    )
    args = parser.parse_args(argv)

    if args.set_limit is not None:
        return ControlCommand(command="UPDATE_CONFIG", params={"lying_limit_sec": args.set_limit})
    if args.command:
        return ControlCommand(command=args.command, params={})
    parser.error("Berikan perintah (ARM/DISARM/SCOLD/SNOOZE/RESET) atau gunakan --set-limit <detik>")


def main() -> None:
    cmd = build_control_from_args()
    client = create_client("control-cli")
    client.loop_start()
    try:
        info = client.publish(topic("control"), cmd.to_json(), qos=1, retain=False)
        info.wait_for_publish(timeout=10)
        print(f"[CONTROL] Terkirim ke {topic('control')}: {cmd.to_json()}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
