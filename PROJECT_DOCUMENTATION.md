# 📖 DOKUMENTASI PROYEK: RAGA ROASTERY IoT MODBUS GATEWAY
*Last Updated: 2026-03-10 | Sprint 5 — Artisan Source Alignment*

---

## 1. Deskripsi Proyek

Proyek **"Artisan-Lite"** bertujuan untuk membuat antarmuka monitoring & logging mesin sangrai kopi yang berjalan di tablet Android, terhubung secara nirkabel ke mesin roasting melalui gateway Modbus TCP/RTU custom berbasis router OpenWrt.

### Pivot Teknologi UI
Proyek ini telah **pivot dari Python/Kivy ke HTML/JS/CSS** untuk mendapatkan keunggulan desain dan kemudahan preview. UI utama kini ada dalam satu file:

```
artisan_lite_ui.html  ← Single-file HTML/JS/CSS app (WebView-ready)
```

UI ini dirancang selaras dengan source code [Artisan Roaster Scope](https://github.com/artisan-roaster-scope/artisan) untuk kompatibilitas maksimal.

---

## 2. Spesifikasi Perangkat Keras

| Komponen | Spesifikasi |
|---|---|
| **Router / Gateway** | Huawei EchoLife HG553 (RAM 64MB) |
| **OS** | OpenWrt 23.05.5 (Kernel 5.15.167) |
| **Konverter Serial** | USB-RS485 FTDI FT232R |
| **Mesin Roasting** | 1kg — Vegas (Mesin Kopi Jember) |
| **Tablet Client** | Infinix XPad (Infinix X20, Helio G99) |
| **Perangkat Rencana** | Active USB Hub, TP-Link WN722N V1 (AR9271), USB Flashdisk (Swap) |

---

## 3. Parameter Komunikasi Modbus RTU

```
Baudrate : 9600
Data Bits: 8
Parity   : None (N)
Stop Bits: 2
Format   : 9600 8N2
```

### Register Suhu (Artisan `modbusport.py` — channels=10)

| Channel | Sensor | Unit ID | Register | FC | Divider | Mode |
|---|---|---|---|---|---|---|
| Ch.1 (inputDeviceIds[0]) | ET (Environment Temp) | 1 | 1000 | FC04 | ÷10 | C |
| Ch.2 (inputDeviceIds[1]) | BT (Bean Temp) | 2 | 1000 | FC04 | ÷10 | C |
| Ch.3-10 | Extra Devices | 0 | 0 | FC03 | none | C |

> **Catatan**: Artisan menggunakan 10 channel (`channels=10`) dengan array `inputDeviceIds`, `inputRegisters`, `inputCodes`, `inputDivs`, `inputModes`.  
> Divider: `0`=none, `1`=÷10, `2`=÷100.

---

## 4. Topologi Jaringan

```
[Mesin Roaster 1kg]
    │ RS485 Modbus RTU (9600 8N2)
    ▼
[FTDI FT232R] → /dev/ttyUSB0
    │ USB
    ▼
[Huawei HG553 — 192.168.11.3]
    ├── net2ser service: port 5000 → /dev/ttyUSB0
    └── Wi-Fi AP: SSID Raga Roastery
         │
         ├── [Macbook] → Artisan Desktop (socket://192.168.11.3:5000)
         └── [Infinix XPad] → artisan_lite_ui.html (Modbus TCP)
```

**Parameter koneksi:**
- **Host:** `192.168.11.3`
- **Port:** `5000` (Modbus TCP)
- **Type:** TCP (Artisan type=3)
- **Timeout:** 1.0s
- **Retries:** 1

---

## 5. Struktur Kode (artisan_lite_ui.html)

### State Management (aligned dengan Artisan `canvas.py`)

```javascript
// timeindex[0..7] matches Artisan canvas.py exactly:
// 0=CHARGE, 1=DRY END, 2=FCs, 3=FCe, 4=SCs, 5=SCe, 6=DROP, 7=COOL
let timeindex = [-1, 0, 0, 0, 0, 0, 0, 0];

// Modbus config (matches modbusport.py)
const cfg = {
  type: 3,            // 0=RTU, 1=ASCII, 2=Binary, 3=TCP, 4=UDP
  host: '192.168.11.3',
  port: 5000,
  inputDeviceIds: [1, 2, 0, 0, 0, 0, 0, 0, 0, 0],  // 10 channels
  inputRegisters:  [1000, 1000, 0, ...],
  inputCodes:      [4, 4, 3, ...],    // FC04 for ET/BT
  inputDivs:       [1, 1, 0, ...],    // ÷10 for ET/BT
  inputModes:      ['C', 'C', ...],
  wordorderLittle: true
};
```

### Phase Bands (aligned dengan Artisan `colors.py` palette)

| Palette Key | Fase | Warna | Trigger |
|---|---|---|---|
| `rect1` | Drying 🟠 | `rgba(230,81,0,.14)` | CHARGE → DRY END |
| `rect2` | Maillard 🟡 | `rgba(180,120,0,.14)` | DRY END → FCs |
| `rect3` | Finishing/Dev 🟢 | `rgba(46,125,50,.14)` | FCs → DROP |
| `rect4` | Cooling 🔵 | `rgba(2,136,209,.10)` | DROP → COOL |

### LCD Panels (aligned dengan Artisan `large_lcds.py`)

| LCD | Warna | Data | Artisan Class |
|---|---|---|---|
| Timer | — | MM:SS elapsed | `lcd0` in `LargeMainLCDs` |
| ET LCD | 🟢 Green | Environment Temp °C | `et` style |
| BT LCD | 🔴 Red | Bean Temp °C | `bt` style |
| ΔET LCD | — | Rate of Rise ET | `deltaet` style |
| ΔBT LCD | — | Rate of Rise BT | `deltabt` style |
| DRYING LCD | 🟠 Orange | Phase duration | `LargePhasesLCDs` phase 1 |
| MAILLARD LCD | 🟡 Yellow | Phase duration | `LargePhasesLCDs` phase 2 |
| DEV LCD | 🔴 Red | FC→DROP duration | `LargePhasesLCDs` phase 3 |
| AUC LCD | 🟡 Amber | °C·min | `LargePhasesLCDs` AUC |
| MET LCD | — | Max ET °C | MET marker |

---

## 6. Format File

### .alog (Roast Log — Artisan Compatible)
```json
{
  "version": "1.0",
  "title": "Artisan-Lite Roast",
  "date": "2026-03-10T00:00:00.000Z",
  "roastUUID": "...",
  "modbushost": "192.168.11.3",
  "modbusport": 5000,
  "modbustype": 3,
  "timex": [...],         // waktu dalam menit
  "temp1": [...],         // ET data array
  "temp2": [...],         // BT data array
  "delta1": [...],        // ΔET (RoR)
  "delta2": [...],        // ΔBT (RoR)
  "timeindex": [-1,0,0,0,0,0,0,0],  // 8 event indices
  "specialevents": [...], // event markers
  "auc": 245.12,
  "met": 198.5
}
```

### .aset (Config — Artisan Compatible)
```ini
[artisan]
modbushost = 192.168.11.3
modbusport = 5000
modbustype = 3
modbustimeout = 1.0
modbusretries = 1
modbuswordorderLittle = 1
modbusinputids = [1,2,0,0,0,0,0,0,0,0]
modbusinputregisters = [1000,1000,0,0,0,0,0,0,0,0]
modbusinputcodes = [4,4,3,3,3,3,3,3,3,3]
modbusinputdivs = [1,1,0,0,0,0,0,0,0,0]
modbusinputmodes = ["C","C","C","C","C","C","C","C","C","C"]
samplerate = 1
```

---

## 7. Log Konfigurasi Sistem (OpenWrt Setup)

### A. Fix OPKG Download (Fix IPv6 routing issue)
```bash
sed -i 's/https/http/g' /etc/opkg/distfeeds.conf
echo "151.101.2.132 downloads.openwrt.org" >> /etc/hosts
opkg update
```

### B. Install net2ser (TCP-to-Serial Bridge)
```bash
opkg install net2ser
# Config: bind 0.0.0.0:5000 → /dev/ttyUSB0 @ 9600 8N2
```

### C. Artisan Desktop Config (Macbook)
Menu: **Config → Ports → Modbus**
```
Type    : TCP
Host    : 192.168.11.3
Port    : 5000
Timeout : 1.0
Retries : 1
Input 1 : Device=1, Register=1000, FC=4, Mode=C
Input 2 : Device=2, Register=1000, FC=4, Mode=C
```

> **Catatan**: Parameter `comport` di file `.aset` awalnya `socket://192.168.11.3:5000`.  
> Di macOS harus diubah ke format `IP + Type TCP` karena protokol `socket://` tidak dikenal.

---

## 8. Progress Log

| Tanggal | Sprint | Pencapaian |
|---|---|---|
| 2026-03-08 | S1 | PoC Modbus TCP berhasil baca ET & BT |
| 2026-03-08 | S2 | Kivy UI prototype (deprecated) |
| 2026-03-09 | S3 | Pivot ke HTML/JS — UI v1 Material Design |
| 2026-03-09 | S4 | UI v2 — 7 bug fixes (RESET, tabs, slider, phases, save/load) |
| 2026-03-10 | S5 | Artisan source alignment (timeindex, rect1-4, 10ch, PhasesLCD) |
| 2026-03-10 | S6 | Python Modbus bridge backend (`modbus_to_ws.py`) |
| TBD        | S7 | Android WebView APK (opsional/PWA ready) |

---

## 9. Yang Belum Dikerjakan (TODO)

- [ ] **Android APK**: Bungkus `artisan_lite_ui.html` dengan Android WebView (jika tidak puas dengan PWA)
- [ ] **Auto-detect CHARGE** (via BT drop detection, seperti Artisan `autoChargeFlag`)
- [ ] **Auto DRY / Auto FCs** (seperti Artisan `autoDRYflag` / `autoFCsFlag`)
- [ ] **PID / Burner control** ke mesin via Modbus Write
- [ ] **Extra device** mapping (Ch.3-10) untuk sensor tambahan
