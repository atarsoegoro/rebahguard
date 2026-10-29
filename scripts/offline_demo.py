"""Demonstrasi offline berurutan FSM RebahGuard tanpa koneksi MQTT/internet.

Menjalankan 6 tahap skenario secara berurutan:
  1. duduk_sehat     -> POSISI_DUDUK_SEHAT
  2. landscape_game  -> POSISI_DUDUK_SEHAT (bebas false positive karena use_roll=False)
  3. telungkup_meja  -> DITARUH_TELUNGKUP (aman di meja, motion_rms=0 bebas bias kalibrasi)
  4. rebahan_main    -> REBAHAN_AKTIF hingga melewati lying_limit_sec menjadi ALERT_MATA
  5. ortu_shake      -> 2 window berturut-turut di Edge 2 memicu TEGURAN_ORTU
  6. duduk_sehat     -> Kembali duduk sehat, mematikan nagging dan memicu event CLEAR ke HP Anak
"""

from nodes.posture_service.rules import RebahDetector
from shared.messages import Telemetry
from shared.processing import extract_features
from shared.sensors import Simulator

BASE_TIME_MS = 1_790_000_000_000


def build_sim_telemetry(
    device_id: str,
    scenario: str,
    sequence: int,
    sent_at_ms: int,
    seed: int = 42,
) -> Telemetry:
    sim = Simulator(scenario=scenario, seed=seed + sequence)
    samples = [sim.read() for _ in range(6)]
    feat = extract_features(samples)
    return Telemetry(
        device_id=device_id,
        boot_id="offline-demo",
        sequence=sequence,
        sent_at_ms=sent_at_ms,
        overhead_deg=feat.overhead_deg,
        roll_deg=feat.roll_deg,
        motion_rms=feat.motion_rms,
        gyro_rms=feat.gyro_rms,
    )


def main() -> None:
    detector = RebahDetector()
    now_ms = BASE_TIME_MS
    e1_seq = 0
    e2_seq = 0

    print("=== REBAHGUARD OFFLINE FSM & MULTISENSOR DEMO ===\n")

    # 1. Duduk sehat
    t = build_sim_telemetry("edge1", "duduk_sehat", e1_seq, now_ms)
    e1_seq += 1
    d = detector.accept(t, now_ms=now_ms)
    print(f"1. [duduk_sehat] overhead={t.overhead_deg:.1f}°, roll={t.roll_deg:.1f}°")
    print(f"   -> Status: {d.status} | Reason: {d.reason}\n")

    # 2. Duduk main game landscape (tetap sehat!)
    now_ms += 2000
    t = build_sim_telemetry("edge1", "landscape_game", e1_seq, now_ms)
    e1_seq += 1
    d = detector.accept(t, now_ms=now_ms)
    print(f"2. [landscape_game] overhead={t.overhead_deg:.1f}°, roll={t.roll_deg:.1f}° (use_roll={detector.config.use_roll})")
    print(f"   -> Status: {d.status} | Reason: {d.reason}\n")

    # 3. HP ditaruh telungkup di meja
    now_ms += 2000
    t = build_sim_telemetry("edge1", "telungkup_meja", e1_seq, now_ms)
    e1_seq += 1
    d = detector.accept(t, now_ms=now_ms)
    print(f"3. [telungkup_meja] overhead={t.overhead_deg:.1f}°, motion_rms={t.motion_rms:.4f} m/s²")
    print(f"   -> Status: {d.status} | Reason: {d.reason}\n")

    # 4. Rebahan main HP hingga melewati lying_limit_sec (10.0s) -> ALERT_MATA
    print("4. [rebahan_main] Anak mulai main HP sambil rebahan telentang:")
    for step in range(5):
        now_ms += 2500
        t = build_sim_telemetry("edge1", "rebahan_main", e1_seq, now_ms)
        e1_seq += 1
        d = detector.accept(t, now_ms=now_ms)
        alert_info = ""
        if d.parent_alert or d.child_alert:
            alert_info = f" | Alerts: parent={d.parent_alert.event if d.parent_alert else None}, child={d.child_alert.event if d.child_alert else None}"
        print(
            f"   Window #{step + 1} (elapsed={detector.lying_elapsed_sec:.1f}s): "
            f"{d.status} — {d.reason}{alert_info}"
        )
    print()

    # 5. Ortu menggoyangkan HP 2 window berturut-turut -> TEGURAN_ORTU
    print("5. [ortu_shake] Orang tua menggoyangkan HP (Edge 2) 2 window berturut-turut:")
    for w in (1, 2):
        now_ms += 1000
        t2 = build_sim_telemetry("edge2", "ortu_shake", e2_seq, now_ms)
        e2_seq += 1
        d = detector.accept(t2, now_ms=now_ms)
        child_ev = d.child_alert.event if d.child_alert else None
        print(
            f"   Shake Window #{w} (motion_rms={t2.motion_rms:.2f} m/s²): "
            f"Status={d.status} | nagging_active={detector.nagging_active} | child_alert={child_ev}"
        )
    print()

    # 6. Anak kembali duduk sehat -> mematikan nagging & mengirim CLEAR
    now_ms += 2000
    t = build_sim_telemetry("edge1", "duduk_sehat", e1_seq, now_ms)
    e1_seq += 1
    d = detector.accept(t, now_ms=now_ms)
    clear_ev = d.child_alert.event if d.child_alert else None
    print(f"6. [duduk_sehat] Anak kembali duduk tegak:")
    print(
        f"   -> Status: {d.status} | nagging_active={detector.nagging_active} "
        f"| child_alert={clear_ev} ({d.reason})\n"
    )
    print("Offline demo selesai dengan sukses. Jalankan `python server.py` untuk mode MQTT penuh.")


if __name__ == "__main__":
    main()
