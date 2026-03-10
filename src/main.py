import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle

import threading
import time
from datetime import datetime

from config_manager import AsetManager
from logger import ArtisanLogger
from modbus_handler import ModbusHandler

import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

# Artisan Desktop Dark Theme Colors
COLOR_BG_MAIN = (0.125, 0.180, 0.224, 1)      # #202e39 (Dark Blue-Grey)
COLOR_BG_GRAPH = '#2a2a2a'                    # Dark Grey for Graph Canvas
COLOR_TEXT_LIGHT = (0.9, 0.9, 0.9, 1)
COLOR_BTN_BLUE = (0.165, 0.584, 0.765, 1)     # #2a95c3 (Artisan Button Blue)
COLOR_BTN_RED = (0.863, 0.106, 0.318, 1)      # #dc1b51 (Artisan Button Red)
COLOR_LCD_GREEN = (0.0, 1.0, 0.0, 1)          # Bright Lime
COLOR_LCD_RED = (1.0, 0.0, 0.0, 1)            # Bright Red

# Set landscape mobile-friendly window size for testing on desktop
Window.size = (1024, 600)

class StyledButton(Button):
    """A flat, neomorphic button mimicking Artisan's top bar."""
    def __init__(self, bg_color=COLOR_BTN_BLUE, **kwargs):
        super(StyledButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_color = bg_color
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = '14sp'

class LCDPanel(BoxLayout):
    """A custom widget to mimic Artisan's dark LCD boxes."""
    def __init__(self, title, color, **kwargs):
        super(LCDPanel, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 70
        self.padding = [5, 2]
        
        # Draw dark background box
        with self.canvas.before:
            Color(0.05, 0.05, 0.05, 1) # Almost black interior
            self.rect = RoundedRectangle(radius=[5])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Title (e.g., 'ET' or 'BT')
        self.title_label = Label(text=title, color=color, font_size='14sp', bold=True, size_hint_y=0.3, halign='right')
        self.title_label.bind(size=self.title_label.setter('text_size'))
        
        # Temperature Readout
        self.value_label = Label(text='---', color=color, font_size='36sp', bold=True, halign='right')
        self.value_label.bind(size=self.value_label.setter('text_size'))
        
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class GraphScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super(GraphScreen, self).__init__(**kwargs)
        self.app_ref = app_ref
        
        # Main Background
        self.layout = BoxLayout(orientation='vertical')
        with self.layout.canvas.before:
            Color(*COLOR_BG_MAIN)
            self.bg_rect = Rectangle()
        self.layout.bind(pos=self.update_bg, size=self.update_bg)

        # ---------------------------------------------------------
        # TOP ACTION BAR
        # ---------------------------------------------------------
        top_bar = BoxLayout(size_hint_y=None, height=60, padding=[20, 10, 20, 10], spacing=10)
        
        # Title / Status
        title_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        self.title_label = Label(text="Roaster Scope", font_size='22sp', bold=True, color=COLOR_TEXT_LIGHT, halign='left')
        self.title_label.bind(size=self.title_label.setter('text_size'))
        self.status_label = Label(text="MODBUS disconnected", font_size='12sp', color=(0.7, 0.7, 0.7, 1), halign='left')
        self.status_label.bind(size=self.status_label.setter('text_size'))
        title_box.add_widget(self.title_label)
        title_box.add_widget(self.status_label)
        
        # Center Clock
        self.clock_label = Label(text="00:00:00", font_size='20sp', bold=True, color=COLOR_TEXT_LIGHT, size_hint_x=0.4)
        Clock.schedule_interval(self.update_clock, 1)
        
        # Right Buttons
        btn_box = BoxLayout(spacing=15, size_hint_x=0.3)
        self.config_btn = StyledButton(text="CONFIG", bg_color=(0.3, 0.3, 0.3, 1))
        self.config_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'config'))
        
        self.connect_btn = StyledButton(text="ON", bg_color=COLOR_BTN_BLUE)
        self.connect_btn.bind(on_press=self.toggle_connection)
        
        self.log_btn = StyledButton(text="SAVE LOG", bg_color=COLOR_BTN_BLUE, disabled=True)
        self.log_btn.bind(on_press=self.save_log)

        btn_box.add_widget(self.config_btn)
        btn_box.add_widget(self.log_btn)
        btn_box.add_widget(self.connect_btn)

        top_bar.add_widget(title_box)
        top_bar.add_widget(self.clock_label)
        top_bar.add_widget(btn_box)
        
        self.layout.add_widget(top_bar)

        # ---------------------------------------------------------
        # MAIN BODY (Graph Left, LCDs Right)
        # ---------------------------------------------------------
        body_layout = BoxLayout(orientation='horizontal', padding=[10, 0, 10, 10], spacing=10)
        
        # -- MATPLOTLIB GRAPH --
        graph_container = BoxLayout(size_hint_x=0.85)
        # Style Matplotlib using Dark Theme
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(facecolor=COLOR_BG_GRAPH)
        self.ax.set_facecolor(COLOR_BG_GRAPH)
        
        # Artisan Style Ticks
        self.ax.set_xlabel("mins", color='white', fontsize=10)
        self.ax.set_ylabel("C", color='white', fontsize=12, rotation=0, labelpad=15)
        self.ax.tick_params(colors='white', labelsize=9)
        self.ax.grid(color='#404040', linestyle='-', linewidth=0.5)
        
        # Hide top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#606060')
        self.ax.spines['left'].set_color('#606060')

        self.line_et, = self.ax.plot([], [], label='ET', color=COLOR_LCD_GREEN[:3], linewidth=2.5)
        self.line_bt, = self.ax.plot([], [], label='BT', color=COLOR_LCD_RED[:3], linewidth=2.5)
        self.fig.tight_layout()
        
        self.graph_widget = FigureCanvasKivyAgg(self.fig)
        graph_container.add_widget(self.graph_widget)
        
        # -- RIGHT SIDEBAR (LCDs) --
        sidebar = BoxLayout(orientation='vertical', size_hint_x=0.15, spacing=15, padding=[10, 20, 0, 0])
        self.et_lcd = LCDPanel(title="ET", color=COLOR_LCD_GREEN)
        self.bt_lcd = LCDPanel(title="BT", color=COLOR_LCD_RED)
        
        sidebar.add_widget(self.et_lcd)
        sidebar.add_widget(self.bt_lcd)
        sidebar.add_widget(Label()) # Spacer to push LCDs to top
        
        body_layout.add_widget(graph_container)
        body_layout.add_widget(sidebar)
        
        self.layout.add_widget(body_layout)
        self.add_widget(self.layout)

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def update_clock(self, dt):
        self.clock_label.text = datetime.now().strftime("%H:%M:%S")

    def toggle_connection(self, instance):
        if not self.app_ref.modbus.is_connected:
            self.status_label.text = "Connecting..."
            self.connect_btn.text = "..."
            self.connect_btn.disabled = True
            
            # Extract config from AsetManager
            cfg = self.app_ref.aset.config_dict
            self.app_ref.modbus.configure(
                ip=cfg['comport'], port=cfg['modbusport'],
                et_slave=cfg['input1deviceId'], et_reg=cfg['input1register'],
                bt_slave=cfg['input2deviceId'], bt_reg=cfg['input2register']
            )
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
            self.status_label.text = f"Logs saved: {datetime.now().strftime('%H:%M:%S')}"


