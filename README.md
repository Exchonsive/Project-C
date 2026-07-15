# Project-C

Project-C adalah aplikasi web interaktif berbasis Streamlit yang memanfaatkan kamera dan deteksi tangan untuk membuat efek portal filter secara real-time. Aplikasi ini menggunakan MediaPipe untuk mendeteksi landmark tangan dan OpenCV untuk menerapkan berbagai filter visual pada area yang dibentuk oleh dua tangan.

## Fitur Utama

- Deteksi tangan secara real-time dari kamera
- Aktivasi portal filter dengan gerakan pinch pada dua tangan
- Pergantian filter visual secara interaktif
- Berbagai efek visual seperti Invert, Heatmap, Cartoon, Neon Glow, dan lainnya
- Antarmuka sederhana yang berjalan di browser

## Teknologi yang Digunakan

- Python
- Streamlit
- Streamlit WebRTC
- OpenCV
- MediaPipe
- NumPy

## Persyaratan Sistem

- Python 3.10+ 
- Kamera terhubung ke perangkat

## Cara Menjalankan

1. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

2. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

3. Buka tautan lokal yang muncul di browser lalu izinkan akses kamera.

## Catatan

- File model MediaPipe akan diunduh secara otomatis saat aplikasi dijalankan jika belum tersedia.
- Aplikasi ini membutuhkan koneksi internet untuk mengunduh model awal.
- Live Demo : https://exchonsive-project-c.streamlit.app/

## Lisensi

Proyek ini dilisensikan di bawah MIT License. Lihat file LICENSE untuk informasi lebih lanjut.
