# 🛠️ Setup & Installation Guide: Artisan-Lite
*Raga Roastery IoT Modbus Gateway — v2 (HTML/WebView Edition)*
*Last Updated: 2026-03-10*

---

<<<<<<< HEAD
## 🌟 TL;DR — Cara Tercepat Preview UI

```bash
# 1. Buka artisan_lite_ui.html di browser Macbook/PC:
open "artisan_lite_ui.html"

# 2. Klik ON → START → jalankan demo mode ✅
```

Tidak perlu install apapun. File HTML sudah self-contained dengan semua dependencies (Chart.js) dari CDN.

---

## Bagian 1: Persiapan Gateway (Huawei HG553 — OpenWrt)

### 1.1 Prerequisites
- Huawei EchoLife HG553 dengan OpenWrt 23.05.5 terpasang
- USB-RS485 adapter (FTDI FT232R) terpasang di USB port router
- Mesin roasting terhubung via kabel RS485

### 1.2 Fix OPKG (jika download gagal — IPv6 issue)
```bash
# SSH ke router
ssh root@192.168.11.3

# Paksa gunakan IPv4 dan HTTP
sed -i 's/https/http/g' /etc/opkg/distfeeds.conf
echo "151.101.2.132 downloads.openwrt.org" >> /etc/hosts
opkg update
```

### 1.3 Install dan konfigurasi net2ser (TCP-to-Serial bridge)
```bash
opkg install net2ser

# Edit konfigurasi net2ser
# Bind TCP port 5000 → /dev/ttyUSB0 @ 9600 8N2
uci set net2ser.@net2ser[0].bind_address='0.0.0.0'
uci set net2ser.@net2ser[0].bind_port='5000'
uci set net2ser.@net2ser[0].serial_port='/dev/ttyUSB0'
uci set net2ser.@net2ser[0].baud_rate='9600'
uci set net2ser.@net2ser[0].data_bits='8'
uci set net2ser.@net2ser[0].parity='none'
uci set net2ser.@net2ser[0].stop_bits='2'
uci commit net2ser
/etc/init.d/net2ser enable
/etc/init.d/net2ser start
```

### 1.4 Verifikasi gateway
```bash
# Di Macbook/PC, test koneksi TCP ke gateway:
nc -zv 192.168.11.3 5000
# Expected: Connection to 192.168.11.3 port 5000 [tcp] succeeded!
```

---

## Bagian 2: Transfer File UI ke Tablet Android

### Opsi A — Via Google Drive (Direkomendasikan)
1. Upload `artisan_lite_ui.html` ke Google Drive dari Macbook
2. Di tablet, buka Google Drive → Download file ke `/sdcard/Download/`
3. Buka file manager → navigasi ke Download → tap `artisan_lite_ui.html`
4. Pilih **"Open with Chrome"** atau browser lain

### Opsi B — Via USB Cable
```bash
# Di Macbook (pastikan MTP mode aktif di tablet):
cp artisan_lite_ui.html /Volumes/InternelStorage/Download/
```

### Opsi C — Via Local HTTP Server (untuk development)
```bash
# Di Macbook, jalankan simple HTTP server:
cd "/Users/malikalhusein/Documents/Google AntiGravity/Raga Artisan Scope Project"
python3 -m http.server 8080

# Di browser tablet, buka:
# http://[IP-Macbook]:8080/artisan_lite_ui.html
```

---

## Bagian 3: Menjalankan Artisan-Lite di Tablet

### 3.1 Koneksi ke Wi-Fi Gateway
1. Buka **Pengaturan Wi-Fi** di tablet
2. Sambungkan ke SSID yang sama dengan gateway Huawei HG553
3. Pastikan bisa ping `192.168.11.3`

### 3.2 Membuka UI
1. Buka Chrome / Samsung Internet di tablet
2. Navigasi ke `artisan_lite_ui.html` (dari file manager atau URL server)
3. Untuk fullscreen: tap ⋮ → **"Add to Home Screen"** (Progressive Web App-like)

### 3.3 Konfigurasi Koneksi
1. Tekan tombol **CONFIG ⚙️** di top bar
2. Tab **Modbus / TCP**:
   - Type: `TCP`
   - Host: `192.168.11.3`
   - Port: `5000`
   - Timeout: `1.0`
   - Retries: `1`
3. Tab **Device Assignment**:
   - Ch.1 (ET): Unit ID=`1`, Register=`1000`, FC=`FC04`, Divider=`1÷10`, Mode=`C`
   - Ch.2 (BT): Unit ID=`2`, Register=`1000`, FC=`FC04`, Divider=`1÷10`, Mode=`C`
