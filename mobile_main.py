"""
Responsive Smart Home Floor Plan Application
Optimized for mobile devices with automatic rotation and scaling
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.vector import Vector
from kivy.utils import platform
import math
import json
import os

# Import controller with fallback
try:
    from tinxy_controller import get_device_status, switch_device, toggle_device, DeviceType
    from config import DEVICES
    print(f"✅ Loaded {len(DEVICES)} devices from config")
except ImportError as e:
    print(f"⚠️ Using fallback configuration: {e}")
    
    class DeviceType:
        FAN = "fan"
        LIGHT = "light"
        BULB = "bulb"
    
    def get_device_status(device_id, dev_num): return 1
    def switch_device(device_id, dev_num, state): return True  
    def toggle_device(device_id, dev_num): return True
    
    DEVICES = [
        {"name": "Living Room Fan", "device_id": "test", "dev_num": 1, "type": DeviceType.FAN, "default_position": (0.6, 0.6)},
        {"name": "Kitchen Light", "device_id": "test", "dev_num": 2, "type": DeviceType.LIGHT, "default_position": (0.3, 0.4)},
        {"name": "Bedroom Light", "device_id": "test", "dev_num": 3, "type": DeviceType.LIGHT, "default_position": (0.7, 0.8)},
        {"name": "Bathroom Light", "device_id": "test", "dev_num": 4, "type": DeviceType.LIGHT, "default_position": (0.2, 0.7)}
    ]


class ResponsiveWidget(Widget):
    """Base widget that handles responsive sizing"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.on_size_change, pos=self.on_pos_change)
        Window.bind(on_resize=self.on_window_resize)
        
    def on_size_change(self, *args):
        """Override in subclasses for responsive behavior"""
        pass
    
    def on_pos_change(self, *args):
        """Override in subclasses for position updates"""
        pass
    
    def on_window_resize(self, *args):
        """Handle window/screen rotation"""
        Clock.schedule_once(lambda dt: self.on_size_change(), 0.1)


class ResponsiveAnimatedFan(ResponsiveWidget):
    """Responsive animated fan that scales with screen size"""
    
    def __init__(self, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_config = device_config
        self.rotation_angle = 0
        self.speed = 0
        self.is_on = False
        self.animation = None
        
        # Responsive sizing
        self.size_hint = (None, None)
        self.update_size()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_once(self.check_initial_status, 1.0)
    
    def update_size(self):
        """Update size based on screen dimensions"""
        min_dimension = min(Window.width, Window.height)
        # Scale device size: 4-8% of smallest screen dimension
        device_size = max(dp(40), min(dp(100), min_dimension * 0.06))
        self.size = (device_size, device_size)
    
    def on_size_change(self, *args):
        self.update_size()
        self.update_graphics()
    
    def update_graphics(self, *args):
        """Draw responsive fan"""
        self.canvas.clear()
        with self.canvas:
            # Responsive border
            Color(0.8, 0.8, 0.8, 0.3)
            border_width = max(1, self.width * 0.02)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=border_width)
            
            PushMatrix()
            Rotate(angle=self.rotation_angle, origin=self.center)
            
            # Fan base - responsive sizing
            base_size = self.width * 0.7
            base_offset = (self.width - base_size) / 2
            
            if self.is_on:
                Color(0.4, 0.7, 1, 0.9)
            else:
                Color(0.4, 0.4, 0.4, 0.8)
            
            Ellipse(pos=(self.x + base_offset, self.y + base_offset), size=(base_size, base_size))
            
            # Fan blades - responsive
            blade_color = (0.2, 0.5, 0.8, 1) if self.is_on else (0.3, 0.3, 0.3, 0.9)
            Color(*blade_color)
            
            blade_length = self.width * 0.3
            blade_width = max(dp(4), self.width * 0.08)
            blade_thickness = max(dp(12), self.width * 0.25)
            
            for i in range(3):
                angle = i * 120
                rad = math.radians(angle)
                blade_x = self.center_x + blade_length * math.cos(rad) - blade_width/2
                blade_y = self.center_y + blade_length * math.sin(rad) - blade_thickness/2
                Rectangle(pos=(blade_x, blade_y), size=(blade_width, blade_thickness))
            
            # Center hub - responsive
            hub_size = max(dp(6), self.width * 0.15)
            Color(0.1, 0.1, 0.1, 1)
            Ellipse(pos=(self.center_x - hub_size/2, self.center_y - hub_size/2), size=(hub_size, hub_size))
            
            PopMatrix()
    
    def set_speed(self, speed):
        """Set fan speed with animation"""
        self.speed = speed
        self.is_on = speed > 0
        
        if self.animation:
            self.animation.cancel(self)
        
        if self.is_on:
            duration_map = {1: 4.0, 2: 2.0, 3: 1.0}
            duration = duration_map.get(speed, 2.0)
            
            self.animation = Animation(rotation_angle=360, duration=duration)
            self.animation += Animation(rotation_angle=720, duration=duration)
            self.animation.repeat = True
            self.animation.bind(on_progress=lambda *args: self.update_graphics())
            self.animation.start(self)
        else:
            self.animation = Animation(rotation_angle=self.rotation_angle + 45, duration=0.8)
            self.animation.start(self)
        
        self.update_graphics()
    
    def toggle(self):
        """Toggle fan through speeds"""
        if not self.is_on:
            new_speed = 2
        elif self.speed == 1:
            new_speed = 0
        elif self.speed == 2:
            new_speed = 3
        else:
            new_speed = 1
        
        self.set_speed(new_speed)
        
        try:
            if new_speed == 0:
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], "off")
            else:
                speed_map = {1: "low", 2: "medium", 3: "high"}
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], speed_map[new_speed])
        except Exception as e:
            print(f"Error controlling fan: {e}")
    
    def check_initial_status(self, *args):
        """Check device status"""
        try:
            status = get_device_status(self.device_config["device_id"], self.device_config["dev_num"])
            self.set_speed(2 if status == 1 else 0)
        except Exception as e:
            print(f"Error getting fan status: {e}")


