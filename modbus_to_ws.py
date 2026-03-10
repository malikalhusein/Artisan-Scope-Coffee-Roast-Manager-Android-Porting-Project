#!/usr/bin/env python3
"""
modbus_to_ws.py — Artisan-Lite Sprint 6
Modbus TCP → WebSocket Bridge

Membaca data suhu ET & BT dari gateway Modbus TCP (Huawei HG553)
dan broadcast ke artisan_lite_ui.html via WebSocket.

Usage:
    python3 modbus_to_ws.py                  # Default config
    python3 modbus_to_ws.py --host 192.168.11.3 --port 5000 --ws-port 8765
    python3 modbus_to_ws.py --help

Install dependencies:
    pip install pymodbus websockets

Config defaults (matches artisan-scope-master/src/artisanlib/modbusport.py):
    Modbus TCP host : 192.168.11.3
    Modbus TCP port : 5000
    ET : Device 1, Register 1000, FC04, Divider÷10
    BT : Device 2, Register 1000, FC04, Divider÷10
    WebSocket      : ws://0.0.0.0:8765
"""

import asyncio
import json
import logging
import argparse
import sys
import time
from datetime import datetime

# ── Dependencies check ─────────────────────────────────────────────────────────
try:
    from pymodbus.client import AsyncModbusTcpClient
    from pymodbus.framer import FramerType
    from pymodbus.pdu import ExceptionResponse
except ImportError:
    print("ERROR: pymodbus tidak terinstall.")
    print("       Jalankan: pip install pymodbus")
    sys.exit(1)

try:
    import websockets
    # Fallback to older import for Python 3.9/websockets legacy if needed, but standard serve is usually ok
    from websockets.server import serve as ws_serve
except ImportError:
    print("ERROR: websockets tidak terinstall.")
    print("       Jalankan: pip install websockets")
    sys.exit(1)

from typing import Optional

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("artisan-bridge")

# ── Defaults (matches Artisan modbusport.py defaults for our setup) ───────────
DEFAULT_MODBUS_HOST = "192.168.11.3"
DEFAULT_MODBUS_PORT = 5000
DEFAULT_MODBUS_TIMEOUT = 1.0
DEFAULT_WS_HOST = "0.0.0.0"
DEFAULT_WS_PORT = 8765
DEFAULT_SAMPLE_INTERVAL = 1.0  # seconds

# Artisan channels: inputDeviceIds, inputRegisters, inputCodes, inputDivs
# Channel 0 = ET, Channel 1 = BT (matches canvas.py / modbusport.py)
CHANNELS = [
    {"name": "ET", "device_id": 1, "register": 1000, "fc": 4, "div": 10},
    {"name": "BT", "device_id": 2, "register": 1000, "fc": 4, "div": 10},
]

# ── Shared State ───────────────────────────────────────────────────────────────
class AppState:
    """Shared state between Modbus reader and WebSocket broadcaster."""
    connected_ws_clients: set = set()
    modbus_connected: bool = False
    last_et: float = 0.0
    last_bt: float = 0.0
    last_ror_et: float = 0.0
    last_ror_bt: float = 0.0
    error_count: int = 0
    sample_count: int = 0
    et_history: list = []  # for RoR calculation
    bt_history: list = []

state = AppState()

# ── RoR Calculation ────────────────────────────────────────────────────────────
def calculate_ror(history: list, window: int = 5) -> float:
    """Calculate Rate of Rise (°C/min) over the last `window` samples."""
    if len(history) < 2:
        return 0.0
    # Use last `window` readings, each 1 second apart
    recent = history[-window:]
    if len(recent) < 2:
        return 0.0
    delta_temp = recent[-1] - recent[0]
    delta_time_min = (len(recent) - 1) / 60.0
    if delta_time_min == 0:
        return 0.0
    return round(delta_temp / delta_time_min, 1)

# ── Modbus Reader ──────────────────────────────────────────────────────────────
async def read_register(client: AsyncModbusTcpClient, device_id: int, register: int, fc: int) -> Optional[float]:
    """Read a single register from Modbus and return raw value or None on error."""
    try:
        if fc == 4:
            result = await client.read_input_registers(register, count=1, slave=device_id)
        elif fc == 3:
            result = await client.read_holding_registers(register, count=1, slave=device_id)
        else:
            return None

        if result is None or isinstance(result, ExceptionResponse) or result.isError():
            return None
        if not hasattr(result, "registers") or len(result.registers) == 0:
            return None
        return float(result.registers[0])
    except Exception as e:
        log.debug(f"read_register error: {e}")
        return None


