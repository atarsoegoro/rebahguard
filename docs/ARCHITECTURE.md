# Arsitektur Sistem IoT RebahGuard

Sistem **RebahGuard** terdiri dari **tiga node utama** yang berjalan pada **tiga perangkat fisik terpisah**: dua smartphone sebagai *edge node* (sensor + aktuator dua arah) dan satu laptop sebagai *posture service* sekaligus pelayan *web dashboard* lokal.

```mermaid
flowchart TB
    subgraph LAN["Lingkungan Pengguna (Wi-Fi / Hotspot / Seluler)"]
        subgraph E1["NODE 1 — Edge 1 (HP Anak)"]
            A1["Accelerometer + Gyroscope"] --> P1["3-Stage Feature Extraction:<br/>overhead_deg, roll_deg,<br/>motion_rms, gyro_rms"]
            ACT1["Aktuator Anak:<br/>Getar / Nada & Clear Banner"]
        end
        subgraph E2["NODE 2 — Edge 2 (HP Orang Tua)"]
            A2["Accelerometer + Gyroscope"] --> P2["3-Stage Feature Extraction:<br/>Deteksi Shake-to-Scold"]
            ACT2["Aktuator Orang Tua:<br/>Getar & Notifikasi Alert"]
        end
        subgraph LAPTOP["NODE 3 — Laptop Server"]
            D["Posture Service (RebahDetector FSM)"]
            UI["Dashboard & Live Tuning<br/>http://localhost:8000"]
        end
    end
    P1 -->|"Publish edge/edge1/telemetry (QoS 1)"| MQTT["MQTT Broker (TLS 8883 / WSS 8884)"]
    P2 -->|"Publish edge/edge2/telemetry (QoS 1)"| MQTT
    MQTT -->|"Subscribe edge/+/telemetry"| D
    D -->|"Publish alerts/child (QoS 1, retain=False)"| MQTT
    D -->|"Publish alerts/parent (QoS 1, retain=False)"| MQTT
    D -->|"Publish status & config (QoS 1, retain=True)"| MQTT
    MQTT -->|"Deliver ALERT_MATA / TEGURAN_ORTU / CLEAR"| ACT1
    MQTT -->|"Deliver ALERT_MATA"| ACT2
    MQTT <-->|"WSS Telemetry, Status, Config & Control"| UI
```

## Peran Setiap Node

| Node | Perangkat | Input Sensor | Pemrosesan Lokal | Output & Aktuasi |
|---|---|---|---|---|
| **Edge 1 (`hp_anak.py` / `web-edge`)** | Smartphone Anak | Accelerometer + Gyroscope | Orientasi gravitasi (`overhead_deg`, `roll_deg`), *mean-centered* `motion_rms`, `gyro_rms` | Publish `edge/edge1/telemetry`; terima `alerts/child` (`ALERT_MATA`, `TEGURAN_ORTU`, `CLEAR`) |
| **Edge 2 (`hp_ortu.py` / `web-edge`)** | Smartphone Orang Tua | Accelerometer + Gyroscope | Ekstraksi `motion_rms` & `gyro_rms` untuk fitur *Shake-to-Scold* | Publish `edge/edge2/telemetry`; terima `alerts/parent` (`ALERT_MATA`) |
| **Posture Service (`server.py`)** | Laptop | Telemetry dari kedua edge & perintah `control` | FSM `RebahDetector` berhisteresis, anti-stale, anti-replay, *shake confirmation* | Publish `status` (retained), `config` (retained), `alerts/parent` & `alerts/child` (non-retained) |
| **Dashboard (`dashboard/index.html`)** | Browser Laptop | `status`, `config`, `edge/+/telemetry`, `alerts/+` | Visualisasi real-time & validasi parameter kalibrasi | Grafik histeresis, tombol `SCOLD`/`SNOOZE`/`RESET`/`ARM`, & `UPDATE_CONFIG` live |

## Alur Komunikasi Dua Arah (Sequence Diagram)

```mermaid
sequenceDiagram
    participant E1 as Edge 1 (HP Anak)
    participant E2 as Edge 2 (HP Orang Tua)
    participant M as MQTT Broker
    participant S as Posture Service (Laptop)
    participant W as Web Dashboard

    S->>M: Publish config & status awal (retain=True)
    E1->>M: Publish edge/edge1/telemetry (overhead_deg=135°, motion_rms=0.20)
    M->>S: Teruskan telemetry Edge 1
    S->>S: Akumulasi durasi rebahan >= lying_limit_sec -> ALERT_MATA
    S->>M: Publish status (ALERT_MATA, retain=True)
    S->>M: Publish alerts/parent & alerts/child (ALERT_MATA, retain=False)
    M->>E2: Notifikasi & getar di HP Ortu
    M->>E1: Peringatan awal di HP Anak
    E2->>M: Publish edge/edge2/telemetry (2 window goyangan berturut-turut)
    M->>S: Teruskan telemetry Edge 2
    S->>S: Konfirmasi Shake-to-Scold -> TEGURAN_ORTU (nagging_active=True)
    S->>M: Publish alerts/child (TEGURAN_ORTU, retain=False)
    M->>E1: Getar kuat & nada peringatan berulang
    E1->>M: Publish edge/edge1/telemetry (overhead_deg=55° duduk tegak)
    M->>S: Teruskan telemetry Edge 1
    S->>S: Transisi ke POSISI_DUDUK_SEHAT (nagging_active=False)
    S->>M: Publish alerts/child (CLEAR, retain=False)
    M->>E1: Hentikan getar & bersihkan notifikasi
```
