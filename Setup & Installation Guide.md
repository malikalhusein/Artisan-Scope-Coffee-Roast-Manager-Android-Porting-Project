# 🛠️ Setup & Installation Guide: Artisan-Lite
*Raga Roastery IoT Modbus Gateway — v2 (HTML/WebView Edition)*  
*Last Updated: 2026-03-10*

---

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