class ConfigScreen(Screen):
    """Redesigned Configuration Screen with dark theme and structured layout."""
    def __init__(self, app_ref, **kwargs):
        super(ConfigScreen, self).__init__(**kwargs)
        self.app_ref = app_ref
        
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        with self.layout.canvas.before:
            Color(*COLOR_BG_MAIN)
            self.bg_rect = Rectangle()
        self.layout.bind(pos=self.update_bg, size=self.update_bg)
        
        # Header
        self.layout.add_widget(Label(text='Ports Configuration & Devices', size_hint_y=None, height=50, font_size='24sp', bold=True, color=COLOR_TEXT_LIGHT))
        
        # Main Grid Container
        main_grid = GridLayout(cols=2, spacing=20, size_hint_y=0.7)
        
        # Left Panel (Network)
        net_box = BoxLayout(orientation='vertical', spacing=10, padding=15)
        with net_box.canvas.before:
            Color(0.2, 0.25, 0.3, 1)
            self.net_rect = RoundedRectangle(radius=[10])
        net_box.bind(pos=self.update_rect_net, size=self.update_rect_net)
        
        net_box.add_widget(Label(text="Modbus Network", bold=True, size_hint_y=0.2, font_size='18sp'))
        
        grid_net = GridLayout(cols=2, spacing=10)
        self.inputs = {}
        target_keys_net = ['comport', 'modbusport']
        labels_net = ['Host IP:', 'TCP Port:']
        
        cfg = self.app_ref.aset.config_dict
        for key, text in zip(target_keys_net, labels_net):
            grid_net.add_widget(Label(text=text, halign='right', size_hint_x=0.4))
            inp = TextInput(text=str(cfg.get(key, '')), multiline=False, background_color=(0.9,0.9,0.9,1))
            self.inputs[key] = inp
            grid_net.add_widget(inp)
        net_box.add_widget(grid_net)
        main_grid.add_widget(net_box)
        
        # Right Panel (Devices)
        dev_box = BoxLayout(orientation='vertical', spacing=10, padding=15)
        with dev_box.canvas.before:
            Color(0.2, 0.25, 0.3, 1)
            self.dev_rect = RoundedRectangle(radius=[10])
        dev_box.bind(pos=self.update_rect_dev, size=self.update_rect_dev)
        
        dev_box.add_widget(Label(text="Device Assignment", bold=True, size_hint_y=0.2, font_size='18sp'))
        
        grid_dev = GridLayout(cols=2, spacing=10)
        target_keys_dev = ['input1deviceId', 'input1register', 'input2deviceId', 'input2register']
        labels_dev = ['ET Device ID:', 'ET Register:', 'BT Device ID:', 'BT Register:']
        
        for key, text in zip(target_keys_dev, labels_dev):
            lbl = Label(text=text, halign='right', size_hint_x=0.5)
            if 'ET' in text: lbl.color = COLOR_LCD_GREEN
            elif 'BT' in text: lbl.color = COLOR_LCD_RED
            
            grid_dev.add_widget(lbl)
            inp = TextInput(text=str(cfg.get(key, '')), multiline=False, background_color=(0.9,0.9,0.9,1))
            self.inputs[key] = inp
            grid_dev.add_widget(inp)
        dev_box.add_widget(grid_dev)
        main_grid.add_widget(dev_box)
        
        self.layout.add_widget(main_grid)
        
        # Action Buttons
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=20, padding=[100,0,100,0])
        back_btn = StyledButton(text='CANCEL', bg_color=(0.4, 0.4, 0.4, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'graph'))
        
        save_btn = StyledButton(text='OK / APPLY', bg_color=COLOR_BTN_BLUE)
        save_btn.bind(on_press=self.save_config)
        
        btn_box.add_widget(back_btn)
        btn_box.add_widget(save_btn)
        self.layout.add_widget(btn_box)
        
        self.add_widget(self.layout)

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    def update_rect_net(self, instance, value):
        self.net_rect.pos = instance.pos
        self.net_rect.size = instance.size
    def update_rect_dev(self, instance, value):
        self.dev_rect.pos = instance.pos
        self.dev_rect.size = instance.size

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
            gs.status_label.text = 'MODBUS connected'
            gs.connect_btn.text = 'OFF'
            gs.connect_btn.background_color = COLOR_BTN_RED
            gs.connect_btn.disabled = False
            gs.log_btn.disabled = False
            
            # Reset graphing data
            self.time_data, self.et_data, self.bt_data = [], [], []
            self.start_time = time.time()
            gs.line_et.set_data([], [])
            gs.line_bt.set_data([], [])
            gs.ax.set_xlim(0, 5) # Start showing 5 minutes ahead
            gs.graph_widget.draw()
            
            # Start UI polling
            self.poll_event = Clock.schedule_interval(self.poll_data, 1.0)
        else:
            gs.status_label.text = f'MODBUS Error: {msg}'
            gs.connect_btn.text = "ON"
            gs.connect_btn.disabled = False
            self.modbus.disconnect()

    def disconnect(self):
        if self.poll_event:
            self.poll_event.cancel()
        self.modbus.disconnect()
        
        gs = self.graph_screen
        gs.status_label.text = 'MODBUS disconnected'
        gs.connect_btn.text = 'ON'
        gs.connect_btn.background_color = COLOR_BTN_BLUE

    def poll_data(self, dt):
        et, bt, error = self.modbus.read_temperatures()
        gs = self.graph_screen
        
        if error:
            self.disconnect()
            gs.status_label.text = f"Modbus Lost: {error}"
            return
            
        gs.et_lcd.value_label.text = f"{et:.1f}"
        gs.bt_lcd.value_label.text = f"{bt:.1f}"
        
        # Update Graph Data (Convert seconds to minutes for X-axis)
        t_mins = (time.time() - self.start_time) / 60.0
        self.time_data.append(t_mins)
        self.et_data.append(et)
        self.bt_data.append(bt)
        
        gs.line_et.set_data(self.time_data, self.et_data)
        gs.line_bt.set_data(self.time_data, self.bt_data)
        
        # Auto-scale axes
        gs.ax.relim()
        gs.ax.autoscale_view()
        
        # Ensure we always show at least a 1-minute window ahead
        current_xlim = gs.ax.get_xlim()
        if t_mins > current_xlim[1] * 0.9:
            gs.ax.set_xlim(0, t_mins + 2)
            
        gs.graph_widget.draw()

if __name__ == '__main__':
    ArtisanLiteApp().run()
