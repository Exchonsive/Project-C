# Project-C

Project-C adalah aplikasi web interaktif berbasis Streamlit yang menggunakan kamera browser dan deteksi tangan untuk membuat efek portal filter secara real-time. Pemrosesan kamera dan filter dilakukan di JavaScript pada browser menggunakan MediaPipe Tasks Vision.

## Fitur Utama

- Deteksi hingga dua tangan secara real-time
- Aktivasi portal dengan gerakan pinch pada kedua tangan
- Pergantian filter dengan gerakan pinch pada salah satu tangan
- Filter `Normal`, `Invert`, `B & W`, `Sepia`, `Warm HDR`, dan `Neon Edge`
- Tampilan kamera yang di-mirror seperti cermin

## Teknologi yang Digunakan

- Streamlit
- JavaScript (ES module)
- MediaPipe Tasks Vision
- HTML Canvas API

## Persyaratan Sistem

- Python 3.10+
- Kamera terhubung ke perangkat
- Browser modern yang mendukung `getUserMedia`, JavaScript modules, dan WebGL
- Koneksi internet untuk memuat MediaPipe Tasks Vision, WASM, dan model dari CDN

## Cara Menjalankan

1. Install dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```

2. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

3. Buka URL yang ditampilkan Streamlit, biasanya `http://localhost:8501`, lalu izinkan akses kamera.

## Cara Menggunakan

1. Pastikan kamera aktif dan wajah atau tangan terlihat jelas.
2. Lakukan pinch dengan ibu jari dan telunjuk pada kedua tangan untuk membuka atau menutup portal.
3. Saat portal terbuka, lakukan pinch dengan satu tangan untuk mengganti filter.
4. Area di antara ibu jari dan telunjuk kedua tangan akan menerima filter aktif.

## Catatan

- Kamera diakses langsung oleh JavaScript melalui browser; aplikasi tidak menggunakan `streamlit-webrtc`.
- Akses kamera browser biasanya memerlukan secure context (`localhost` atau HTTPS). Jika kamera tidak dapat diakses, periksa izin kamera dan pesan error pada halaman.
- Aplikasi membutuhkan koneksi internet saat runtime untuk memuat library, WASM, dan model MediaPipe.
- Live demo: https://exchonsive-project-c.streamlit.app/

## Lisensi

Proyek ini dilisensikan di bawah MIT License. Lihat file LICENSE untuk informasi lebih lanjut.