class ResponsiveAnimatedLight(ResponsiveWidget):
    """Responsive animated light that scales with screen size"""
    
    def __init__(self, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_config = device_config
        self.is_on = False
        self.brightness = 1.0
        self.glow_animation = None
        self.pulse_scale = 1.0
        
        # Responsive sizing
        self.size_hint = (None, None)
        self.update_size()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_once(self.check_initial_status, 1.0)
    
    def update_size(self):
        """Update size based on screen dimensions"""
        min_dimension = min(Window.width, Window.height)
        device_size = max(dp(35), min(dp(80), min_dimension * 0.05))
        self.size = (device_size, device_size)
    
    def on_size_change(self, *args):
        self.update_size()
        self.update_graphics()
    
    def update_graphics(self, *args):
        """Draw responsive light"""
        self.canvas.clear()
        with self.canvas:
            # Responsive border
            Color(0.8, 0.8, 0.8, 0.3)
            border_width = max(1, self.width * 0.02)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=border_width)
            
            if self.is_on:
                # Responsive glow
                glow_size = self.width * 1.8 * self.pulse_scale
                Color(1, 0.9, 0.4, 0.2 * self.brightness)
                Ellipse(
                    pos=(self.center_x - glow_size/2, self.center_y - glow_size/2),
                    size=(glow_size, glow_size)
                )
                
                # Main bulb
                Color(1, 0.95, 0.7, self.brightness)
                Ellipse(pos=self.pos, size=self.size)
                
                # Bright center - responsive
                center_size = self.width * 0.5
                Color(1, 1, 0.9, self.brightness)
                Ellipse(
                    pos=(self.center_x - center_size/2, self.center_y - center_size/2),
                    size=(center_size, center_size)
                )
            else:
                # Off state
                Color(0.4, 0.4, 0.4, 0.7)
                Ellipse(pos=self.pos, size=self.size)
                
                # Responsive filament lines
                line_width = max(1.5, self.width * 0.02)
                filament_size = self.width * 0.4
                Color(0.2, 0.2, 0.2, 0.9)
                Line(
                    points=[
                        self.center_x - filament_size/2, self.center_y,
                        self.center_x + filament_size/2, self.center_y
                    ], width=line_width
                )
                Line(
                    points=[
                        self.center_x, self.center_y - filament_size/2,
                        self.center_x, self.center_y + filament_size/2
                    ], width=line_width
                )
    
    def turn_on(self, brightness=1.0):
        """Turn light on"""
        self.is_on = True
        self.brightness = brightness
        self.start_pulse()
        self.update_graphics()
    
    def turn_off(self):
        """Turn light off"""
        self.is_on = False
        self.stop_pulse()
        self.update_graphics()
    
    def toggle(self):
        """Toggle light"""
        if self.is_on:
            self.turn_off()
            try:
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], "off")
            except Exception as e:
                print(f"Error turning off light: {e}")
        else:
            self.turn_on()
            try:
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], "on")
            except Exception as e:
                print(f"Error turning on light: {e}")
    
    def start_pulse(self):
        """Start pulsing animation"""
        if self.glow_animation:
            self.glow_animation.cancel(self)
        
        self.glow_animation = (
            Animation(pulse_scale=1.15, duration=2.5) + 
            Animation(pulse_scale=0.85, duration=2.5)
        )
        self.glow_animation.repeat = True
        self.glow_animation.bind(on_progress=lambda *args: self.update_graphics())
        self.glow_animation.start(self)
    
    def stop_pulse(self):
        """Stop pulsing"""
        if self.glow_animation:
            self.glow_animation.cancel(self)
        self.pulse_scale = 1.0
    
    def check_initial_status(self, *args):
        """Check device status"""
        try:
            status = get_device_status(self.device_config["device_id"], self.device_config["dev_num"])
            if status == 1:
                self.turn_on()
            else:
                self.turn_off()
        except Exception as e:
            print(f"Error getting light status: {e}")


