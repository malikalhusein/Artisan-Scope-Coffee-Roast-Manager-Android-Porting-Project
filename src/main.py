import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window

import threading
import time

from config_manager import AsetManager
from logger import ArtisanLogger
from modbus_handler import ModbusHandler

import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

# Set standard mobile-friendly window size for testing on desktop
Window.size = (400, 750)

class GraphScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super(GraphScreen, self).__init__(**kwargs)
        self.app_ref = app_ref
        
        self.layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=50)
        self.status_label = Label(text='Status: Disconnected', font_size='18sp', bold=True)
        config_btn = Button(text='Config ⚙️', size_hint_x=0.3, background_color=(0.5, 0.5, 0.5, 1))
        config_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'config'))
        
        header.add_widget(self.status_label)
        header.add_widget(config_btn)
        self.layout.add_widget(header)
        
        # Temp Display
        display_grid = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        et_box_disp = BoxLayout(orientation='vertical')
        et_box_disp.add_widget(Label(text='ET °C', font_size='14sp', color=(0.1, 0.5, 0.9, 1)))
        self.et_display = Label(text='---', font_size='35sp', bold=True)
        et_box_disp.add_widget(self.et_display)
        display_grid.add_widget(et_box_disp)
        
        bt_box_disp = BoxLayout(orientation='vertical')
        bt_box_disp.add_widget(Label(text='BT °C', font_size='14sp', color=(0.9, 0.2, 0.2, 1)))
        self.bt_display = Label(text='---', font_size='35sp', bold=True)
        bt_box_disp.add_widget(self.bt_display)
        display_grid.add_widget(bt_box_disp)
        self.layout.add_widget(display_grid)
        
        # Matplotlib Graph
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Roaster Temperatures")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Temp (°C)")
        self.line_et, = self.ax.plot([], [], label='ET', color='blue', linewidth=2)
        self.line_bt, = self.ax.plot([], [], label='BT', color='red', linewidth=2)
        self.ax.legend()
        self.ax.grid(True)
        self.graph_widget = FigureCanvasKivyAgg(self.fig)
        self.layout.add_widget(self.graph_widget)
        
        # Controls
        controls = BoxLayout(size_hint_y=None, height=60, spacing=5)
        self.connect_btn = Button(text='Connect', background_color=(0.1, 0.6, 0.1, 1))
        self.connect_btn.bind(on_press=self.toggle_connection)
        
        self.log_btn = Button(text='Save Log', background_color=(0.1, 0.1, 0.8, 1), disabled=True)
        self.log_btn.bind(on_press=self.save_log)
        
        controls.add_widget(self.connect_btn)
        controls.add_widget(self.log_btn)
        self.layout.add_widget(controls)
        
        self.add_widget(self.layout)

    def toggle_connection(self, instance):
        if not self.app_ref.modbus.is_connected:
            self.status_label.text = "Connecting..."
            self.connect_btn.disabled = True
            
            # Extract config from AsetManager
            cfg = self.app_ref.aset.config_dict
            self.app_ref.modbus.configure(
                ip=cfg['comport'], port=cfg['modbusport'],
                et_slave=cfg['input1deviceId'], et_reg=cfg['input1register'],
                bt_slave=cfg['input2deviceId'], bt_reg=cfg['input2register']
            )
            
            # Threaded connect to avoid freezing UI
            threading.Thread(target=self._threaded_connect, daemon=True).start()
        else:
            self.app_ref.disconnect()

    def _threaded_connect(self):
        success, msg = self.app_ref.modbus.connect()
        Clock.schedule_once(lambda dt: self.app_ref._on_connect_result(success, msg))

    def save_log(self, instance):
        if len(self.app_ref.time_data) > 0:
            csv_path = self.app_ref.logger.save_csv(self.app_ref.time_data, self.app_ref.et_data, self.app_ref.bt_data)
            alog_path = self.app_ref.logger.save_alog(self.app_ref.time_data, self.app_ref.et_data, self.app_ref.bt_data)
            self.status_label.text = f"Logs saved locally"

class ConfigScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super(ConfigScreen, self).__init__(**kwargs)
        self.app_ref = app_ref
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.layout.add_widget(Label(text='Artisan Config (.aset)', size_hint_y=None, height=40, font_size='20sp', bold=True))
        
        # Dynamic grid for settings
        target_keys = ['comport', 'modbusport', 'input1deviceId', 'input1register', 'input2deviceId', 'input2register']
        labels = ['IP Host:', 'TCP Port:', 'ET ModBus ID:', 'ET Register:', 'BT ModBus ID:', 'BT Register:']
        
        self.inputs = {}
        grid = GridLayout(cols=2, size_hint_y=None, height=250, spacing=5)
        
        cfg = self.app_ref.aset.config_dict
        for key, text in zip(target_keys, labels):
            grid.add_widget(Label(text=text))
            inp = TextInput(text=str(cfg.get(key, '')), multiline=False)
            self.inputs[key] = inp
            grid.add_widget(inp)
            
        self.layout.add_widget(grid)
        
        # Spacer
        self.layout.add_widget(Label())
        
        # Buttons
        btn_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        save_btn = Button(text='Save & Apply', background_color=(0.1, 0.6, 0.1, 1))
        save_btn.bind(on_press=self.save_config)
        
        back_btn = Button(text='Back', background_color=(0.8, 0.1, 0.1, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'graph'))
        
        btn_box.add_widget(back_btn)
        btn_box.add_widget(save_btn)
        self.layout.add_widget(btn_box)
        
        self.add_widget(self.layout)

    def save_config(self, instance):
        new_dict = {}
        for key, inp in self.inputs.items():
            new_dict[key] = inp.text.strip()
            
        if self.app_ref.aset.save_config(new_dict):
            self.app_ref.aset.config_dict.update(new_dict)
            self.manager.current = 'graph'
        else:
            print("Failed to save .aset")

class ArtisanLiteApp(App):
    def build(self):
        # Initialize Core Modules
        self.aset = AsetManager()
        self.aset.config_dict = self.aset.load_config()
        self.logger = ArtisanLogger()
        self.modbus = ModbusHandler()
        
        # State Data
        self.poll_event = None
        self.time_data = [] 
        self.et_data = []   
        self.bt_data = []   
        self.start_time = None

        # Build UI Screens
        self.sm = ScreenManager()
        self.graph_screen = GraphScreen(app_ref=self, name='graph')
        self.config_screen = ConfigScreen(app_ref=self, name='config')
        
        self.sm.add_widget(self.graph_screen)
        self.sm.add_widget(self.config_screen)
        
        return self.sm

    def _on_connect_result(self, success, msg):
        gs = self.graph_screen
        if success:
            gs.status_label.text = 'Connected & Logging'
            gs.connect_btn.text = 'Disconnect'
            gs.connect_btn.background_color = (0.8, 0.1, 0.1, 1)
            gs.connect_btn.disabled = False
            gs.log_btn.disabled = False
            
            # Reset graphing data
            self.time_data, self.et_data, self.bt_data = [], [], []
            self.start_time = time.time()
            gs.line_et.set_data([], [])
            gs.line_bt.set_data([], [])
            gs.ax.relim()
            gs.ax.autoscale_view()
            gs.graph_widget.draw()
            
            # Start UI polling
            self.poll_event = Clock.schedule_interval(self.poll_data, 1.0)
        else:
            gs.status_label.text = f'Error: {msg}'
            gs.connect_btn.disabled = False
            self.modbus.disconnect()

    def disconnect(self):
        if self.poll_event:
            self.poll_event.cancel()
        self.modbus.disconnect()
        
        gs = self.graph_screen
        gs.status_label.text = 'Disconnected'
        gs.connect_btn.text = 'Connect'
        gs.connect_btn.background_color = (0.1, 0.6, 0.1, 1)

    def poll_data(self, dt):
        et, bt, error = self.modbus.read_temperatures()
        gs = self.graph_screen
        
        if error:
            self.disconnect()
            gs.status_label.text = f"Modbus Lost: {error}"
            return
            
        gs.et_display.text = f"{et:.1f}"
        gs.bt_display.text = f"{bt:.1f}"
        
        # Update Graph Data
        t = time.time() - self.start_time
        self.time_data.append(t)
        self.et_data.append(et)
        self.bt_data.append(bt)
        
        gs.line_et.set_data(self.time_data, self.et_data)
        gs.line_bt.set_data(self.time_data, self.bt_data)
        gs.ax.relim()
        gs.ax.autoscale_view()
        gs.graph_widget.draw()

if __name__ == '__main__':
    ArtisanLiteApp().run()