4. Klik **OK / Apply**

### 3.4 Load Konfigurasi dari file .aset (Opsional)
Jika sudah punya file konfigurasi Artisan Desktop (`.aset`):
1. Di modal Config, klik **📂 Load .aset**
2. Pilih file `.aset` dari storage tablet
3. Semua parameter (host, port, register, channel) akan ter-load otomatis
4. Klik **OK / Apply**

---

## Bagian 4: Menjalankan Sesi Roasting

```
1. Tekan [ON]        → Mulai koneksi ke gateway (atau demo mode jika offline)
2. Tekan [START]     → Mulai timer & rekam data
3. Tekan [CHARGE]    → Tandai saat biji kopi dimasukkan
4. Tekan [DRY END]   → Tandai akhir fase drying
5. Tekan [FC START]  → Tandai First Crack mulai
6. Tekan [FC END]    → Tandai First Crack selesai
7. Tekan [SC START]  → Tandai Second Crack mulai (jika ada)
8. Tekan [SC END]    → Tandai Second Crack selesai (jika ada)
9. Tekan [DROP]      → Tandai saat biji di-drop ke cooling tray
10. Tekan [COOL]     → Tandai akhir fase cooling
11. Tekan [STOP]     → Hentikan rekaman
```

Setiap event akan:
- Membuat marker vertikal di grafik
- Memperbarui timer di **Phases LCD** sidebar (DRYING / MAILLARD / DEV)
- Disimpan dalam `timeindex[0..7]` untuk kompatibilitas Artisan

---

## Bagian 5: Menyimpan Hasil Roasting

### 5.1 Save Roast Log
1. Tekan tombol **LOG 💾** di top bar
2. Dua file akan terdownload otomatis:
   - `artisan_lite_roast_[timestamp].alog` — JSON, compatible dengan Artisan Desktop
   - `artisan_lite_roast_[timestamp].csv` — untuk analisis Excel/Sheets

### 5.2 Load Roast Log Sebelumnya
1. Tekan tombol **LOG 💾** → pilih **Load Log**
2. Pilih file `.alog` dari storage
3. Grafik akan ter-rekonstruksi lengkap dengan event markers

### 5.3 Analisis di Artisan Desktop (Macbook)
1. Copy file `.alog` dari tablet ke Macbook (Google Drive / USB)
2. Buka Artisan Desktop
3. Menu **File → Open Recent** → pilih file `.alog`
4. Grafik roasting akan tampil lengkap dengan semua event markers

---

## Bagian 6: Save/Load Konfigurasi (.aset)

### Save config ke .aset
1. Buka **CONFIG ⚙️** → atur semua parameter
2. Klik **💾 Save .aset** di bagian bawah modal
3. File `artisan_lite_config.aset` akan terdownload

Format file `.aset` menggunakan key yang kompatibel dengan Artisan desktop:
```ini
[artisan]
modbushost = 192.168.11.3
modbusport = 5000
modbusinputids = [1,2,0,0,0,0,0,0,0,0]
modbusinputregisters = [1000,1000,0,0,0,0,0,0,0,0]
...
```

### Load config dari .aset
1. Buka **CONFIG ⚙️**
2. Klik **📂 Load .aset**
3. Pilih file `.aset` (bisa dari Artisan Desktop atau file yang sudah disave sebelumnya)

---

## Bagian 7: Mode Demo (Tanpa Hardware)

Jika gateway tidak tersedia, UI tetap bisa dijalankan dalam **Demo Mode**:

1. Buka `artisan_lite_ui.html` di browser manapun (tidak perlu terhubung ke gateway)
2. Tekan **ON** (akan menampilkan "Demo Mode")
3. Tekan **START** — data simulasi ET & BT akan mulai mengalir
4. Semua fitur (event marking, phase bands, save/load) tetap berfungsi penuh

---

## Bagian 8: Pydroid 3 (Legacy — Untuk Future Backend)

> ⚠️ Bagian ini untuk development backend Python Modbus bridge di masa depan.  
> UI HTML tidak memerlukan Pydroid untuk berjalan.

Jika ingin menjalankan backend Python (`modbus_to_ws.py`) di tablet:

1. Install **Pydroid 3** dari Google Play Store
2. Buka Pydroid → Menu → **Pip** → Install:
   - `pymodbus`
   - `websockets`
   - `asyncio`
