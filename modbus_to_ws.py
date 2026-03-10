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
    try:
        from websockets.server import serve as ws_serve
    except ImportError:
        from websockets import serve as ws_serve
except ImportError:
    print("ERROR: websockets tidak terinstall.")
    print("       Jalankan: pip install websockets")
    sys.exit(1)

from typing import Optional, Tuple

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
# Note: 'div' here refers to the INDEX sent by the UI (0=none/1, 1=÷10, 2=÷100)
CHANNELS = [
    {"name": "ET", "device_id": 1, "register": 1000, "fc": 4, "div": 0},
    {"name": "BT", "device_id": 2, "register": 1000, "fc": 4, "div": 0},
]

def get_divisor(div_index: int) -> int:
    """Map UI divider index to actual numeric divisor."""
    if div_index == 1: return 10
    if div_index == 2: return 100
    return 1 # default for index 0 or invalid indices

# ── Shared State ───────────────────────────────────────────────────────────────
class AppState:
    """Shared state between Modbus reader and WebSocket broadcaster."""
    connected_ws_clients: set = set()
    modbus_connected: bool = False
    simulate: bool = False
    last_et: float = 25.0
    last_bt: float = 25.0
    last_ror_et: float = 0.0
    last_ror_bt: float = 0.0
    error_count: int = 0
    sample_count: int = 0
    start_time: float = time.time()
    et_history: list = []
    bt_history: list = []

state = AppState()

# ── Simulation Logic ───────────────────────────────────────────────────────────
def get_simulated_data():
    """Generate S-curve data similar to UI demo mode."""
    elapsed = (time.time() - state.start_time) / 60.0
    # Simple simulated roast
    if elapsed < 1.5:
        state.last_et += 0.4; state.last_bt += 0.05
    elif elapsed < 5:
        state.last_et += 0.2; state.last_bt += 0.15
    elif elapsed < 10:
        state.last_et += 0.05; state.last_bt += 0.1
    else:
        state.last_et -= 0.1; state.last_bt += 0.02

    state.last_et = min(250, state.last_et)
    state.last_bt = min(230, state.last_bt)
    return state.last_et, state.last_bt

# ── RoR Calculation ────────────────────────────────────────────────────────────
def calculate_ror(history: list, window: int = 5) -> float:
    """Calculate Rate of Rise (°C/min) over the last `window` samples."""
    if len(history) < 2:
        return 0.0
    recent = history[-window:]
    if len(recent) < 2:
        return 0.0
    delta_temp = recent[-1] - recent[0]
    delta_time_min = (len(recent) - 1) / 60.0
    return round(delta_temp / delta_time_min, 1) if delta_time_min > 0 else 0.0

# ── Modbus Reader ──────────────────────────────────────────────────────────────
async def read_register(client: AsyncModbusTcpClient, device_id: int, register: int, fc: int) -> Tuple[Optional[float], str]:
    """Read a single register from Modbus. Returns (value, status_message)."""
    try:
        if fc == 4:
            result = await client.read_input_registers(register, count=1, slave=device_id)
        elif fc == 3:
            result = await client.read_holding_registers(register, count=1, slave=device_id)
        else:
            return None, "Invalid FC"

        if result is None:
            return None, "No response (Timeout)"
        if isinstance(result, ExceptionResponse):
            return None, f"Modbus Error: {result.original_code} ({result})"
        if hasattr(result, "isError") and result.isError():
            return None, f"Modbus Error: {result}"
        
        if not hasattr(result, "registers") or len(result.registers) == 0:
            return None, "Empty registers"
        
        return float(result.registers[0]), "OK"
    except Exception as e:
        log.debug(f"read_register(Dev={device_id}, Reg={register}, FC={fc}) error: {e}")
        return None, str(e)


async def modbus_reader_loop(args):
    """Main loop: poll Modbus TCP or generate simulation data."""
    reconnect_delay = 2.0
    state.start_time = time.time()

    while True:
        if state.simulate:
            log.info("🚀 SIMULATION MODE ACTIVE")
            while state.simulate:
                et, bt = get_simulated_data()
                state.et_history.append(et)
                state.bt_history.append(bt)
                if len(state.et_history) > 60:
                    state.et_history.pop(0); state.bt_history.pop(0)

                state.last_ror_bt = calculate_ror(state.bt_history)
                payload = {
                    "type": "data", "ts": time.time(), "et": et, "bt": bt,
                    "ror_et": calculate_ror(state.et_history), "ror_bt": state.last_ror_bt,
                    "connected": True, "message": "SIMULATION MODE"
                }
                await broadcast(payload)
                await asyncio.sleep(args.sample)
            continue

        log.info(f"Menghubungkan ke Modbus TCP {args.host}:{args.port} ...")
        client = AsyncModbusTcpClient(host=args.host, port=args.port, timeout=args.timeout, retries=1)

        try:
            await client.connect()
            if client.connected:
                state.modbus_connected = True; state.error_count = 0
                log.info(f"✅ Modbus TCP terhubung ke {args.host}:{args.port}")

                while client.connected and not state.simulate:
                    # Read ET & BT based on CURRENT CHANNELS (allow dynamic updates)
                    et_raw, et_status = await read_register(client, CHANNELS[0]["device_id"], CHANNELS[0]["register"], CHANNELS[0]["fc"])
                    bt_raw, bt_status = await read_register(client, CHANNELS[1]["device_id"], CHANNELS[1]["register"], CHANNELS[1]["fc"])

                    if et_raw is not None and bt_raw is not None:
                        # Use mapped divisors
                        div0 = get_divisor(CHANNELS[0]["div"])
                        div1 = get_divisor(CHANNELS[1]["div"])
                        state.last_et = round(et_raw / div0, 1)
                        state.last_bt = round(bt_raw / div1, 1)
                        state.error_count = 0
                        state.et_history.append(state.last_et)
                        state.bt_history.append(state.last_bt)
                        if len(state.et_history) > 60:
                            state.et_history.pop(0); state.bt_history.pop(0)

                        state.last_ror_bt = calculate_ror(state.bt_history)
                        state.sample_count += 1
                        await broadcast({
                            "type": "data", "ts": time.time(), "et": state.last_et, "bt": state.last_bt,
                            "ror_et": calculate_ror(state.et_history), "ror_bt": state.last_ror_bt,
                            "connected": True
                        })
                        log.info(f"[{state.sample_count:04d}] ET={state.last_et:.1f} BT={state.last_bt:.1f} ΔBT={state.last_ror_bt:.1f}")
                    else:
                        state.error_count += 1
                        # Detailed error message for debugging
                        detail = f"ET:{et_status} | BT:{bt_status}"
                        err_msg = f"Modbus Read Failed (#{state.error_count})"
                        log.warning(f"⚠️ {err_msg} -> {detail}")
                        await broadcast({"type": "status", "connected": True, "message": detail})
                        if state.error_count >= 10: break

                    await asyncio.sleep(args.sample)
            else:
                log.warning(f"⚠️ Gagal konek {args.host}:{args.port}")
        except Exception as e:
            log.error(f"❌ Modbus error: {e}")
        finally:
            state.modbus_connected = False
            try: client.close()
            except: pass
            if not state.simulate:
                await broadcast({"type": "status", "connected": False, "message": "Modbus disconnected"})
                await asyncio.sleep(reconnect_delay)