async def modbus_reader_loop(args):
    """Main loop: connect to Modbus TCP, poll ET & BT, broadcast via WebSocket."""
    reconnect_delay = 2.0

    while True:
        log.info(f"Menghubungkan ke Modbus TCP {args.host}:{args.port} ...")
        client = AsyncModbusTcpClient(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            retries=1,
        )

        try:
            await client.connect()

            if client.connected:
                state.modbus_connected = True
                state.error_count = 0
                log.info(f"✅ Modbus TCP terhubung ke {args.host}:{args.port}")

                while client.connected:
                    et_raw = await read_register(client, CHANNELS[0]["device_id"], CHANNELS[0]["register"], CHANNELS[0]["fc"])
                    bt_raw = await read_register(client, CHANNELS[1]["device_id"], CHANNELS[1]["register"], CHANNELS[1]["fc"])

                    if et_raw is not None and bt_raw is not None:
                        state.last_et = round(et_raw / CHANNELS[0]["div"], 1)
                        state.last_bt = round(bt_raw / CHANNELS[1]["div"], 1)
                        state.error_count = 0

                        # Rolling history for RoR calculation
                        state.et_history.append(state.last_et)
                        state.bt_history.append(state.last_bt)
                        if len(state.et_history) > 30:  # keep last 30 readings
                            state.et_history.pop(0)
                            state.bt_history.pop(0)

                        state.last_ror_et = calculate_ror(state.et_history)
                        state.last_ror_bt = calculate_ror(state.bt_history)
                        state.sample_count += 1

                        # Build payload — matches Artisan data structure
                        payload = {
                            "type": "data",
                            "ts": time.time(),
                            "et": state.last_et,
                            "bt": state.last_bt,
                            "ror_et": state.last_ror_et,
                            "ror_bt": state.last_ror_bt,
                            "connected": True,
                        }
                        await broadcast(payload)
                        log.info(f"[{state.sample_count:04d}] ET={state.last_et:.1f}°C  BT={state.last_bt:.1f}°C  ΔBT={state.last_ror_bt:.1f}°/min")

                    else:
                        state.error_count += 1
                        log.warning(f"⚠️  Baca gagal (error #{state.error_count})")
                        if state.error_count >= 5:
                            log.error("❌ Terlalu banyak error, reconnect...")
                            break

                    await asyncio.sleep(args.sample)

            else:
                log.warning(f"⚠️  Gagal terhubung ke {args.host}:{args.port}")

        except Exception as e:
            log.error(f"❌ Modbus error: {e}")
        finally:
            state.modbus_connected = False
            try:
                client.close()
            except Exception:
                pass

            # Broadcast disconnect status to all UI clients
            await broadcast({"type": "status", "connected": False, "message": "Modbus disconnected — retrying..."})
            log.info(f"Reconnect dalam {reconnect_delay}s ...")
            await asyncio.sleep(reconnect_delay)


# ── WebSocket Broadcaster ──────────────────────────────────────────────────────
async def broadcast(payload: dict):
    """Send JSON payload to all connected WebSocket clients."""
    if not state.connected_ws_clients:
        return
    msg = json.dumps(payload)
    # Fire-and-forget to all clients; remove dead connections
    dead = set()
    for ws in state.connected_ws_clients.copy():
        try:
            await ws.send(msg)
        except Exception:
            dead.add(ws)
    state.connected_ws_clients -= dead


