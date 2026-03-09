import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from pymodbus.client import ModbusTcpClient
import threading
import time

# Matplotlib setup for Kivy
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

# Set standard mobile-friendly window size for testing on desktop
Window.size = (400, 750)

class ArtisanLitePoC(App):
    def build(self):
        self.modbus_client = None
        self.is_connected = False
        self.poll_event = None
        
        # Data Arrays for Graphing
        self.time_data = [] # X-axis (time in seconds)
        self.et_data = []   # Y1-axis (Environment Temp)
        self.bt_data = []   # Y2-axis (Bean Temp)
        self.start_time = None
        
        # Main Layout
        self.root = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # --- TITLE ---
        self.root.add_widget(Label(
            text='Artisan-Lite: Modbus PoC',
            size_hint_y=None, height=40,
            font_size='20sp', bold=True
        ))
        
        # --- NETWORK CONFIGURATION ---
        net_grid = GridLayout(cols=2, size_hint_y=None, height=70, spacing=2)
        net_grid.add_widget(Label(text='IP Address:'))
        self.ip_input = TextInput(text='192.168.11.3', multiline=False)
        net_grid.add_widget(self.ip_input)
        net_grid.add_widget(Label(text='Port (TCP):'))
        self.port_input = TextInput(text='5000', multiline=False, input_filter='int')
        net_grid.add_widget(self.port_input)
        self.root.add_widget(net_grid)
        
        # --- MODBUS CONFIGURATION ---
        modbus_grid = GridLayout(cols=2, size_hint_y=None, height=140, spacing=2)
        modbus_grid.add_widget(Label(text='ET Slave / Reg:'))
        
        et_box = BoxLayout(orientation='horizontal')
        self.et_slave_input = TextInput(text='1', multiline=False, input_filter='int', size_hint_x=0.3)
        self.et_reg_input = TextInput(text='1000', multiline=False, input_filter='int')
        et_box.add_widget(self.et_slave_input)
        et_box.add_widget(self.et_reg_input)
        modbus_grid.add_widget(et_box)
        
        modbus_grid.add_widget(Label(text='BT Slave / Reg:'))
        bt_box = BoxLayout(orientation='horizontal')
        self.bt_slave_input = TextInput(text='2', multiline=False, input_filter='int', size_hint_x=0.3)
        self.bt_reg_input = TextInput(text='1000', multiline=False, input_filter='int')
        bt_box.add_widget(self.bt_slave_input)
        bt_box.add_widget(self.bt_reg_input)
        modbus_grid.add_widget(bt_box)
        
        self.root.add_widget(modbus_grid)
        
        # --- CONTROL BUTTON ---
        self.connect_btn = Button(
            text='Connect & Read',
            size_hint_y=None, height=50,
            background_color=(0.1, 0.6, 0.1, 1) # Greenish
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        self.root.add_widget(self.connect_btn)
        
        # --- STATUS & TEXT DISPLAY ---
        self.status_label = Label(text='Status: Disconnected', size_hint_y=None, height=30)
        self.root.add_widget(self.status_label)
        
        display_grid = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        
        # ET Display
        et_box_disp = BoxLayout(orientation='vertical')
        et_box_disp.add_widget(Label(text='ET °C', font_size='14sp', color=(0.1, 0.5, 0.9, 1)))
        self.et_display = Label(text='---', font_size='35sp', bold=True)
        et_box_disp.add_widget(self.et_display)
        display_grid.add_widget(et_box_disp)
        
        # BT Display
        bt_box_disp = BoxLayout(orientation='vertical')
        bt_box_disp.add_widget(Label(text='BT °C', font_size='14sp', color=(0.9, 0.2, 0.2, 1)))
        self.bt_display = Label(text='---', font_size='35sp', bold=True)
        bt_box_disp.add_widget(self.bt_display)
        display_grid.add_widget(bt_box_disp)
        
        self.root.add_widget(display_grid)
        
        # --- MATPLOTLIB GRAPH ---
        # Create figure and axes
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Roaster Temperatures")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Temp (°C)")
        
        # Initialize empty lines
        self.line_et, = self.ax.plot([], [], label='ET', color='blue', linewidth=2)
        self.line_bt, = self.ax.plot([], [], label='BT', color='red', linewidth=2)
        self.ax.legend()
        self.ax.grid(True)
        
        # Integrate Matplotlib figure into Kivy UI
        self.graph_widget = FigureCanvasKivyAgg(self.fig)
        self.root.add_widget(self.graph_widget)
        
        return self.root

    def toggle_connection(self, instance):
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        ip = self.ip_input.text.strip()
        port = int(self.port_input.text.strip())
        
        self.status_label.text = f'Connecting to {ip}:{port}...'
        self.connect_btn.disabled = True
        
        threading.Thread(target=self._connect_thread, args=(ip, port), daemon=True).start()

    def _connect_thread(self, ip, port):
        try:
            client = ModbusTcpClient(ip, port=port, timeout=2.0)
            if client.connect():
                Clock.schedule_once(lambda dt: self._on_connect_success(client))
            else:
                Clock.schedule_once(lambda dt: self._on_connect_fail("Connection Refused"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_connect_fail(str(e)))

    def _on_connect_success(self, client):
        self.modbus_client = client
        self.is_connected = True
        self.status_label.text = 'Status: Connected & Logging'
        self.connect_btn.text = 'Disconnect'
        self.connect_btn.background_color = (0.8, 0.1, 0.1, 1)
        self.connect_btn.disabled = False
        
        # Reset graph data
        self.time_data = []
        self.et_data = []
        self.bt_data = []
        self.start_time = time.time()
        
        # Clear previous plot data visually before starting
        self.line_et.set_data([], [])
        self.line_bt.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.graph_widget.draw()
        
        # Disable inputs
        for inp in [self.ip_input, self.port_input, self.et_slave_input, self.et_reg_input, self.bt_slave_input, self.bt_reg_input]:
            inp.disabled = True
        
        # Polling loop (every 1 second)
        self.poll_event = Clock.schedule_interval(self.poll_modbus, 1.0)

    def _on_connect_fail(self, error_msg):
        self.status_label.text = f'Error: {error_msg}'
        self.connect_btn.disabled = False
        self.is_connected = False
        if self.modbus_client:
            self.modbus_client.close()
            self.modbus_client = None

    def disconnect(self):
        if self.poll_event:
            self.poll_event.cancel()
        
        if self.modbus_client:
            self.modbus_client.close()
            self.modbus_client = None
            
        self.is_connected = False
        self.status_label.text = 'Status: Disconnected'
        self.connect_btn.text = 'Connect & Read'
        self.connect_btn.background_color = (0.1, 0.6, 0.1, 1)
        
        # Re-enable inputs
        for inp in [self.ip_input, self.port_input, self.et_slave_input, self.et_reg_input, self.bt_slave_input, self.bt_reg_input]:
            inp.disabled = False
        
    def poll_modbus(self, dt):
        if not self.modbus_client or not self.modbus_client.is_socket_open():
            self.disconnect()
            self.status_label.text = 'Error: Connection lost'
            return

        et_slave, et_start_reg = int(self.et_slave_input.text), int(self.et_reg_input.text)
        bt_slave, bt_start_reg = int(self.bt_slave_input.text), int(self.bt_reg_input.text)
        
        current_time_offset = time.time() - self.start_time
        et_val_scaled = None
        bt_val_scaled = None

        try:
            # Read ET
            et_result = self.modbus_client.read_input_registers(address=et_start_reg, count=1, slave=et_slave)
            if not et_result.isError():
                # SCALING LOGIC: Assume module returns 2055 for 205.5 Celsius. 
                # (Standard Artisan ModBus setup often requires divide by 10)
                et_val_scaled = et_result.registers[0] / 10.0
                self.et_display.text = f"{et_val_scaled:.1f}"
            else:
                self.et_display.text = "ERR"

            # Read BT
            bt_result = self.modbus_client.read_input_registers(address=bt_start_reg, count=1, slave=bt_slave)
            if not bt_result.isError():
                bt_val_scaled = bt_result.registers[0] / 10.0
                self.bt_display.text = f"{bt_val_scaled:.1f}"
            else:
                self.bt_display.text = "ERR"
                
            # If both reads are successful, update the graph
            if et_val_scaled is not None and bt_val_scaled is not None:
                self.update_graph(current_time_offset, et_val_scaled, bt_val_scaled)

        except Exception as e:
            print(f"Polling error: {e}")
            self.disconnect()
            self.status_label.text = f'Error during poll'
            
    def update_graph(self, t, et, bt):
        # Append data
        self.time_data.append(t)
        self.et_data.append(et)
        self.bt_data.append(bt)
        
        # Optional: Limit data points to keep app snappy (e.g., last 30 minutes = 1800 seconds)
        max_points = 1800
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.et_data = self.et_data[-max_points:]
            self.bt_data = self.bt_data[-max_points:]

        # Update matplotlib lines
        self.line_et.set_data(self.time_data, self.et_data)
        self.line_bt.set_data(self.time_data, self.bt_data)
        
        # Rescale axes based on new data
        self.ax.relim()
        self.ax.autoscale_view()
        
        # Trigger Kivy to redraw the canvas
        self.graph_widget.draw()

if __name__ == '__main__':
    ArtisanLitePoC().run()
