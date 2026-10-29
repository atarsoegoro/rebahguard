# Panduan Edge Browser HP Tanpa Termux (`web-edge/index.html`)

Halaman [`web-edge/index.html`](../web-edge/index.html) mengubah browser **Safari iPhone (iOS)** maupun **Chrome Android** menjadi perangkat edge fisik RebahGuard secara langsung menggunakan `DeviceMotionEvent`, `Web Audio API`, dan `Screen Wake Lock API`.

## 1. Persiapan Hosting HTTPS

Browser modern mewajibkan **HTTPS (Secure Context)** untuk mengizinkan akses sensor gerak (`DeviceMotionEvent`).
- Unggah folder `web-edge/` ke layanan hosting statis HTTPS seperti **Netlify Drop**, **Cloudflare Pages**, atau **GitHub Pages**.
- Buka tautan `https://...` tersebut di **HP Anak** dan **HP Orang Tua**.

## 2. Menjalankan Edge 1 & Edge 2 di Browser HP

1. **Pada HP Anak**:
   - Pilih peran **`Edge 1 — HP Anak (Deteksi Postur + Terima Teguran)`**.
   - Isi `PROJECT_ID` sama persis dengan laptop.
   - Jika menggunakan **Safari di iPhone/iPad**, pastikan kotak **"Invert Sumbu Z (Aktifkan khusus Safari iPhone/iOS)"** tercentang (terdeteksi otomatis). Safari iOS membalik tanda sumbu gravitasi `accelerationIncludingGravity` dibanding standar Android Chrome.
   - Tekan **Mulai membaca sensor** dan izinkan akses sensor gerak.
2. **Pada HP Orang Tua**:
   - Pilih peran **`Edge 2 — HP Orang Tua (Shake-to-Scold + Terima Alert)`**.
   - Isi `PROJECT_ID` yang sama, lalu tekan **Mulai membaca sensor**.

## 3. Kesetaraan Rumus & Praktik Mobile Browser

- **Rumus Identik 100% dengan Python**: Fungsi `extractFeatures()` di `web-edge/index.html` menghitung `overhead_deg`, `roll_deg`, *mean-centered* `motion_rms`, dan `gyro_rms` (dalam $\text{rad/s}$) setiap jendela `1200 ms` (minimal 5 sampel), lalu menampilkan keempat angka tersebut secara *live* di layar HP.
- **Unlock `AudioContext` Saat Klik Start**: Safari iOS tidak mendukung `navigator.vibrate`. Oleh karena itu, saat pengguna menekan tombol **Mulai membaca sensor**, halaman langsung membuka kunci `AudioContext` sehingga saat `ALERT_MATA` atau `TEGURAN_ORTU` masuk, HP mengeluarkan bunyi *beep* oscillator tanpa diblokir oleh kebijakan *autoplay*.
- **Screen Wake Lock API**: Mencegah layar HP mati selama pengujian berlangsung, dan otomatis meminta ulang *wake lock* ketika tab kembali aktif (`visibilitychange`).
- **Penanganan Event `CLEAR`**: Ketika anak kembali ke posisi duduk sehat atau meletakkan HP telungkup di meja, pesan `CLEAR` pada `rebahguard/<PROJECT_ID>/alerts/child` langsung mengembalikan banner merah ke status hijau aman.