async def ws_handler(websocket):
    """Handle new WebSocket client connection."""
    client_addr = websocket.remote_address
    log.info(f"🔌 WebSocket client connect: {client_addr}")
    state.connected_ws_clients.add(websocket)

    # Send current status immediately on connect
    await websocket.send(json.dumps({
        "type": "hello",
        "connected": state.modbus_connected,
        "et": state.last_et,
        "bt": state.last_bt,
        "ror_et": state.last_ror_et,
        "ror_bt": state.last_ror_bt,
        "message": "Artisan-Lite Bridge v1.0 — Sprint 6",
    }))

    try:
        # Keep connection open; process incoming messages from UI
        async for msg in websocket:
            try:
                data = json.loads(msg)
                cmd = data.get("cmd", "")
                if cmd == "ping":
                    await websocket.send(json.dumps({"type": "pong", "ts": time.time()}))
                elif cmd == "get_config":
                    await websocket.send(json.dumps({
                        "type": "config",
                        "channels": CHANNELS,
                        "sample": DEFAULT_SAMPLE_INTERVAL,
                    }))
                else:
                    log.debug(f"Unknown cmd from {client_addr}: {cmd}")
            except json.JSONDecodeError:
                pass
    except Exception as e:
        log.debug(f"WebSocket handler error: {e}")
    finally:
        state.connected_ws_clients.discard(websocket)
        log.info(f"🔌 WebSocket client disconnect: {client_addr}")


# ── Main ───────────────────────────────────────────────────────────────────────
async def main(args):
    """Run Modbus reader and WebSocket server concurrently."""
    log.info("=" * 60)
    log.info(" Artisan-Lite Modbus → WebSocket Bridge (Sprint 6)")
    log.info("=" * 60)
    log.info(f" Modbus TCP  : {args.host}:{args.port}")
    log.info(f" WebSocket   : ws://{DEFAULT_WS_HOST}:{args.ws_port}")
    log.info(f" Sampling    : {args.sample}s")
    log.info(f" ET Channel  : Device {CHANNELS[0]['device_id']}, Reg {CHANNELS[0]['register']}, FC0{CHANNELS[0]['fc']}, ÷{CHANNELS[0]['div']}")
    log.info(f" BT Channel  : Device {CHANNELS[1]['device_id']}, Reg {CHANNELS[1]['register']}, FC0{CHANNELS[1]['fc']}, ÷{CHANNELS[1]['div']}")
    log.info("=" * 60)
    log.info(" Buka artisan_lite_ui.html di Chrome, tekan [ON] untuk connect")
    log.info("=" * 60)

    ws_server = await ws_serve(ws_handler, DEFAULT_WS_HOST, args.ws_port)
    log.info(f"✅ WebSocket server aktif di ws://localhost:{args.ws_port}")

    # Run both concurrently
    await asyncio.gather(
        modbus_reader_loop(args),
        ws_server.wait_closed(),
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Artisan-Lite Modbus→WebSocket Bridge (Sprint 6)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python3 modbus_to_ws.py
  python3 modbus_to_ws.py --host 192.168.11.3 --port 5000
  python3 modbus_to_ws.py --sample 2 --ws-port 9000
  python3 modbus_to_ws.py --et-device 1 --et-reg 1000 --bt-device 2 --bt-reg 1000
        """
    )
    parser.add_argument("--host",      default=DEFAULT_MODBUS_HOST, help=f"Modbus TCP host (default: {DEFAULT_MODBUS_HOST})")
    parser.add_argument("--port",      type=int, default=DEFAULT_MODBUS_PORT, help=f"Modbus TCP port (default: {DEFAULT_MODBUS_PORT})")
    parser.add_argument("--timeout",   type=float, default=DEFAULT_MODBUS_TIMEOUT, help=f"Modbus timeout detik (default: {DEFAULT_MODBUS_TIMEOUT})")
    parser.add_argument("--ws-port",   type=int, default=DEFAULT_WS_PORT, help=f"WebSocket port (default: {DEFAULT_WS_PORT})")
    parser.add_argument("--sample",    type=float, default=DEFAULT_SAMPLE_INTERVAL, help=f"Interval sampling detik (default: {DEFAULT_SAMPLE_INTERVAL})")
    parser.add_argument("--et-device", type=int, default=1, help="ET Modbus Unit ID (default: 1)")
    parser.add_argument("--et-reg",    type=int, default=1000, help="ET Register address (default: 1000)")
    parser.add_argument("--bt-device", type=int, default=2, help="BT Modbus Unit ID (default: 2)")
    parser.add_argument("--bt-reg",    type=int, default=1000, help="BT Register address (default: 1000)")
    parser.add_argument("--debug",     action="store_true", help="Enable debug logging")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Apply custom channel config from args
    CHANNELS[0]["device_id"] = args.et_device
    CHANNELS[0]["register"]  = args.et_reg
    CHANNELS[1]["device_id"] = args.bt_device
    CHANNELS[1]["register"]  = args.bt_reg

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        log.info("\n👋 Bridge dihentikan.")
