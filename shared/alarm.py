"""OUTPUT / ACTUATOR: handler aktuator getar & notifikasi untuk HP Anak (Edge 1) dan HP Ortu (Edge 2).

Di Android (Termux + Termux:API), HP bergetar dan menampilkan/menghapus notifikasi sistem.
Di laptop/non-Termux, kode tetap berjalan aman dan mencetak log ke terminal.
"""

import shutil
import subprocess
from typing import Any


def _run_quietly(command: list[str]) -> None:
    try:
        subprocess.run(command, capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[ALARM] Gagal menjalankan {command[0]}: {exc}")


def handle_parent_alert(alert: dict[str, Any]) -> None:
    """Handler aktuator untuk Edge 2 (HP Orang Tua) saat menerima alert dari topic alerts/parent."""
    event = str(alert.get("event", "ALERT_MATA"))
    reason = str(alert.get("reason", "Anak terdeteksi main HP sambil rebahan"))
    lying_sec = alert.get("lying_sec", 0.0)

    if event == "ALERT_MATA":
        print(
            f"\n[HP ORTU | ALERT_MATA] Anak rebahan {lying_sec}s! — {reason} "
            "(Goyangkan HP ini untuk mengirim TEGURAN_ORTU)\n",
            flush=True,
        )
        if shutil.which("termux-vibrate"):
            _run_quietly(["termux-vibrate", "-d", "1200"])
        if shutil.which("termux-notification"):
            _run_quietly(
                [
                    "termux-notification",
                    "--id",
                    "rebahguard-parent",
                    "--title",
                    "RebahGuard: Anak Rebahan!",
                    "--content",
                    f"Durasi {lying_sec}s. {reason}. Goyangkan HP untuk menegur!",
                    "--priority",
                    "high",
                    "--sound",
                ]
            )
    elif event == "CLEAR":
        print(f"[HP ORTU | CLEAR] {reason}", flush=True)
        if shutil.which("termux-notification-remove"):
            _run_quietly(["termux-notification-remove", "rebahguard-parent"])


def handle_child_alert(alert: dict[str, Any]) -> None:
    """Handler aktuator untuk Edge 1 (HP Anak) saat menerima alert dari topic alerts/child."""
    event = str(alert.get("event", ""))
    reason = str(alert.get("reason", ""))
    lying_sec = alert.get("lying_sec", 0.0)

    if event == "CLEAR":
        print(f"\n[HP ANAK | CLEAR] Posisi sudah sehat / HP ditaruh: {reason}\n", flush=True)
        if shutil.which("termux-notification-remove"):
            _run_quietly(["termux-notification-remove", "rebahguard-child"])
        return

    if event == "TEGURAN_ORTU":
        print(
            f"\n[HP ANAK | TEGURAN_ORTU] RebahGuard: Segera duduk tegak! ({reason})\n",
            flush=True,
        )
        if shutil.which("termux-vibrate"):
            _run_quietly(["termux-vibrate", "-f", "-d", "1500"])
        if shutil.which("termux-notification"):
            _run_quietly(
                [
                    "termux-notification",
                    "--id",
                    "rebahguard-child",
                    "--title",
                    "RebahGuard: Segera duduk tegak!",
                    "--content",
                    f"Teguran Orang Tua! ({lying_sec}s) — {reason}",
                    "--priority",
                    "high",
                    "--sound",
                ]
            )
        return

    if event == "ALERT_MATA":
        print(
            f"\n[HP ANAK | ALERT_MATA] Peringatan postur rebahan ({lying_sec}s): {reason}\n",
            flush=True,
        )
        if shutil.which("termux-vibrate"):
            _run_quietly(["termux-vibrate", "-d", "600"])
        if shutil.which("termux-notification"):
            _run_quietly(
                [
                    "termux-notification",
                    "--id",
                    "rebahguard-child",
                    "--title",
                    "RebahGuard: Peringatan Mata & Postur",
                    "--content",
                    f"Kamu sudah rebahan {lying_sec}s. Duduk tegak atau taruh HP!",
                    "--priority",
                    "high",
                    "--sound",
                ]
            )


def ring_alarm(alert: dict[str, Any]) -> None:
    """Alias kompatibilitas untuk memicu alarm orang tua."""
    handle_parent_alert({"event": "ALERT_MATA", **alert})
