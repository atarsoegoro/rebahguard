# Panduan Web Dashboard & Live Parameter Tuning (`http://localhost:8000`)

Dashboard lokal disajikan otomatis saat Anda menjalankan **`python server.py`** di laptop.

```bash
python -m pip install -r requirements.txt
python server.py
```

Buka **http://localhost:8000** di browser laptop. Server HTTP lokal hanya mengikat ke `127.0.0.1` dan menyediakan `/config.json` yang berisi `project_id` serta `websocket_url` tanpa membocorkan password broker dari `.env`.

## Fitur Utama Dashboard RebahGuard

1. **Badge Status FSM Semantik & Progress Bar Durasi Rebahan**:
   - Menampilkan status aktif (`POSISI_DUDUK_SEHAT`, `DITARUH_TELUNGKUP`, `REBAHAN_AKTIF`, `ALERT_MATA`, `TEGURAN_ORTU`, `SNOOZED`, `EDGE_OFFLINE`, `DISARMED`) dengan skema warna *Eye-Care* (otomatis mengikuti *light/dark mode*).
   - Menampilkan progress bar akumulasi waktu rebahan (`lying_elapsed_sec` / `lying_limit_sec`).
2. **Kartu Telemetry Edge 1 (HP Anak) & Edge 2 (HP Orang Tua)**:
   - Memantau indikator Online/Offline, `overhead_deg`, `roll_deg`, `motion_rms`, `gyro_rms`, nomor sequence, dan kesiapan *Shake-to-Scold*.
3. **Grafik Canvas Real-Time dengan Garis Histeresis Dinamis**:
   - Memplot 60 sampel terakhir `overhead_deg` dari HP Anak beserta **2 garis putus-putus histeresis** (`overhead_enter_deg` dan `overhead_exit_deg`) yang bergeser secara langsung saat konfigurasi diubah.
4. **Panel Kontrol 2 Arah Cepat**:
   - **TEGUR ANAK SEKARANG (`SCOLD`)**: Langsung mengaktifkan `TEGURAN_ORTU` dari dashboard.
   - **SNOOZE 30 DETIK (`SNOOZE`)**: Menunda deteksi sementara selama `snooze_duration_sec`.
   - **RESET STATE (`RESET`)**: Mengembalikan timer rebahan ke 0 dan membersihkan alert.
   - **ARM / DISARM**: Mengaktifkan atau menonaktifkan pemantauan.
5. **Mode Kalibrasi & Live Tuning Threshold (`UPDATE_CONFIG`)**:
   - Tersinkronisasi otomatis dengan pesan *retained* di topic `rebahguard/<PROJECT_ID>/config`.
   - Memungkinkan perubahan `overhead_enter_deg`, `overhead_exit_deg`, `face_down_deg`, `lying_limit_sec`, `still_motion_max`, `still_gyro_max`, `shake_motion_min`, `shake_gyro_min`, `shake_confirm_windows`, `alert_cooldown_sec`, `edge_timeout_sec`, serta `use_roll` + `roll_enter_deg` **secara live tanpa me-restart server maupun HP**.
