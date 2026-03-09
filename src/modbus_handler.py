from pymodbus.client import ModbusTcpClient
import time

class ModbusHandler:
    """
    Dedicated background service for managing the Modbus TCP connection
    to the OpenWrt router bridge, decoupled from the Kivy UI thread.
    """
    def __init__(self):
        self.client = None
        self.is_connected = False
        
        # Connection params
        self.ip = "192.168.11.3"
        self.port = 5000
        
        # Modbus registers (Default ET=Device1/Reg1000, BT=Device2/Reg1000)
        self.et_slave = 1
        self.et_reg = 1000
        self.bt_slave = 2
        self.bt_reg = 1000
        
    def configure(self, ip, port, et_slave, et_reg, bt_slave, bt_reg):
        """Updates connection parameters before connecting."""
        self.ip = ip
        self.port = int(port)
        self.et_slave = int(et_slave)
        self.et_reg = int(et_reg)
        self.bt_slave = int(bt_slave)
        self.bt_reg = int(bt_reg)

    def connect(self):
        """Attempts connection synchronously. Run this in a thread from Kivy!"""
        try:
            self.client = ModbusTcpClient(self.ip, port=self.port, timeout=2.0)
            if self.client.connect():
                self.is_connected = True
                return True, "Connected successfully"
            else:
                self.is_connected = False
                return False, "Connection Refused/Timeout"
        except Exception as e:
            self.is_connected = False
            return False, str(e)

    def disconnect(self):
        """Closes the Modbus socket."""
        self.is_connected = False
        if self.client:
            self.client.close()
            self.client = None

    def read_temperatures(self):
        """
        Polls the registers for ET and BT.
        Returns a tuple: (et_celsius, bt_celsius, error_msg)
        Scales the returned raw integer down by 10 (e.g. 2055 -> 205.5)
        """
        if not self.is_connected or not self.client or not self.client.is_socket_open():
            return None, None, "Socket closed or disconnected"
            
        try:
            # Read ET (Function Code 4)
            et_res = self.client.read_input_registers(address=self.et_reg, count=1, slave=self.et_slave)
            if et_res.isError():
                return None, None, "ET Modbus Read Error"
            et_scaled = et_res.registers[0] / 10.0
            
            # Read BT (Function Code 4)
            bt_res = self.client.read_input_registers(address=self.bt_reg, count=1, slave=self.bt_slave)
            if bt_res.isError():
                return None, None, "BT Modbus Read Error"
            bt_scaled = bt_res.registers[0] / 10.0
            
            return et_scaled, bt_scaled, None
            
        except Exception as e:
            return None, None, f"Modbus Exception: {e}"
