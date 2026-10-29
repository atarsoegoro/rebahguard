# Panduan Edge Fisik: Android + Termux (`hp_anak.py` & `hp_ortu.py`)

Jalankan **Edge 1 (`hp_anak.py`)** dan **Edge 2 (`hp_ortu.py`)** pada **dua smartphone Android fisik terpisah**.

## 1. Instalasi di Kedua HP Android

1. Pasang aplikasi **Termux** dan **Termux:API** dari F-Droid (pastikan keduanya berasal dari sumber distribusi yang sama), lalu berikan izin sensor & notifikasi.
2. Di dalam Termux, jalankan:

```bash
pkg update
pkg install python git termux-api
git clone https://github.com/myudak/contoh-project-iot1.git
cd contoh-project-iot1
python -m pip install -r requirements.txt
cp .env.example .env
termux-sensor -l
```

3. Samakan nilai `PROJECT_ID` di file `.env` pada kedua HP dan laptop.

## 2. Menjalankan Node Sesuai Peran

**Pada HP Anak (Edge 1):**
```bash
python hp_anak.py
```

**Pada HP Orang Tua (Edge 2):**
```bash
python hp_ortu.py
```

**Pada Laptop (Posture Service + Web Dashboard):**
```bash
python server.py
```

## 3. Optimasi Sensor & WakeLock di RebahGuard

- **Otomatis `termux-wake-lock`**: Saat `AndroidTermux` diinisialisasi di [`shared/sensors.py`](../shared/sensors.py), sistem otomatis memanggil `termux-wake-lock` agar pembacaan sensor tidak dimatikan oleh Android saat layar meredup, dan melepaskannya (`termux-wake-unlock`) saat program dihentikan.
- **Batch Window Acquisition (`read_window`)**: Mengambil sampel window sekaligus melalui `termux-sensor -s "<accel>,<gyro>" -d 100 -n 6` dengan parser stream multi-JSON (serta fallback otomatis ke `-n 1` bila versi Termux hanya mengeluarkan satu snapshot), sehingga bebas *bottleneck* pemanggilan proses berulang.

## 4. Aktuator Getar & Notifikasi Dua Arah (`shared/alarm.py`)

- **HP Orang Tua (`handle_parent_alert`)**:
  - Saat menerima `ALERT_MATA`, bergetar `1200 ms` (`termux-vibrate -d 1200`) dan menampilkan notifikasi sistem `--id rebahguard-parent`.
- **HP Anak (`handle_child_alert`)**:
  - Saat menerima `ALERT_MATA`, bergetar `600 ms` dan menampilkan peringatan postur `--id rebahguard-child`.
  - Saat menerima `TEGURAN_ORTU` (akibat *Shake-to-Scold* dari HP Ortu atau tombol `SCOLD` di Dashboard), bergetar kuat `termux-vibrate -f -d 1500` dengan notifikasi prioritas tinggi `"RebahGuard: Segera duduk tegak!"`.
  - Saat anak kembali duduk sehat atau menaruh HP telungkup di meja (`event == "CLEAR"`), sistem menjalankan `termux-notification-remove rebahguard-child` untuk menghapus notifikasi secara otomatis.

## 5. Diagnostik Sensor Tanpa MQTT

Untuk memastikan sensor fisik HP bekerja sebelum terhubung ke broker:

```bash
python -m scripts.check_sensors --readings 8
```

Untuk mencetak angka mentah akselerometer dan giroskop selama pengiriman MQTT berlangsung:

```bash
python hp_anak.py --debug-sensors
```