class ResponsiveDraggableDevice(ResponsiveWidget):
    """Responsive draggable device container"""
    
    def __init__(self, device_widget, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_widget = device_widget
        self.device_config = device_config
        
        self.size_hint = (None, None)
        self.size = device_widget.size
        
        self.add_widget(device_widget)
        device_widget.pos = (0, 0)
        
        # Touch handling
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_threshold = dp(20)  # Larger threshold for mobile
        
        # Bind size updates
        device_widget.bind(size=self.on_device_size_change)
    
    def on_device_size_change(self, *args):
        """Update container size when device size changes"""
        self.size = self.device_widget.size
    
    def on_size_change(self, *args):
        """Handle responsive size changes"""
        if hasattr(self, 'device_widget'):
            self.device_widget.on_size_change()
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.drag_start_pos = touch.pos
            self.is_dragging = False
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if self.drag_start_pos:
            distance = Vector(touch.pos).distance(self.drag_start_pos)
            
            if not self.is_dragging and distance > self.drag_threshold:
                self.is_dragging = True
            
            if self.is_dragging:
                # Keep device within screen bounds
                new_x = max(0, min(touch.pos[0] - self.width/2, Window.width - self.width))
                new_y = max(0, min(touch.pos[1] - self.height/2, Window.height - self.height))
                self.pos = (new_x, new_y)
                return True
        
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if self.drag_start_pos:
            if not self.is_dragging and self.collide_point(*touch.pos):
                self.show_control_popup()
            
            self.drag_start_pos = None
            self.is_dragging = False
            return True
        
        return super().on_touch_up(touch)
    
    def show_control_popup(self):
        """Show responsive control popup"""
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Device name
        name_label = Label(
            text=self.device_config['name'],
            font_size=sp(18),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1)
        )
        content.add_widget(name_label)
        
        if hasattr(self.device_widget, 'speed'):  # Fan
            self.create_fan_controls(content)
        else:  # Light
            self.create_light_controls(content)
        
        # Responsive popup sizing
        popup_width = min(0.9, max(0.6, 300 / Window.width))
        popup_height = min(0.8, max(0.4, 400 / Window.height))
        
        popup = Popup(
            title=f"Control {self.device_config['name']}",
            content=content,
            size_hint=(popup_width, popup_height),
            auto_dismiss=True
        )
        popup.open()
    
    def create_fan_controls(self, content):
        """Create fan control interface"""
        # Current status
        speed_names = ['Off', 'Low', 'Medium', 'High']
        status_label = Label(
            text=f"Speed: {speed_names[self.device_widget.speed]}",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(status_label)
        
        # Speed buttons
        for i, (label, speed) in enumerate([("Off", 0), ("Low", 1), ("Medium", 2), ("High", 3)]):
            btn = Button(
                text=label,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(16)
            )
            
            if speed == self.device_widget.speed:
                btn.background_color = (0.3, 0.7, 0.3, 1)
            else:
                btn.background_color = (0.2, 0.4, 0.8, 1)
            
            btn.bind(on_press=lambda x, s=speed: self.set_fan_speed(s))
            content.add_widget(btn)
    
    def create_light_controls(self, content):
        """Create light control interface"""
        # Toggle button
        toggle_btn = Button(
            text="Turn Off" if self.device_widget.is_on else "Turn On",
            size_hint_y=None,
            height=dp(60),
            font_size=sp(16)
        )
        
        if self.device_widget.is_on:
            toggle_btn.background_color = (0.8, 0.3, 0.3, 1)
        else:
            toggle_btn.background_color = (0.3, 0.8, 0.3, 1)
        
        toggle_btn.bind(on_press=lambda x: self.device_widget.toggle())
        content.add_widget(toggle_btn)
        
        # Brightness slider (if on)
        if self.device_widget.is_on:
            brightness_label = Label(
                text=f"Brightness: {int(self.device_widget.brightness * 100)}%",
                font_size=sp(14),
                size_hint_y=None,
                height=dp(30)
            )
            content.add_widget(brightness_label)
            
            brightness_slider = Slider(
                min=0.1,
                max=1.0,
                value=self.device_widget.brightness,
                size_hint_y=None,
                height=dp(50)
            )
            
            def update_brightness(slider, value):
                self.device_widget.brightness = value
                self.device_widget.update_graphics()
                brightness_label.text = f"Brightness: {int(value * 100)}%"
            
            brightness_slider.bind(value=update_brightness)
            content.add_widget(brightness_slider)
    
    def set_fan_speed(self, speed):
        """Set fan speed"""
        self.device_widget.set_speed(speed)


class ResponsiveFloorPlan(ResponsiveWidget):
    """Responsive floor plan that adapts to screen size"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_floor_plan, size=self.draw_floor_plan)
    
    def draw_floor_plan(self, *args):
        """Draw responsive floor plan"""
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.92, 0.92, 0.92, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Responsive wall thickness
            wall_width = max(dp(2), min(self.width, self.height) * 0.008)
            Color(0.2, 0.2, 0.2, 1)
            
            # Outer walls
            self.draw_rectangle_outline(self.pos, self.size, wall_width)
            
            # Internal walls - responsive positioning
            w, h = self.size
            x, y = self.pos
            
            # Vertical dividers
            Line(points=[x + w*0.25, y, x + w*0.25, y + h*0.4], width=wall_width)
            Line(points=[x + w*0.6, y + h*0.4, x + w*0.6, y + h], width=wall_width)
            
            # Horizontal dividers
            Line(points=[x, y + h*0.6, x + w*0.6, y + h*0.6], width=wall_width)
            Line(points=[x + w*0.25, y + h*0.4, x + w, y + h*0.4], width=wall_width)
            
            # Room labels (responsive)
            self.draw_room_labels()
    
    def draw_rectangle_outline(self, pos, size, width):
        """Draw rectangle outline"""
        x, y = pos
        w, h = size
        Line(points=[x, y, x + w, y], width=width)
        Line(points=[x + w, y, x + w, y + h], width=width)
        Line(points=[x + w, y + h, x, y + h], width=width)
        Line(points=[x, y + h, x, y], width=width)
    
    def draw_room_labels(self):
        """Draw responsive room labels"""
        # Could add responsive Label widgets here
        pass


class ResponsiveSmartHomeApp(App):
    """Main responsive app"""
    
    def build(self):
        """Build responsive app"""
        # Configure window for mobile
        if platform == 'android' or platform == 'ios':
            # Mobile-specific settings
            Window.softinput_mode = 'below_target'
            Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
        
        # Set initial orientation support
        Window.clearcolor = (0.08, 0.08, 0.12, 1)
        
        # FIXED: Return the main widget, not class with same name
        return ResponsiveSmartHomeWidget()
    
    def on_start(self):
        """App startup"""
        print("🏠 Responsive Smart Home App Started!")
        print(f"📱 Screen: {Window.width}x{Window.height}")
        print("🔄 Supports automatic rotation")
        print("📱 Optimized for mobile devices")
        
        # Check if running on mobile
        if platform in ['android', 'ios']:
            print(f"📱 Running on {platform}")
        else:
            print("💻 Running on desktop (test mode)")
    
    def on_pause(self):
        """Handle app pause (mobile)"""
        return True
    
    def on_resume(self):
        """Handle app resume (mobile)"""
        pass


class ResponsiveSmartHomeWidget(ResponsiveWidget):
    """Main responsive app widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create layout based on orientation
        self.create_layout()
        
        # Bind to window resize for rotation handling
        Window.bind(on_resize=self.handle_rotation)
    
    def create_layout(self):
        """Create responsive layout"""
        self.clear_widgets()
        
        # Determine if portrait or landscape
        is_portrait = Window.height > Window.width
        
        if is_portrait:
            self.create_portrait_layout()
        else:
            self.create_landscape_layout()
    
    def create_portrait_layout(self):
        """Create portrait-optimized layout"""
        main_layout = BoxLayout(orientation='vertical')
        
        # Title
        title = Label(
            text="Smart Home",
            font_size=sp(20),
            size_hint_y=None,
            height=dp(50),
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(title)
        
        # Floor plan (takes most space)
        floor_plan_container = FloatLayout()
        
        # Calculate responsive floor plan size
        margin = dp(20)
        available_height = Window.height - dp(180)  # Space for title and controls
        floor_plan_size = min(Window.width - margin*2, available_height)
        
        self.floor_plan = ResponsiveFloorPlan(
            size_hint=(None, None),
            size=(floor_plan_size, floor_plan_size * 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        floor_plan_container.add_widget(self.floor_plan)
        
        # Create devices
        self.devices = []
        self.create_devices(floor_plan_container)
        
        main_layout.add_widget(floor_plan_container)
        
        # Control buttons
        self.create_control_panel(main_layout)
        
        self.add_widget(main_layout)
    
    def create_landscape_layout(self):
        """Create landscape-optimized layout"""
        main_layout = BoxLayout(orientation='horizontal')
        
        # Left side - floor plan
        floor_plan_container = FloatLayout()
        
        # Calculate responsive sizes
        margin = dp(15)
        floor_plan_width = Window.width * 0.75
        floor_plan_height = Window.height - dp(100)
        
        self.floor_plan = ResponsiveFloorPlan(
            size_hint=(None, None),
            size=(floor_plan_width, floor_plan_height),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        floor_plan_container.add_widget(self.floor_plan)
        
        # Create devices
        self.devices = []
        self.create_devices(floor_plan_container)
        
        main_layout.add_widget(floor_plan_container)
        
        # Right side - controls
        control_layout = BoxLayout(orientation='vertical', size_hint_x=0.25, padding=dp(10), spacing=dp(10))
        
        # Title
        title = Label(
            text="Smart\nHome",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(60),
            color=(1, 1, 1, 1),
            halign='center'
        )
        control_layout.add_widget(title)
        
        # Control buttons (vertical)
        self.create_control_buttons(control_layout)
        
        main_layout.add_widget(control_layout)
        self.add_widget(main_layout)
    
    def create_devices(self, container):
        """Create responsive devices"""
        print(f"Creating {len(DEVICES)} responsive devices...")
        
        floor_plan_x = self.floor_plan.x
        floor_plan_y = self.floor_plan.y
        floor_plan_w = self.floor_plan.width
        floor_plan_h = self.floor_plan.height
        
        for i, device_config in enumerate(DEVICES):
            # Create device widget
            if device_config["type"] == DeviceType.FAN:
                device_widget = ResponsiveAnimatedFan(device_config)
            else:
                device_widget = ResponsiveAnimatedLight(device_config)
            
            # Make it draggable
            draggable = ResponsiveDraggableDevice(device_widget, device_config)
            
            # Position based on relative coordinates
            if "default_position" in device_config:
                pos = device_config["default_position"]
                # Convert relative position (0-1) to absolute
                x = floor_plan_x + floor_plan_w * pos[0]
                y = floor_plan_y + floor_plan_h * pos[1]
            else:
                # Distribute devices
                x = floor_plan_x + floor_plan_w * 0.2 * (i % 3 + 1)
                y = floor_plan_y + floor_plan_h * 0.2 * (i // 3 + 1)
            
            # Ensure within bounds
            x = max(floor_plan_x, min(x, floor_plan_x + floor_plan_w - draggable.width))
            y = max(floor_plan_y, min(y, floor_plan_y + floor_plan_h - draggable.height))
            
            draggable.pos = (x, y)
            
            container.add_widget(draggable)
            self.devices.append(draggable)
            
            print(f"  Device '{device_config['name']}' positioned at {draggable.pos}")
        
        print(f"✅ Created {len(self.devices)} responsive devices")
    
    def create_control_panel(self, parent):
        """Create control panel for portrait mode"""
        control_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10),
            padding=dp(10)
        )
        
        self.create_control_buttons(control_layout)
        parent.add_widget(control_layout)
    
    def create_control_buttons(self, layout):
        """Create responsive control buttons"""
        button_height = dp(45) if Window.height > Window.width else dp(35)
        font_size = sp(12) if Window.height > Window.width else sp(10)
        
        buttons = [
            ("Save", self.save_layout, (0.2, 0.6, 0.2, 1)),
            ("Load", self.load_layout, (0.6, 0.2, 0.2, 1)),
            ("Refresh", self.refresh_devices, (0.2, 0.2, 0.6, 1))
        ]
        
        for text, callback, color in buttons:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=button_height,
                font_size=font_size,
                background_color=color
            )
            btn.bind(on_press=callback)
            layout.add_widget(btn)
    
    def handle_rotation(self, *args):
        """Handle screen rotation"""
        print(f"Screen rotated: {Window.width}x{Window.height}")
        Clock.schedule_once(lambda dt: self.create_layout(), 0.1)
    
    def save_layout(self, instance):
        """Save current layout with relative positioning"""
        layout_data = []
        
        floor_plan_x = self.floor_plan.x
        floor_plan_y = self.floor_plan.y
        floor_plan_w = self.floor_plan.width
        floor_plan_h = self.floor_plan.height
        
        for device in self.devices:
            # Convert absolute position to relative (0-1)
            rel_x = (device.x - floor_plan_x) / floor_plan_w if floor_plan_w > 0 else 0.5
            rel_y = (device.y - floor_plan_y) / floor_plan_h if floor_plan_h > 0 else 0.5
            
            layout_data.append({
                "device_name": device.device_config["name"],
                "relative_position": [rel_x, rel_y]
            })
        
        try:
            with open("mobile_layout.json", "w") as f:
                json.dump(layout_data, f, indent=2)
            self.show_message("Layout Saved", "Device positions saved!")
        except Exception as e:
            self.show_message("Error", f"Failed to save: {str(e)}")
    
    def load_layout(self, instance):
        """Load layout with relative positioning"""
        if not os.path.exists("mobile_layout.json"):
            self.show_message("No Layout", "No saved layout found.")
            return
        
        try:
            with open("mobile_layout.json", "r") as f:
                layout_data = json.load(f)
            
            floor_plan_x = self.floor_plan.x
            floor_plan_y = self.floor_plan.y
            floor_plan_w = self.floor_plan.width
            floor_plan_h = self.floor_plan.height
            
            for item in layout_data:
                device_name = item["device_name"]
                rel_pos = item["relative_position"]
                
                # Convert relative to absolute position
                abs_x = floor_plan_x + floor_plan_w * rel_pos[0]
                abs_y = floor_plan_y + floor_plan_h * rel_pos[1]
                
                # Find and update device
                for device in self.devices:
                    if device.device_config["name"] == device_name:
                        device.pos = (abs_x, abs_y)
                        break
            
            self.show_message("Layout Loaded", "Positions restored!")
        except Exception as e:
            self.show_message("Error", f"Failed to load: {str(e)}")
    
    def refresh_devices(self, instance):
        """Refresh all device statuses"""
        for device in self.devices:
            if hasattr(device.device_widget, 'check_initial_status'):
                device.device_widget.check_initial_status()
        self.show_message("Refreshed", "All devices updated!")
    
    def show_message(self, title, message):
        """Show responsive popup message"""
        content = Label(
            text=message,
            text_size=(dp(200), None),
            halign="center",
            font_size=sp(14)
        )
        
        popup_width = min(0.8, max(0.6, dp(300) / Window.width))
        popup_height = min(0.6, max(0.3, dp(200) / Window.height))
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(popup_width, popup_height),
            auto_dismiss=True
        )
        popup.open()


class ResponsiveSmartHomeApp(App):
    """Main responsive app"""
    
    def build(self):
        """Build responsive app"""
        # Configure window for mobile
        if platform == 'android' or platform == 'ios':
            # Mobile-specific settings
            Window.softinput_mode = 'below_target'
            Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
        
        # Set initial orientation support
        Window.clearcolor = (0.08, 0.08, 0.12, 1)
        
        return ResponsiveSmartHomeWidget()
    
    def on_start(self):
        """App startup"""
        print("🏠 Responsive Smart Home App Started!")
        print(f"📱 Screen: {Window.width}x{Window.height}")
        print("🔄 Supports automatic rotation")
        print("📱 Optimized for mobile devices")
        
        # Check if running on mobile
        if platform in ['android', 'ios']:
            print(f"📱 Running on {platform}")
        else:
            print("💻 Running on desktop (test mode)")
    
    def on_pause(self):
        """Handle app pause (mobile)"""
        return True
    
    def on_resume(self):
        """Handle app resume (mobile)"""
        pass


if __name__ == "__main__":
    ResponsiveSmartHomeApp().run()