# 🛠️ Setup & Installation Guide: Artisan-Lite
*Raga Roastery IoT Modbus Gateway — v2 (HTML/WebView Edition)*
*Last Updated: 2026-03-10*

---

## 🌟 Quick Start (Preview UI Instan)
Jika Anda hanya ingin melihat tampilan UI atau mencoba fitur simulasi:
1. Klik kanan file [`artisan_lite_ui.html`](./artisan_lite_ui.html) -> **Open with Chrome**.
2. Klik tombol **ON** (Warna kuning: "DEMO MODE").
3. Klik tombol **START** (Warna merah: "STOP").
4. Data simulasi suhu akan mulai mengalir di grafik. 

---

## 🏗️ Bagian 1: Persiapan Hardware (Gateway)
Pastikan Gateway (Huawei HG553) sudah siap untuk memancarkan data Modbus via Wi-Fi.

### 1.1 Koneksi Fisik
- Hubungkan kabel RS485 dari mesin roasting ke **USB-RS485 Adapter**.
- Colokkan adapter ke port USB di **Huawei HG553**.
- Nyalakan Router dan tunggu hingga lampu Wi-Fi stabil (~60 detik).

### 1.2 Konfigurasi Router (OpenWrt)
Jika router belum dikonfigurasi, jalankan perintah ini via SSH (`ssh root@192.168.11.3`):
```bash
# Update package list (Gunakan HTTP jika HTTPS gagal)
sed -i 's/https/http/g' /etc/opkg/distfeeds.conf
opkg update

# Install & Aktifkan Bridge TCP-to-Serial
opkg install net2ser
uci set net2ser.@net2ser[0].bind_port='5000'
uci set net2ser.@net2ser[0].serial_port='/dev/ttyUSB0'
uci set net2ser.@net2ser[0].baud_rate='9600'
uci commit net2ser
/etc/init.d/net2ser restart
```

---

## 💻 Bagian 2: Persiapan Software (Tablet & Macbook)

### 2.1 Pindah File ke Tablet
Transfer file `artisan_lite_ui.html` dan `modbus_to_ws.py` ke tablet:
- **Cara termudah**: Gunakan Google Drive atau kabel USB. Simpan di folder `/Download/`.

### 2.2 Install Dependencies (Hanya di Tablet)
Karena Chrome Android tidak bisa membaca Modbus secara langsung, kita butuh jembatan Python:
1. Install **Pydroid 3** dari Play Store.
2. Di dalam Pydroid 3, buka menu **Pip** dan install: `pymodbus` dan `websockets`.

---

## 🔥 Bagian 3: Panduan Hari-H Roasting (Workflow)

Ikuti urutan ini setiap kali Anda akan mulai menyangrai kopi.

### Langkah 1: Jalankan Backend Bridge
1. Buka **Pydroid 3** di tablet.
2. Buka file `modbus_to_ws.py`.
3. Klik tombol **Play (▶️)**. Biarkan Pydroid berjalan di background.
   > Backend ini akan membaca data HG553 dan mengirimkannya ke UI.

### Langkah 2: Buka UI di Chrome
1. Buka **Chrome** di tablet.
2. Buka alamat: `file:///sdcard/Download/artisan_lite_ui.html`
3. Ketuk menu ⋮ -> **Add to Home Screen** agar bisa dibuka seperti aplikasi biasa di masa depan.

### Langkah 3: Koneksi & Roasting
1. Klik **ON** -> Status harus berubah hijau: **"LIVE — Connected to Gateway"**.
2. Klik **START** saat mesin siap.
3. Gunakan tombol event (**CHARGE**, **DRY END**, **FC START**, **DROP**, dsb) sesuai progres sangrai.

---

## 💾 Bagian 4: Analisis & Penyimpanan

### 4.1 Menyimpan Data
Setelah menekan **STOP**, klik tombol **LOG 💾**:
- File `.alog` akan terdownload. File ini bisa langsung dibuka di **Artisan Desktop (Macbook)** untuk analisis profesional.
- File `.csv` juga tersedia untuk dibuka di Microsoft Excel.

### 4.2 Mengatur Konfigurasi
Jika Anda ingin mengubah nomor register atau IP address:
1. Klik **CONFIG ⚙️**.
2. Ubah parameter sesuai kebutuhan, lalu klik **OK/Apply**.
3. Klik **💾 Save .aset** untuk menyimpan settingan tersebut selamanya.

---

## 🔧 Troubleshooting
| Masalah | Solusi |
|---|---|
| Status tetap "DEMO MODE" | Pastikan script di Pydroid 3 sudah status "Listening/Aktif". |
| Suhu di grafik `---` | Cek apakah HG553 sudah menyala dan tablet terhubung ke Wi-Fi-nya. |
| Tombol event tidak merespon | Pastikan Anda sudah klik **ON** dan **START** terlebih dahulu. |
| Error di Pydroid | Pastikan sudah install `pymodbus` dan `websockets` di menu Pip. |
| Grafik tidak muncul (**Offline**) | Pastikan folder `libs/` berisi `chart.js` sudah dipindah ke tablet. |
| UI Terasa "Nge-Bug" | Lakukan **Force Refresh** di Chrome (Cmd+Shift+R atau Ctrl+F5) untuk hapus cache versi lama. |

---

### 🚀 Tips Tambahan: Modus Simulasi (Tanpa Hardware)
Jika Anda ingin mengetes koneksi tablet ke backend tanpa menyalakan mesin roasting:
1. Di Pydroid 3, jalankan perintah ini di Terminal:
   ```bash
   python3 modbus_to_ws.py --simulate
   ```
2. Buka UI di Chrome. Status akan berubah menjadi **LIVE — Connected to Gateway** dan data suhu akan mengalir otomatis meskipun mesin mati. Ini berguna untuk memastikan "jalur pipa" data dari Python ke Chrome sudah lancar.
