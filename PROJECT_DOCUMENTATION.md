# 📖 DOKUMENTASI PROYEK: RAGA ROASTERY IoT MODBUS GATEWAY

## 1. Deskripsi Proyek
Proyek "Artisan-Lite Android Port" bertujuan untuk mengubah router lawas (Huawei HG553) menjadi sebuah **Industrial-grade Modbus TCP/RTU Gateway**. Sistem ini berfungsi untuk menjembatani komunikasi data serial (Modbus RTU) dari sensor suhu (Thermocouple ET & BT) pada mesin sangrai kopi ke antarmuka perangkat lunak Artisan Scope (Macbook) dan Smartphone (Android) sepenuhnya secara nirkabel (Wi-Fi).

Aplikasi "Artisan-Lite" dibangun menggunakan Python dan Kivy untuk tujuan *standalone monitoring* dan *logging* mesin roaster di atas tablet Android.

## 2. Spesifikasi Perangkat Keras (Hardware)
* **Router / Gateway:** Huawei EchoLife HG553 (RAM 64MB)
* **Sistem Operasi:** OpenWrt 23.05.5 (Kernel 5.15.167)
* **Konverter Serial:** USB to RS485 Adapter (Chipset: FTDI FT232R)
* **Mesin Roasting:** Kapasitas 1kg (Vegas - Mesin Kopi Jember)
* **Perangkat Tambahan (Rencana):** Active USB Hub, TP-Link WN722N V1 (Atheros AR9271) untuk modul Wi-Fi eksternal, dan USB Flashdisk untuk Swap RAM.
* **Perangkat Klien (Tablet):** Infinix XPad (Infinix X20, Helio G99 chipset).

## 3. Parameter Komunikasi (Modbus RTU)
* **Baudrate:** 9600
* **Data Bits:** 8
* **Parity:** None (N)
* **Stop Bits:** 2
* *(Format: 9600 8N2)*

**Alamat Register Suhu:**
* **ET (Environment Temp):** Device ID 1, Register 1000, Function Code 4 (Read Input Registers).
* **BT (Bean Temp):** Device ID 2, Register 1000, Function Code 4 (Read Input Registers).

## 4. Topologi Jaringan & Sistem
* **IP Address Gateway (Huawei HG553):** `192.168.11.3` (Statis)
* **Port Gateway Modbus TCP:** `5000`

**Proses Kerja Topologi:**
Sistem beroperasi menggunakan protokol pengalamatan TCP/IP. Aplikasi klien (Artisan di Macbook atau Aplikasi Kivy Android) terhubung ke jaringan Wi-Fi yang sama dengan Huawei HG553. Klien mengirimkan paket **Modbus TCP** ke `192.168.11.3:5000`. Router secara cerdas mengubah paket TCP tersebut menjadi sinyal listrik **Modbus RTU** beserta perhitungan matematika keamanannya (CRC) (menggunakan layanan `net2ser`), lalu mengirimkannya melalui port fisik `/dev/ttyUSB0` ke mesin roaster.

---

## 5. Log Konfigurasi Sistem (Langkah demi Langkah)

### A. Perbaikan Masalah Unduhan OPKG (Bypass IPv6 pada OpenWrt)
Karena router mengalami isu routing IPv6 (*"Operation not permitted"* / *wget returned 4*), unduhan *repository* diarahkan paksa menggunakan IPv4 dengan memodifikasi file *hosts* dan mengganti HTTPS menjadi HTTP.

```bash
sed -i 's/https/http/g' /etc/opkg/distfeeds.conf
echo "151.101.2.132 downloads.openwrt.org" >> /etc/hosts
opkg update
```

### B. Konfigurasi Klien (Client Setup) - Artisan Desktop

Konfigurasi asli untuk Artisan Scope (Macbook / PC) yang tersimpan di dalam file *Settingan RAGA JOSS wirles.aset*.  Parameter vital di menu Config -> Port -> Modbus:

*   **Type:** TCP
*   **Host:** `192.168.11.3`
*   **Port:** `5000`
*   **Timeout:** `1.0`
*   **Input 1 (ET):** Device 1, Register 1000, Function 4, Mode C, Decode uInt16.
*   **Input 2 (BT):** Device 2, Register 1000, Function 4, Mode C, Decode uInt16.

*(Catatan Analisis macOS):* Parameter `comport` pada file `.aset` awalnya tertulis `socket://192.168.11.3:5000`. macOS tidak mengenali protokol `socket://` secara langsung sehingga memunculkan error *"protocol 'socket' not known"*. Solusinya adalah mengubah parameter menjadi sekadar IP Host dan Type `TCP`.

### C. Konfigurasi Aplikasi Klien (Modbus Android / Pydroid 3 PoC)

*   **IP / Host:** `192.168.11.3`
*   **Port:** `5000`
*   **Protocol:** Modbus TCP (atau TCP/IP)
*   **Function Code:** FC04 (Read Input Registers)
*   **Slave / Device ID:** 1 (ET) atau 2 (BT)
*   **Register Address:** 1000
