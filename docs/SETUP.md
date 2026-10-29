# Konfigurasi MQTT Broker & Skema Topik RebahGuard

## 1. Konfigurasi `.env`

Salin `.env.example` menjadi `.env`:

```env
PROJECT_ID=iot_kelompok_07
MQTT_HOST=broker.hivemq.com
MQTT_PORT=8883
MQTT_TLS=true
MQTT_WS_URL=wss://broker.hivemq.com:8884/mqtt
MQTT_USERNAME=
MQTT_PASSWORD=
DASHBOARD_PORT=8000
```

Pastikan **`PROJECT_ID` identik** di laptop (`server.py`), HP Anak (`hp_anak.py` / `web-edge`), dan HP Orang Tua (`hp_ortu.py` / `web-edge`).

## 2. Daftar Topik & Kebijakan Retain MQTT

Seluruh komunikasi menggunakan namespace **`rebahguard/<PROJECT_ID>/...`**:

| Topik MQTT | Publisher | Subscriber | QoS | Retain | Deskripsi Payload |
|---|---|---|---|---|---|
| `rebahguard/<PROJECT_ID>/edge/edge1/telemetry` | Edge 1 (HP Anak) | Posture Service, Dashboard | 1 | `False` | `Telemetry` JSON (`overhead_deg`, `roll_deg`, `motion_rms`, `gyro_rms`) |
| `rebahguard/<PROJECT_ID>/edge/edge2/telemetry` | Edge 2 (HP Ortu) | Posture Service, Dashboard | 1 | `False` | `Telemetry` JSON untuk deteksi *Shake-to-Scold* |
| `rebahguard/<PROJECT_ID>/status` | Posture Service | Dashboard | 1 | **`True`** | `StatusMessage` JSON (termasuk LWT `OFFLINE` saat service mati) |
| `rebahguard/<PROJECT_ID>/config` | Posture Service | Dashboard | 1 | **`True`** | `DetectorConfig` JSON agar form kalibrasi Dashboard selalu sinkron |
| `rebahguard/<PROJECT_ID>/alerts/parent` | Posture Service | Edge 2, Dashboard | 1 | **`False`** | `AlertMessage` JSON (`target="parent"`, `event="ALERT_MATA"`) |
| `rebahguard/<PROJECT_ID>/alerts/child` | Posture Service | Edge 1, Dashboard | 1 | **`False`** | `AlertMessage` JSON (`target="child"`, `event="ALERT_MATA" \| "TEGURAN_ORTU" \| "CLEAR"`) |
| `rebahguard/<PROJECT_ID>/control` | Dashboard / CLI | Posture Service | 1 | `False` | `ControlCommand` JSON (`ARM`, `DISARM`, `SCOLD`, `SNOOZE`, `RESET`, `UPDATE_CONFIG`) |

## 3. Pengiriman Perintah Kontrol via CLI (`scripts/send_control.py`)

Selain melalui tombol di Web Dashboard, Anda dapat mengirim perintah dari terminal:

```bash
python -m scripts.send_control SCOLD
python -m scripts.send_control SNOOZE
python -m scripts.send_control RESET
python -m scripts.send_control DISARM
python -m scripts.send_control ARM
python -m scripts.send_control --set-limit 5
```
