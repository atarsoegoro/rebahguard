# Fisika Sensor, 3 Tahap Pengolahan Sinyal, dan Algoritma FSM RebahGuard

## 1. Dua Sensor Fisik pada Setiap Edge

- **Accelerometer** mengukur resultan percepatan linier dan gravitasi bumi pada tiga sumbu $(a_x, a_y, a_z)$ dalam satuan $\text{m/s}^2$.
  - Saat HP dipegang duduk tegak menatap pengguna: $a_z > 0$ ($\text{overhead\_deg} < 90^\circ$).
  - Saat HP dipegang di atas wajah sambil rebahan telentang (atau diletakkan telungkup di meja): $a_z < 0$ ($\text{overhead\_deg} > 120^\circ$, hingga $180^\circ$ saat telungkup rata).
- **Gyroscope** mengukur kecepatan sudut rotasi $(g_x, g_y, g_z)$ dalam satuan $\text{rad/s}$.
  - Saat HP ditaruh di meja, giroskop mendekati $0.0000\text{ rad/s}$.
  - Saat HP dipegang tangan manusia (meskipun berusaha diam), terdapat *physiological hand tremor* dan aktivitas mikro jari ($\text{gyro\_rms} > 0.015\text{ rad/s}$).

---

## 2. Tiga Tahap Data Processing (`shared/processing.py`)

### Processing A: Gravity Orientation Smoothing (`overhead_deg` & `roll_deg`)
Untuk meredam getaran tangan sesaat sebelum menghitung sudut orientasi terhadap gravitasi, dihitung rata-rata vektor percepatan pada satu window:
$$\bar{a}_x = \frac{1}{N}\sum_{i=1}^N a_{x,i}, \quad \bar{a}_y = \frac{1}{N}\sum_{i=1}^N a_{y,i}, \quad \bar{a}_z = \frac{1}{N}\sum_{i=1}^N a_{z,i}$$
$$g_{\text{norm}} = \max\left(10^{-6}, \sqrt{\bar{a}_x^2 + \bar{a}_y^2 + \bar{a}_z^2}\right)$$
$$\text{overhead\_deg} = \text{degrees}\left(\arccos\left(\text{clamp}\left(\frac{\bar{a}_z}{g_{\text{norm}}}, -1.0, 1.0\right)\right)\right)$$
$$\text{roll\_deg} = \text{degrees}\left(\text{atan2}\left(|\bar{a}_x|, \sqrt{\bar{a}_y^2 + \bar{a}_z^2}\right)\right)$$

### Processing B: Mean-Centered Dynamic Motion RMS (Bebas Bias Kalibrasi $9.81\text{ m/s}^2$)
Mengapa **tidak boleh** menghitung $\sqrt{\frac{1}{N}\sum (m_i - 9.81)^2}$?
Karena sensor MEMS akselerometer pada smartphone komersial memiliki *zero-g offset* / bias kalibrasi statis sekitar $0.1\text{--}0.3\text{ m/s}^2$ (misalnya saat diam di meja membaca $a_z = -9.55\text{ m/s}^2$ konstan). Jika dikurangi $9.81$, HP yang diam di meja akan memiliki $\text{RMS} = 0.26\text{ m/s}^2 > 0.05\text{ m/s}^2$ dan gagal dikenali sebagai ditaruh di meja!

Oleh karena itu, RebahGuard menghitung simpangan terhadap **rata-rata magnitudo window itu sendiri ($\bar{m}$)**:
$$m_i = \sqrt{a_{x,i}^2 + a_{y,i}^2 + a_{z,i}^2}, \quad \bar{m} = \frac{1}{N}\sum_{i=1}^N m_i$$
$$\text{motion\_rms} = \sqrt{\frac{1}{N}\sum_{i=1}^N (m_i - \bar{m})^2}$$
Dengan rumus ini, bias kalibrasi statis saling menghilangkan sehingga HP yang diam di meja menghasilkan `motion_rms = 0.0000` secara presisi.

### Processing C: Gyroscope Micro-Activity RMS (`gyro_rms`)
$$\text{gyro\_rms} = \sqrt{\frac{1}{N}\sum_{i=1}^N (g_{x,i}^2 + g_{y,i}^2 + g_{z,i}^2)}$$

---

## 3. Keterbatasan Fisika Sensor Akselerometer: Landscape vs Tidur Miring (`use_roll`)

Secara fisika, akselerometer pada HP **hanya mengukur orientasi HP terhadap gravitasi bumi**, bukan orientasi kepala/tubuh pengguna:
- Saat pengguna **duduk tegak bermain game dalam orientasi *landscape***, sumbu $X$ HP mengarah vertikal sejajar gravitasi ($a_x \approx \pm 9.81\text{ m/s}^2, a_y \approx 0, a_z \approx 2.0\text{ m/s}^2$), menghasilkan $\text{roll\_deg} \approx 78^\circ$ meskipun pengguna duduk tegak.
- Saat pengguna **tidur miring (menyamping)** sambil memegang HP secara *portrait* sejajar wajahnya, vektor gravitasi pada kerangka HP juga jatuh pada sumbu $X$ ($\text{roll\_deg} \approx 75^\circ\text{--}85^\circ$).

Karena kedua kondisi fisik tersebut menghasilkan vektor gravitasi yang identik pada HP:
- Secara default, **`use_roll = False`** di [`shared/config.py`](../shared/config.py) agar posisi duduk bermain game/menonton video *landscape* (`overhead_deg < 90°`) **100% bebas dari *false positive***.
- Apabila pengguna hanya menggunakan HP dalam mode *portrait* dan ingin mendeteksi kebiasaan rebahan miring, fitur `use_roll` dapat diaktifkan secara live dari panel **Mode Kalibrasi & Live Tuning** di Dashboard (`use_roll = True`, `roll_enter_deg = 60°`, `roll_exit_deg = 45°`).

---

## 4. Histeresis Sudut & FSM (`nodes/posture_service/rules.py`)

Untuk mencegah status berkedip-kedip (*chattering*) saat sudut tangan berada di sekitar ambang batas:
- **Ambang Masuk Rebahan (`overhead_enter_deg`)**: $120.0^\circ$
- **Ambang Keluar Rebahan (`overhead_exit_deg`)**: $105.0^\circ$
- **Zona Abu-Abu ($105^\circ < \text{overhead\_deg} < 120^\circ$)**: Sistem mempertahankan nilai `in_lying_zone` sebelumnya.
- **Proteksi Paket Terlambat (`max_window_dt_sec = 3.0`)**: Penambahan waktu rebahan tiap paket dibatasi $\Delta t = \min(3.0, \max(0.0, t_{\text{now}} - t_{\text{prev}}))$ agar lonjakan latensi jaringan tidak langsung memicu `ALERT_MATA`.
