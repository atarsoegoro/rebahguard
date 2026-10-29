# Sensor Playground (Eksplorasi Multi-Sensor via Browser HP)

Halaman [`web-edge/index.html`](../web-edge/index.html) juga dilengkapi mode **Sensor Playground** untuk mengeksplorasi pembacaan berbagai sensor smartphone secara mandiri ke topik MQTT pilihan Anda.

## Cara Menggunakan

1. Buka halaman `web-edge` melalui **HTTPS** di Safari iPhone atau Chrome Android.
2. Tekan tombol **Buka Sensor Playground** (atau tambahkan `?mode=playground` pada URL).
3. Isi **Device ID**, **MQTT WebSocket URL (WSS)**, dan **MQTT Topic** yang unik.
4. Pilih sensor yang ingin dikirim (**Accelerometer**, **Gyroscope**, **Orientation**, **GPS**, **Microphone RMS**), lalu tekan **Start sensor sender**.
5. Tekan **Kembali ke RebahGuard** untuk kembali ke mode deteksi postur RebahGuard.

## Sensor & Format JSON

| Sensor | API Browser | Field JSON |
|---|---|---|
| **Accelerometer** | `DeviceMotionEvent.accelerationIncludingGravity` | `sensors.accelerometer.{x,y,z,magnitude}` ($\text{m/s}^2$) + `features.motion_rms` (*mean-centered*) |
| **Gyroscope** | `DeviceMotionEvent.rotationRate` | `sensors.gyroscope.{x,y,z,magnitude,unit:"rad/s"}` |
| **Orientation** | `DeviceOrientationEvent` | `sensors.orientation.{alpha,beta,gamma,unit:"deg"}` |
| **GPS** | `navigator.geolocation.watchPosition` | `sensors.gps.{latitude,longitude,accuracy_m}` |
| **Microphone** | `getUserMedia` + `AnalyserNode` | `sensors.microphone.{rms,unit:"linear_amplitude_0_to_1"}` |