3. Buka file `modbus_to_ws.py` (akan dibuat di Sprint 6)
4. Tekan tombol Play kuning → backend berjalan di `localhost:8765`
5. Di HTML UI, ubah host ke `localhost:8765` (WebSocket mode)

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| "Cannot connect to gateway" | Pastikan tablet di Wi-Fi yang sama. Test `ping 192.168.11.3` |
| Suhu tampil `---` | Cek Unit ID dan Register di Device Assignment tab |
| Nilai suhu tidak masuk akal (misal 65535) | Ubah Divider dari `0` ke `1` (÷10) |
| Chart tidak update | Refresh halaman, tekan RESET lalu ON → START lagi |
| File .aset tidak terbaca | Pastikan format file benar — key `modbushost` harus ada |
| Grafik tidak smooth di tablet | Kurangi sampling rate dari 1s ke 2s di Device Assignment |
=======
## 🚨 Baca Ini Dulu — Status Proyek Saat Ini

Ada **dua skenario** penggunaan, dan ini penting kamu pahami sebelum mulai:

| Skenario | Status | Keterangan |
|---|---|---|
| **A — UI + Demo Mode** | ✅ Siap dipakai | Semua fitur UI, grafik simulasi, save/load log & config |
| **B — Live Data dari Mesin** | ✅ Siap dipakai | Baca ET & BT nyata dari mesin via Pydroid + WebSocket |

> **Jujurnya**: Untuk Demo Mode (tanpa mesin), UI bisa dijalankan langsung dari Chrome. Untuk **Live Data dari mesin nyata**, Anda harus mensimulasikan "Backend" dengan menjalankan satu script Python (`modbus_to_ws.py`) di background tablet (menggunakan Pydroid 3) agar Chrome bisa menerima data Modbus.

---

## ☕ SKENARIO A — "Mau Roasting Hari Ini" (UI Ready, Data Simulasi)

> Gunakan skenario ini **sekarang**. Kamu bisa catat semua event, lihat grafik fase, dan save log — dengan data simulasi sebagai referensi visual.

### Step 1: Nyalakan Perangkat
1. Nyalakan **mesin roasting** — pastikan thermocouple ET & BT terpasang
2. Colokkan **USB-RS485 adapter** dari mesin ke port USB **Huawei HG553**
3. Nyalakan **Huawei HG553** → tunggu boot selesai (~60 detik, lampu Wi-Fi menyala)

### Step 2: Sambungkan Tablet ke Wi-Fi
1. Buka **Pengaturan → Wi-Fi** di Infinix XPad
2. Sambungkan ke jaringan Wi-Fi yang sama dengan HG553
3. *(Opsional verifikasi)*: buka Chrome → ketik `http://192.168.11.3` — jika halaman terbuka, gateway aktif ✅

### Step 3: Buka Artisan-Lite di Tablet

**One-time setup** (pertama kali saja): transfer file ke tablet dulu:
```
Macbook → Google Drive → upload artisan_lite_ui.html
Tablet  → Google Drive → download ke /sdcard/Download/
```

Selanjutnya, setiap kali mau roasting:
1. Buka **Chrome** di tablet
2. Di address bar ketik: `file:///sdcard/Download/artisan_lite_ui.html`
3. UI terbuka → siap digunakan!

   > 💡 **Tips**: Buka menu Chrome ⋮ → **"Add to Home Screen"** → nanti bisa buka dari layar utama tablet seperti aplikasi biasa.

### Step 4: Konfigurasi (Hanya Perlu Sekali)
1. Ketuk **CONFIG ⚙️** di top bar
2. Tab **Modbus / TCP**:  
   Host: `192.168.11.3` | Port: `5000` | Timeout: `1.0` | Type: `TCP`
3. Tab **Device Assignment**:  
   Ch.1 (ET): Unit ID=`1`, Register=`1000`, FC=`FC04`, Divider=`1÷10`, Mode=`C`  
   Ch.2 (BT): Unit ID=`2`, Register=`1000`, FC=`FC04`, Divider=`1÷10`, Mode=`C`
4. Klik **💾 Save .aset** → simpan config (cukup sekali, load lagi kapan pun)
5. Klik **OK / Apply**

### Step 5: Roasting! 🔥

```
Urutan tombol saat roasting:

[ON]         → Aktifkan (demo mode = simulasi data)
[START]      → Mulai timer & rekam

↓ Saat masukkan biji ke mesin:
[CHARGE]     → timeindex[0] — fase drying mulai dihitung

↓ ~4–8 menit (suhu BT ~160–170°C):
[DRY END]    → timeindex[1] — Phases LCD: DRYING timer muncul

↓ Saat dengar first crack:
[FC START]   → timeindex[2] — Phases LCD: MAILLARD timer muncul
[FC END]     → timeindex[3]

↓ (Opsional, jika roast lebih gelap):
[SC START]   → timeindex[4]
[SC END]     → timeindex[5]

↓ Saat buang biji ke cooling tray:
[DROP]       → timeindex[6] — Phases LCD: DEV timer muncul

↓ Setelah cooling selesai:
[COOL]       → timeindex[7]

[STOP]       → Hentikan rekaman
```

