# Keamanan Siber & Ketahanan Sistem RebahGuard

**Lakukan eksperimen pengujian keamanan hanya pada broker dan namespace topic milik kelompok Anda sendiri.**

## 1. Lapisan Proteksi pada RebahGuard

| Ancaman / Risiko | Mekanisme Pertahanan di RebahGuard | Lokasi Implementasi |
|---|---|---|
| **Penyadapan jalur komunikasi** | MQTT over TLS (port `8883`) dan WebSocket Secure (`wss://` port `8884`) | `shared/mqtt_connection.py` |
| **Kebocoran kredensial broker ke browser** | Endpoint `/config.json` lokal hanya mengirimkan `project_id` dan `websocket_url` tanpa `MQTT_PASSWORD` | `shared/dashboard_server.py` |
| **Serangan Replay (*Replay Attack*)** | Validasi monotonik `sequence > last_seq[(device_id, boot_id)]` -> menolak dengan `REJECTED_REPLAY` | `nodes/posture_service/rules.py` |
| **Paket Kadaluarsa (*Stale Packet Injection*)** | Validasi `abs(now_ms - sent_at_ms) <= stale_message_ms` ($30\text{ detik}$) -> menolak dengan `REJECTED_STALE` | `nodes/posture_service/rules.py` |
| **Injeksi Payload Rusak / NaN / Infinity** | Validasi skema ketat di `from_json()` dan `to_json(allow_nan=False)` untuk `Telemetry`, `AlertMessage`, `StatusMessage`, dan `ControlCommand` | `shared/messages.py` |
| **Ghost Vibration saat Reconnect** | Seluruh pesan di `alerts/parent` dan `alerts/child` dipublish dengan `retain=False`, sedangkan `status` dan `config` menggunakan `retain=True` | `nodes/posture_service/main.py` |
| **False Scold saat HP Ortu di Saku** | *Shake-to-Scold* mewajibkan `shake_confirm_windows = 2` window goyangan berturut-turut dan hanya aktif saat `edge1` sedang dalam postur rebahan | `nodes/posture_service/rules.py` |

## 2. Lab A: Pengujian Anti-Replay (`scripts/replay_test.py`)

Jalankan `python server.py` di satu terminal, lalu jalankan skrip pengujian replay di terminal lain:

```bash
python -m scripts.replay_test
```

Skrip ini mengirimkan dua paket `Telemetry` dengan `boot_id` dan `sequence` yang sama persis ke `rebahguard/<PROJECT_ID>/edge/edge1/telemetry`. Paket pertama diproses normal, sedangkan paket kedua langsung ditolak dengan status **`REJECTED_REPLAY`**.

## 3. Lab B: Daftar Access Control List (ACL) untuk Broker Privat

Jika menggunakan broker privat (seperti HiveMQ Cloud atau EMQX Cloud), terapkan prinsip *least privilege* pada setiap akun perangkat:

```text
edge1     publish    rebahguard/<PROJECT_ID>/edge/edge1/telemetry
edge1     subscribe  rebahguard/<PROJECT_ID>/alerts/child
edge2     publish    rebahguard/<PROJECT_ID>/edge/edge2/telemetry
edge2     subscribe  rebahguard/<PROJECT_ID>/alerts/parent
posture   subscribe  rebahguard/<PROJECT_ID>/edge/+/telemetry
posture   subscribe  rebahguard/<PROJECT_ID>/control
posture   publish    rebahguard/<PROJECT_ID>/status
posture   publish    rebahguard/<PROJECT_ID>/config
posture   publish    rebahguard/<PROJECT_ID>/alerts/parent
posture   publish    rebahguard/<PROJECT_ID>/alerts/child
dashboard subscribe  rebahguard/<PROJECT_ID>/edge/+/telemetry
dashboard subscribe  rebahguard/<PROJECT_ID>/status
dashboard subscribe  rebahguard/<PROJECT_ID>/config
dashboard subscribe  rebahguard/<PROJECT_ID>/alerts/+
dashboard publish    rebahguard/<PROJECT_ID>/control
```
