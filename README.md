# ☕ Artisan-Lite — Raga Roastery IoT Modbus Gateway

> **Artisan-Lite** adalah versi mobile-first dari [Artisan Roaster Scope](https://github.com/artisan-roaster-scope/artisan) yang dirancang khusus untuk monitoring & logging mesin sangrai kopi 1kg secara nirkabel via Modbus TCP/RTU Gateway.

---

## 🏗️ Arsitektur Sistem

```
[Mesin Roaster 1kg]
       │ RS485 / Modbus RTU (9600 8N2)
       ▼
[FTDI FT232R USB-RS485]
       │ USB
       ▼
[Huawei HG553 — OpenWrt 23.05.5]  ←── net2ser (TCP→RTU bridge)
 IP: 192.168.11.3:5000 (Modbus TCP)
       │ Wi-Fi 802.11b/g
       ▼
[Infinix XPad / Browser]  ←── artisan_lite_ui.html (WebView / Browser)
[Macbook / Artisan Desktop]  ←── .aset config compatibility
```

---

## 📋 Spesifikasi Hardware

| Komponen | Detail |
|---|---|
| **Gateway / Router** | Huawei EchoLife HG553 (RAM 64MB) |
| **OS Gateway** | OpenWrt 23.05.5 (Kernel 5.15.167) |
| **Konverter Serial** | USB-RS485 Adapter (FTDI FT232R) |
| **Mesin Roasting** | Kapasitas 1kg — Vegas (Mesin Kopi Jember) |
| **Tablet Client** | Infinix XPad (Infinix X20, Helio G99) |
| **Protocol** | Modbus TCP (Wi-Fi) → Modbus RTU (RS485) |
| **Baudrate RTU** | 9600 8N2 |

---

## 🎨 Teknologi UI — HTML/JS/CSS (WebView)

Setelah melalui beberapa iterasi desain, proyek ini **pivot dari Python/Kivy ke single-file HTML/JS/CSS** untuk mendapatkan:
- Preview instan di browser tanpa instalasi
- Desain neomorphic premium dengan Chart.js
- Kompatibilitas penuh sebagai Android WebView APK

**File utama:** [`artisan_lite_ui.html`](./artisan_lite_ui.html)

---

## ✅ Fitur yang Telah Diimplementasikan

### 🖥️ UI & Layout (v2 — Artisan Source-Aligned)
- [x] Dark neomorphic theme (`#141b22` background)
- [x] Top navigation bar (clock, status, phase indicators, buttons)
- [x] LCD-style side panels: ET (green), BT (red), ΔET, ΔBT, AUC, MET
- [x] **Phases LCD panel**: DRYING / MAILLARD / DEV phase timers — *aligned dengan Artisan `LargePhasesLCDs`*
- [x] Burner control slider (vertikal, kiri panel, gradient api 🔥)
- [x] Tombol RESET (amber)

### 📈 Grafik Real-Time (Chart.js)
- [x] Plot ET & BT kurva suhu real-time
- [x] Rate of Rise (RoR / ΔBT) pada sumbu Y kanan
- [x] **4 Phase bands on graph** — *aligned dengan Artisan palette `rect1`-`rect4`*:
  - `rect1` 🟠 Drying (CHARGE → DRY END)
  - `rect2` 🟡 Maillard (DRY END → FCs)
  - `rect3` 🟢 Finishing/Dev (FCs → DROP)
  - `rect4` 🔵 Cooling (DROP → end)
- [x] **8 Event markers** — *aligned dengan Artisan `canvas.py` timeindex[0..7]*:
  `CHARGE`, `DRY END`, `FC START`, `FC END`, `SC START`, `SC END`, `DROP`, `COOL`
- [x] AUC (Area Under Curve) & MET (Max ET) calculation
- [x] Scalable Y-axis (Temp & RoR range configurable)

### ⚙️ Konfigurasi Modal (3 Tab)
- [x] **Modbus/TCP Tab**: Type (RTU/ASCII/Binary/TCP/UDP), Host, Port, Timeout, Retries
- [x] **Device Assignment Tab** — *aligned dengan Artisan `modbusport.py` channels=10*:
  - Ch.1 (ET): Unit ID, Register, FC01-FC04, Divider (0=none/÷10/÷100), Mode (°C/°F)
  - Ch.2 (BT): Unit ID, Register, FC01-FC04, Divider, Mode
  - Ch.3-10 Extra channels
  - Sampling interval & Word Order (little/big endian)
- [x] **Curves Tab**: Toggle ET/BT/RoR visibility + color picker + Y-axis scaling

### 💾 Save / Load
- [x] **Save Log** → `.alog` (JSON, Artisan-compatible) + `.csv`  
- [x] **Load Log** → Rekonstruksi grafik dari file `.alog`
- [x] **Save Config `.aset`** → Artisan-compatible key names (`modbusinputids`, `modbusinputregisters`, dll.)
- [x] **Load Config `.aset`** → Parse & restore semua 10 channel config

---

## 🗺️ Status Pengembangan

| Sprint | Status | Keterangan |
|---|---|---|
| Sprint 1 — PoC Modbus | ✅ SELESAI | Python script berhasil baca ET/BT |
| Sprint 2 — Kivy UI | ✅ SELESAI | Prototype UI Android (deprecated) |
| Sprint 3 — HTML UI v1 | ✅ SELESAI | Material Design dark theme |
| Sprint 4 — HTML UI v2 | ✅ SELESAI | Bug fixes, 7 issue resolved |
| Sprint 5 — Artisan Alignment | ✅ SELESAI | Source code lookup & alignment |
| Sprint 6 — Backend Integration | ✅ SELESAI | Python Modbus-to-WebSocket bridge |
| Sprint 7 — Android APK | ⏳ PENDING | WebView wrapper (Opsional, saat ini pakai PWA) |

---

## 📁 Struktur File

```
Raga Artisan Scope Project/
├── artisan_lite_ui.html        ← MAIN UI (buka di browser / WebView)
├── modbus_to_ws.py             ← Backend Bridge (Sprint 6)
├── requirements.txt            ← Python dependencies (pymodbus, websockets)
├── README.md                   ← Dokumen ini
├── PROJECT_DOCUMENTATION.md    ← Spesifikasi teknis lengkap
├── Setup & Installation Guide.md  ← Panduan instalasi
├── artisan-scope-master/       ← Artisan source code (referensi)
│   └── src/artisanlib/
│       ├── canvas.py           ← timeindex, phase bands
│       ├── modbusport.py       ← Modbus channels config
│       ├── large_lcds.py       ← LCD panel layout
│       ├── phases.py           ← Phase dialog
│       └── colors.py           ← Palette keys (rect1-rect4)
└── venv/                       ← Python venv (legacy Kivy)
```

---

## 🚀 Quick Start

### Preview di Browser (paling mudah)
```bash
# Cukup buka file HTML di browser:
open artisan_lite_ui.html
# atau double-click dari Finder
```

### Preview di Tablet (Android WebView)
1. Transfer `artisan_lite_ui.html` ke tablet (USB / Google Drive)
2. Buka dengan browser tablet (Chrome / Samsung Internet)
3. Sambungkan tablet ke Wi-Fi Gateway (SSID mesin roasting)
4. Tekan **ON** → **START** untuk mulai sesi roasting

---

## 📚 Dokumentasi Lengkap
- [`PROJECT_DOCUMENTATION.md`](./PROJECT_DOCUMENTATION.md) — Spesifikasi hardware, topologi, Modbus config
- [`Setup & Installation Guide.md`](./Setup%20%26%20Installation%20Guide.md) — Panduan langkah demi langkah