**Perhatikan sidebar kanan** — Phases LCD akan otomatis menampilkan:
- `DRYING` — durasi dari CHARGE ke DRY END
- `MAILLARD` — durasi dari DRY END ke FC START
- `DEV` — durasi dari FC START ke DROP

### Step 6: Simpan Log
1. Tekan **LOG 💾** di top bar
2. Dua file terdownload otomatis:
   - `.alog` — kompatibel dengan Artisan Desktop (untuk analisis lanjut)
   - `.csv` — untuk Excel / Google Sheets
3. *(Opsional)*: copy file `.alog` ke Macbook → buka di Artisan Desktop

---

## 🖥️ Paralel: Artisan Desktop di Macbook (Live Data Sekarang)

Sambil menunggu Sprint 6 selesai, **Artisan Desktop sudah langsung bisa** baca live data ET & BT dari mesin:

1. Pastikan Macbook terhubung ke Wi-Fi yang sama
2. Buka Artisan → **Config → Ports → Modbus**:
   - Type: `TCP` | Host: `192.168.11.3` | Port: `5000`
   - Input 1 (ET): Device=1, Reg=1000, FC=4, Mode=C
   - Input 2 (BT): Device=2, Reg=1000, FC=4, Mode=C
3. Tekan **ON** → Artisan Desktop mulai baca suhu langsung dari mesin ✅

> File `.aset` yang disave dari Artisan-Lite juga bisa di-load ke Artisan Desktop (dan sebaliknya) karena format key-nya sudah kompatibel.

---

## � SKENARIO B — Live Data Langsung ke Tablet (Hari H Roasting)

Ini adalah cara kerja nyata di mana tablet akan membaca suhu ET & BT aktual dari mesin.

### Prerequisite: Install Pydroid 3
Karena Chrome Android tidak bisa membaca Modbus TCP secara native, kita butuh "Jembatan WebSocket" dari Python.
1. Install **Pydroid 3** dari Google Play Store di tablet
2. Buka Pydroid → Menu ≡ → **Pip** → Install: `pymodbus` dan `websockets`
3. Copy **`modbus_to_ws.py`** ke memori tablet bersama dengan `artisan_lite_ui.html`

### Step 1: Jalankan Backend (Bridge)
1. Nyalakan mesin roasting & Gateway Huawei HG553
2. Buka **Pydroid 3** di tablet
3. Buka file `modbus_to_ws.py`
4. Tekan tombol ▶️ Play kuning besar.
5. Akan muncul teks di terminal Pydroid: `Memulai WebSocket... Menghubungkan ke Modbus...`
   Biarkan Pydroid berjalan di background. (Jangan di-swipe close/force close).

### Step 2: Buka UI
1. Buka **Chrome** di tablet
2. Buka `file:///sdcard/Download/artisan_lite_ui.html`
3. Tekan **ON**
4. Status akan berubah menjadi **LIVE — Connected to Gateway** (Warna hijau).
5. Selesai! Saat ditekan START, grafik akan langsung merender suhu benda nyata dari mesin Anda.

> Jika backend mati atau terputus secara tiba-tiba saat roasting, UI tidak akan crash. UI akan menampilkan **"MODBUS disconnected — retrying..."** dan beralih ke warna fallback otomatis.

---

## 🔧 Troubleshooting

| Masalah | Solusi |
|---|---|
| File HTML tidak terbuka di Chrome | Coba ketik alamat manual di address bar: `file:///sdcard/Download/artisan_lite_ui.html` |
| Suhu tampil `---` (tapi itu normal!) | Normal untuk saat ini — data simulasi berjalan setelah klik ON → START |
| Modal Config tidak menutup | Refresh halaman Chrome, buka ulang |
| File .aset tidak terbaca | Pastikan file dari versi terbaru `artisan_lite_ui.html` (v2) |
| Tombol SC END / COOL tidak ada | Kamu pakai versi lama — download ulang `artisan_lite_ui.html` yang terbaru |
| Gateway tidak merespons | Cek apakah HG553 sudah boot penuh dan USB-RS485 terpasang |
>>>>>>> 1f79151 (feat(Sprint 6): Add Python WebSocket bridge (modbus_to_ws.py), integrate WS client in HTML UI, and update S6 documentation)
