# Artisan-Lite Android Port (Raga Roastery IoT Modbus Gateway)

## Overview
This project is an Android port ("Artisan-Lite") of the popular [Artisan Roaster Scope](https://github.com/artisan-roaster-scope/artisan) software. The goal is to provide a touch-optimized, standalone tablet application to control and monitor a custom 1kg coffee roaster via a wireless **Modbus TCP/RTU Gateway**.

This application is built using **Python and Kivy** to ensure cross-platform compatibility and direct access to native Modbus libraries (`pymodbus`). It communicates over Wi-Fi with an OpenWrt router (Huawei HG553) acting as a transparent network bridge to the roaster's serial Modbus interface.

## Quick Specs
- **Client App:** Python + Kivy (Android APK via Buildozer, or Pydroid 3 for testing).
- **Communication Protocol:** Modbus TCP (over Wi-Fi) ➔ Modbus RTU (over RS485).
- **Control Hub (Gateway):** Huawei EchoLife HG553 running OpenWrt 23.05.5.
- **Roaster:** Custom 1kg (Vegas - Mesin Kopi Jember).
- **Tablet:** Infinix XPad (Helio G99).

## Key Features
- **Wireless Connectivity**: Fully decoupled control via OpenWrt TCP-to-Serial proxy (`net2ser`).
- **Real-Time Data**: Accurate polling of Bean Temperature (BT) and Environment Temperature (ET) via Modbus `Read Input Registers` (`FC04`).
- **Artisan Ecosystem Compatibility**:
  - Full support for reading/writing original Artisan `.aset` configuration files.
  - Generates compatible `.json`/`.csv` roast profiles for analysis on the Artisan Desktop app.
- **Mobile First**: Large touch targets and Material Design philosophy for easy interaction while roasting.

## Testing Information
You can find the Proof of Concept test script (`poc_modbus_test.py`) in the root directory. To run this script:
1. Transfer the `.py` script to your Android tablet.
2. Install [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) from the Google Play Store.
3. Use the Pydroid "Pip" menu to install `kivy` and `pymodbus`.
4. Run the script while connected to the Gateway's Wi-Fi network.

## Documentation
- Refer to `PROJECT_DOCUMENTATION.md` for deep-dive technical specifications detailing the hardware topology, OpenWrt configurations, and Artisan/Modbus setup.
- Refer to the system `brain/task.md` for sprint progression and task tracking.
# Artisan-Scope-Coffee-Roast-Manager-Android-Porting-Project
