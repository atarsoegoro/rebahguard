"""NODE 3 — Laptop: MQTT Posture Service + Web Dashboard Lokal RebahGuard.

Run: python server.py
Open the printed http://localhost:8000 link on this laptop.
"""

from nodes.posture_service.main import main
from shared.dashboard_server import start_dashboard_server
from shared.mqtt_connection import project_id


def run() -> None:
    try:
        server, thread, url = start_dashboard_server()
    except OSError as exc:
        raise SystemExit(
            f"[DASHBOARD] Gagal membuka localhost:8000: {exc}. "
            "Tutup aplikasi lain di port ini atau set DASHBOARD_PORT di .env."
        ) from exc

    print("\nRebahGuard — NODE 3 / Posture Service & Dashboard", flush=True)
    print(f"[DASHBOARD] Buka di laptop: {url}", flush=True)
    print(f"[CONFIG] PROJECT_ID: {project_id()}", flush=True)
    print("[POSTURE] Menunggu Edge 1 (HP Anak) dan Edge 2 (HP Orang Tua) dari MQTT Broker...\n", flush=True)
    try:
        main()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    run()