# ── WebSocket Broadcaster ──────────────────────────────────────────────────────
async def broadcast(payload: dict):
    """Send JSON payload to all connected WebSocket clients."""
    if not state.connected_ws_clients: return
    msg = json.dumps(payload)
    dead = set()
    for ws in state.connected_ws_clients.copy():
        try: await ws.send(msg)
        except: dead.add(ws)
    state.connected_ws_clients -= dead


async def ws_handler(websocket):
    """Handle new WebSocket client connection."""
    client_addr = websocket.remote_address
    log.info(f"🔌 WebSocket client connect: {client_addr}")
    state.connected_ws_clients.add(websocket)

    await websocket.send(json.dumps({
        "type": "hello", "connected": state.modbus_connected, "simulate": state.simulate,
        "et": state.last_et, "bt": state.last_bt, "message": f"Bridge v1.1 - {'SIMULATING' if state.simulate else 'LIVE'}"
    }))

    try:
        async for msg in websocket:
            try:
                data = json.loads(msg)
                cmd = data.get("cmd", "")
                if cmd == "ping": await websocket.send(json.dumps({"type": "pong"}))
                elif cmd == "set_simulate":
                    state.simulate = bool(data.get("value", False))
                    log.info(f"Simulation mode set to: {state.simulate}")
                elif cmd == "update_config":
                    # Update CHANNELS dynamically from UI
                    new_channels = data.get("channels", [])
                    if len(new_channels) >= 2:
                        CHANNELS[0].update(new_channels[0])
                        CHANNELS[1].update(new_channels[1])
                        log.info(f"Config updated: ET=Dev{CHANNELS[0]['device_id']} BT=Dev{CHANNELS[1]['device_id']}")
                elif cmd == "get_config":
                    await websocket.send(json.dumps({"type": "config", "channels": CHANNELS}))
            except: pass
    finally:
        state.connected_ws_clients.discard(websocket)
        log.info(f"🔌 WebSocket client disconnect: {client_addr}")


# ── Main ───────────────────────────────────────────────────────────────────────
async def main(args):
    state.simulate = args.simulate
    log.info("=" * 60)
    log.info(f" Artisan-Lite Bridge v1.1 {'[SIMULATION]' if state.simulate else ''}")
    log.info(f" Modbus TCP  : {args.host}:{args.port}")
    log.info(f" WebSocket   : ws://0.0.0.0:{args.ws_port}")
    log.info("=" * 60)

    ws_server = await ws_serve(ws_handler, "0.0.0.0", args.ws_port)
    await asyncio.gather(modbus_reader_loop(args), ws_server.wait_closed())


def parse_args():
    parser = argparse.ArgumentParser(description="Artisan-Lite Bridge v1.1")
    parser.add_argument("--host",      default=DEFAULT_MODBUS_HOST)
    parser.add_argument("--port",      type=int, default=DEFAULT_MODBUS_PORT)
    parser.add_argument("--timeout",   type=float, default=DEFAULT_MODBUS_TIMEOUT)
    parser.add_argument("--ws-port",   type=int, default=DEFAULT_WS_PORT)
    parser.add_argument("--sample",    type=float, default=DEFAULT_SAMPLE_INTERVAL)
    parser.add_argument("--simulate",  action="store_true", help="Jalankan data simulasi (tanpa hardware)")
    parser.add_argument("--et-device", type=int, default=1)
    parser.add_argument("--et-reg",    type=int, default=1000)
    parser.add_argument("--bt-device", type=int, default=2)
    parser.add_argument("--bt-reg",    type=int, default=1000)
    parser.add_argument("--debug",     action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    CHANNELS[0].update({"device_id": args.et_device, "register": args.et_reg})
    CHANNELS[1].update({"device_id": args.bt_device, "register": args.bt_reg})
    if args.debug: logging.getLogger().setLevel(logging.DEBUG)
    try: asyncio.run(main(args))
    except KeyboardInterrupt: log.info("\n👋 Bridge dihentikan.")
