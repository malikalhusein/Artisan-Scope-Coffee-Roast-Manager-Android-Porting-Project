# Setup & Installation Guide: Artisan-Lite Android Port

Panduan ini menjelaskan langkah demi langkah cara menginstal dan menjalankan aplikasi **Artisan-Lite** di tablet Android Anda (Infinix XPad) menggunakan **Pydroid 3**.

---

## Bagian 1: Persiapan Tablet (Instalasi Pydroid 3)

Pydroid 3 adalah emulator dan IDE Python 3 yang sangat stabil di Android. Ini adalah cara tercepat untuk menjalankan aplikasi Kivy tanpa harus melakukan proses *build APK* (Buildozer) yang rumit.

1.  Buka **Google Play Store** di tablet Android Anda.
2.  Cari aplikasi **"Pydroid 3 - IDE for Python 3"** (Developer: IIEC).
3.  Instal dan buka aplikasi tersebut.
4.  *(Opsional namun disarankan)*: Instal juga plugin **"Pydroid repository plugin"** dari Play Store agar proses unduh *library* lebih stabil.

---

## Bagian 2: Menginstal Library yang Dibutuhkan

Aplikasi Kivy Artisan-Lite membutuhkan beberapa komponen (*library*) khusus.

1.  Buka aplikasi **Pydroid 3**.
2.  Ketuk ikon **Menu Hamburger (Garis Tiga)** di pojok kiri atas.
3.  Pilih menu **Pip**.
4.  Di tab `INSTALL`, ketik dan instal library berikut satu per satu (ketik namanya, lalu tekan tombol kuning INSTALL):
    *   `kivy`
    *   `pymodbus`
    *   `matplotlib`
5.  *Tunggu hingga terminal menampilkan pesan sukses untuk setiap instalasi.*

---

## Bagian 3: Memasukkan File Proyek ke Tablet

Anda perlu memindahkan folder proyek `src` dari Macbook Anda ke tablet.

1.  Di Macbook Anda, temukan folder `src` yang berisi file aplikasi:
    *   `main.py`
    *   `config_manager.py`
    *   `logger.py`
    *   `modbus_handler.py`
2.  Salin seluruh folder `src` tersebut ke memori internal tablet Anda (misalnya: ke folder `Download` atau `Documents` di Infinix XPad) menggunakan Kabel USB, Google Drive, atau Bluetooth.
3.  *(Opsional)*: Jika Anda memiliki file konfigurasi Artisan Desktop (`.aset`) seperti `Settingan RAGA JOSS wirles.aset`, Anda bisa menyalinnya **ke dalam folder `src` yang sama** agar langsung terbaca oleh aplikasi.

---

## Bagian 4: Menjalankan Aplikasi

1.  Buka aplikasi **Pydroid 3**.
2.  Ketuk ikon **Folder** di pojok kanan atas, lalu pilih **Open**.
3.  Cari lokasi tempat Anda menyimpan folder `src` tadi di `Internal Storage` tablet.
4.  Pilih dan buka file **`main.py`**.
5.  Pastikan tablet Anda sudah **Terhubung ke Wi-Fi Gateway Mesin Roasting (Huawei HG553)**.
6.  Tekan **Tombol Play Kuning** yang besar di pojok kanan bawah Pydroid 3.

Aplikasi Artisan-Lite akan terbuka dengan layar Kivy.

---

## Bagian 5: Mengubah Pengaturan di Dalam Aplikasi

Jika alamat IP atau ID *Register* Modbus mesin Anda berbeda—atau jika .aset awal tidak terbaca:

1.  Pada layar utama aplikasi, ketuk tombol abu-abu **Config ⚙️**.
2.  Ubah `IP Host` menjadi `192.168.11.3` dan `TCP Port` menjadi `5000`.
3.  Pastikan parameter Modbus benar (ET = ID 1 / Reg 1000, BT = ID 2 / Reg 1000).
4.  Ketuk **Save & Apply**. (Ini akan langsung mengubah/membuat file `.aset` di memori tablet).
5.  Aplikasi akan kembali ke menu awal. Ketuk **Connect** untuk mulai membaca suhu.

---

## Bagian 6: Menyimpan Hasil Roasting (Log)

1.  Saat proses menyangrai kopi selesai, tekan tombol merah **Disconnect**.
2.  Tekan tombol biru **Save Log**.
3.  Aplikasi akan otomatis membuat file `.csv` (untuk Excel) dan `.alog` (untuk Artisan Desktop) di dalam folder `src` tersebut.
4.  File `.alog` ini bisa Anda salin kembali ke Macbook untuk di-*Load* ke dalam aplikasi Artisan utama jika ingin menganalisa grafik lengkung lebih lanjut.
