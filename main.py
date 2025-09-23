"""
Interactive Smart Home Floor Plan Application
A complete Kivy app with drag-and-drop devices and visual animations
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.vector import Vector
import math
import json
import os

# Import controller
from tinxy_controller import (
    get_device_status, switch_device, toggle_device, 
    DeviceType
)

# Import device configurations
try:
    from config import DEVICES
    print(f"✅ Successfully imported {len(DEVICES)} devices from config")
    # Validate devices have required fields
    for device in DEVICES:
        required_fields = ["name", "device_id", "dev_num", "type"]
        missing = [field for field in required_fields if field not in device]
        if missing:
            print(f"⚠️  Device '{device.get('name', 'Unknown')}' missing fields: {missing}")
except ImportError as e:
    print(f"❌ Failed to import config: {e}")
    print("Creating fallback device configuration...")
    DEVICES = [
        {
            "name": "Test Fan",
            "device_id": "649d9d4dd6587b445bdcd3af",
            "dev_num": 1,
            "type": DeviceType.FAN,
            "default_position": (400, 300)
        },
        {
            "name": "Test Light", 
            "device_id": "649d9d4dd6587b445bdcd3af",
            "dev_num": 2,
            "type": DeviceType.LIGHT,
            "default_position": (200, 250)
        }
    ]

class AnimatedFan(Widget):
    """Animated fan with rotation based on speed"""
    
    def __init__(self, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_config = device_config
        self.size = (dp(50), dp(50))
        self.rotation_angle = 0
        self.speed = 0  # 0=off, 1=low, 2=medium, 3=high
        self.is_on = False
        self.animation = None
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_once(self.check_initial_status, 1.0)
    
    def update_graphics(self, *args):
        """Draw the fan with current rotation"""
        self.canvas.clear()
        with self.canvas:
            # Add a visible border for debugging
            Color(0.8, 0.8, 0.8, 0.5)  # Light gray border
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
            
            PushMatrix()
            # Center the rotation
            Rotate(angle=self.rotation_angle, origin=self.center)
            
            # Fan base circle
            if self.is_on:
                Color(0.4, 0.7, 1, 0.9)  # Blue when on
            else:
                Color(0.4, 0.4, 0.4, 0.8)  # Gray when off
            
            Ellipse(pos=(self.x + dp(8), self.y + dp(8)), size=(dp(34), dp(34)))
            
            # Fan blades
            blade_color = (0.2, 0.5, 0.8, 1) if self.is_on else (0.3, 0.3, 0.3, 0.9)
            Color(*blade_color)
            
            center_x, center_y = self.center_x, self.center_y
            
            # Draw 3 fan blades
            for i in range(3):
                angle = i * 120  # 120 degrees apart
                rad = math.radians(angle)
                
                # Blade position
                blade_x = center_x + dp(15) * math.cos(rad) - dp(4)
                blade_y = center_y + dp(15) * math.sin(rad) - dp(10)
                
                Rectangle(pos=(blade_x, blade_y), size=(dp(8), dp(20)))
            
            # Center hub
            Color(0.1, 0.1, 0.1, 1)
            Ellipse(pos=(center_x - dp(5), center_y - dp(5)), size=(dp(10), dp(10)))
            
            PopMatrix()
    
    def set_speed(self, speed):
        """Set fan speed and start/stop animation"""
        self.speed = speed
        self.is_on = speed > 0
        
        if self.animation:
            self.animation.cancel(self)
        
        if self.is_on:
            # Different speeds = different rotation rates
            duration_map = {1: 4.0, 2: 2.0, 3: 1.0}  # slower = higher duration
            duration = duration_map.get(speed, 2.0)
            
            # Continuous rotation animation
            self.animation = Animation(rotation_angle=360, duration=duration)
            self.animation += Animation(rotation_angle=720, duration=duration)  # Continue rotating
            self.animation.repeat = True
            self.animation.bind(on_progress=self.on_animation_progress)
            self.animation.start(self)
        else:
            # Gradually stop
            self.animation = Animation(rotation_angle=self.rotation_angle + 90, duration=1.0)
            self.animation.bind(on_complete=lambda *args: setattr(self, 'rotation_angle', 0))
            self.animation.start(self)
        
        self.update_graphics()
    
    def on_animation_progress(self, animation, widget, progress):
        """Update graphics during animation"""
        self.update_graphics()
    
    def toggle(self):
        """Cycle through fan speeds: off -> medium -> high -> low -> off"""
        if not self.is_on:
            new_speed = 2  # Start with medium
        elif self.speed == 1:  # low -> off
            new_speed = 0
        elif self.speed == 2:  # medium -> high  
            new_speed = 3
        elif self.speed == 3:  # high -> low
            new_speed = 1
        else:
            new_speed = 0
        
        self.set_speed(new_speed)
        
        # Send command to real device
        try:
            if new_speed == 0:
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], "off")
            else:
                speed_map = {1: "low", 2: "medium", 3: "high"}
                switch_device(self.device_config["device_id"], self.device_config["dev_num"], speed_map[new_speed])
        except Exception as e:
            print(f"Error controlling fan: {e}")
    
    def check_initial_status(self, *args):
        """Check device status from API"""
        try:
            status = get_device_status(self.device_config["device_id"], self.device_config["dev_num"])
            if status == 1:
                self.set_speed(2)  # Default to medium when on
            else:
                self.set_speed(0)
        except Exception as e:
            print(f"Error getting fan status: {e}")


class AnimatedLight(Widget):
    """Animated light with glow effects"""
    
    def __init__(self, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_config = device_config  
        self.size = (dp(40), dp(40))
        self.is_on = False
        self.brightness = 1.0
        self.glow_animation = None
        self.pulse_scale = 1.0
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        Clock.schedule_once(self.check_initial_status, 1.0)
    
    def update_graphics(self, *args):
        """Draw the light with glow effect"""
        self.canvas.clear()
        with self.canvas:
            # Add a visible border for debugging
            Color(0.8, 0.8, 0.8, 0.5)  # Light gray border
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
            
            if self.is_on:
                # Outer glow effect
                glow_size = dp(60) * self.pulse_scale
                Color(1, 0.9, 0.4, 0.3 * self.brightness)
                Ellipse(
                    pos=(self.center_x - glow_size/2, self.center_y - glow_size/2), 
                    size=(glow_size, glow_size)
                )
                
                # Main light bulb
                Color(1, 0.95, 0.7, self.brightness)
                Ellipse(pos=self.pos, size=self.size)
                
                # Bright center
                Color(1, 1, 0.9, self.brightness)
                center_size = dp(20)
                Ellipse(
                    pos=(self.center_x - center_size/2, self.center_y - center_size/2),
                    size=(center_size, center_size)
                )
            else:
                # Off state - gray bulb
                Color(0.4, 0.4, 0.4, 0.7)
                Ellipse(pos=self.pos, size=self.size)
                
                # Filament pattern when off
                Color(0.2, 0.2, 0.2, 0.9)
                Line(
                    points=[
                        self.center_x - dp(8), self.center_y,
                        self.center_x + dp(8), self.center_y
                    ], 
                    width=1.5
                )
                Line(
                    points=[
                        self.center_x, self.center_y - dp(8),
                        self.center_x, self.center_y + dp(8)
                    ], 
                    width=1.5
                )
    
    def set_brightness(self, brightness):
        """Set light brightness 0.0 to 1.0"""
        self.brightness = max(0.0, min(1.0, brightness))
        self.update_graphics()
        
        # Send brightness to real device if supported
        try:
            if brightness > 0:
                if brightness < 0.4:
                    switch_device(self.device_config["device_id"], self.device_config["dev_num"], "low")
                elif brightness < 0.8:
                    switch_device(self.device_config["device_id"], self.device_config["dev_num"], "medium") 
                else:
                    switch_device(self.device_config["device_id"], self.device_config["dev_num"], "high")
        except Exception as e:
            print(f"Error setting brightness: {e}")
    
    def turn_on(self, brightness=1.0):
        """Turn light on with brightness"""
        self.is_on = True
        self.set_brightness(brightness)
        self.start_pulse()
    
    def turn_off(self):
        """Turn light off"""
        self.is_on = False
        self.stop_pulse()
        self.update_graphics()
    
    def toggle(self):
        """Toggle light on/off"""
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
        """Start subtle pulsing animation"""
        if self.glow_animation:
            self.glow_animation.cancel(self)
        
        # Gentle pulsing effect
        self.glow_animation = (
            Animation(pulse_scale=1.1, duration=3.0) + 
            Animation(pulse_scale=0.9, duration=3.0)
        )
        self.glow_animation.repeat = True
        self.glow_animation.bind(on_progress=lambda *args: self.update_graphics())
        self.glow_animation.start(self)
    
    def stop_pulse(self):
        """Stop pulsing animation"""
        if self.glow_animation:
            self.glow_animation.cancel(self)
        self.pulse_scale = 1.0
    
    def check_initial_status(self, *args):
        """Check device status from API"""
        try:
            status = get_device_status(self.device_config["device_id"], self.device_config["dev_num"])
            if status == 1:
                self.turn_on()
            else:
                self.turn_off()
        except Exception as e:
            print(f"Error getting light status: {e}")


class DraggableDevice(Widget):
    """Container that makes devices draggable"""
    
    def __init__(self, device_widget, device_config, **kwargs):
        super().__init__(**kwargs)
        self.device_widget = device_widget
        self.device_config = device_config
        
        # IMPORTANT: Set size to match the device widget, not default
        self.size_hint = (None, None)
        self.size = device_widget.size
        
        # Add device widget as child
        self.add_widget(device_widget)
        
        # Position device widget at (0,0) relative to parent
        device_widget.pos = (0, 0)
        
        # Drag state
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_threshold = dp(15)
        
        # Debug info
        print(f"    DraggableDevice created: size={self.size}, device_size={device_widget.size}")
    
    def on_size(self, *args):
        """Update child widget size when container size changes"""
        if hasattr(self, 'device_widget'):
            self.device_widget.size = self.size
    
    def on_pos(self, *args):
        """Update child widget position when container position changes"""  
        if hasattr(self, 'device_widget'):
            self.device_widget.pos = self.pos
    
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
                # Move device to follow touch
                self.pos = (
                    touch.pos[0] - self.width / 2,
                    touch.pos[1] - self.height / 2
                )
                return True
        
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if self.drag_start_pos:
            if not self.is_dragging and self.collide_point(*touch.pos):
                # It was a tap, not a drag - show control
                self.show_device_control()
            
            self.drag_start_pos = None
            self.is_dragging = False
            return True
        
        return super().on_touch_up(touch)
    
    def show_device_control(self):
        """Show device-specific control popup"""
        if hasattr(self.device_widget, 'speed'):
            self.show_fan_control()
        else:
            self.show_light_control()
    
    def show_fan_control(self):
        """Show fan speed control"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # Current status
        status_label = Label(
            text=f"Current Speed: {['Off', 'Low', 'Medium', 'High'][self.device_widget.speed]}",
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(status_label)
        
        # Speed buttons
        button_layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        speeds = [("Off", 0), ("Low", 1), ("Medium", 2), ("High", 3)]
        for label, speed in speeds:
            btn = Button(
                text=label,
                size_hint_y=None,
                height=dp(50)
            )
            if speed == self.device_widget.speed:
                btn.background_color = (0.3, 0.7, 0.3, 1)  # Highlight current
            else:
                btn.background_color = (0.2, 0.4, 0.8, 1)
            
            btn.bind(on_press=lambda x, s=speed: self.set_fan_speed(s))
            button_layout.add_widget(btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title=f"Control {self.device_config['name']}",
            content=content,
            size_hint=(0.7, 0.6),
            auto_dismiss=True
        )
        popup.open()
        self.current_popup = popup
    
    def show_light_control(self):
        """Show light brightness control"""
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(10))
        
        # On/Off toggle
        toggle_btn = Button(
            text="Turn Off" if self.device_widget.is_on else "Turn On",
            size_hint_y=None,
            height=dp(60)
        )
        if self.device_widget.is_on:
            toggle_btn.background_color = (0.8, 0.3, 0.3, 1)  # Red for off
        else:
            toggle_btn.background_color = (0.3, 0.8, 0.3, 1)  # Green for on
            
        toggle_btn.bind(on_press=lambda x: self.device_widget.toggle())
        content.add_widget(toggle_btn)
        
        # Brightness control (only if on)
        if self.device_widget.is_on:
            brightness_label = Label(
                text=f"Brightness: {int(self.device_widget.brightness * 100)}%",
                size_hint_y=None,
                height=dp(30)
            )
            content.add_widget(brightness_label)
            
            brightness_slider = Slider(
                min=0.1, 
                max=1.0, 
                value=self.device_widget.brightness,
                size_hint_y=None,
                height=dp(40)
            )
            brightness_slider.bind(
                value=lambda x, v: self.device_widget.set_brightness(v)
            )
            brightness_slider.bind(
                value=lambda x, v: setattr(brightness_label, 'text', f"Brightness: {int(v * 100)}%")
            )
            content.add_widget(brightness_slider)
        
        popup = Popup(
            title=f"Control {self.device_config['name']}",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True
        )
        popup.open()
    
    def set_fan_speed(self, speed):
        """Set fan speed and close popup"""
        self.device_widget.set_speed(speed)
        if hasattr(self, 'current_popup'):
            self.current_popup.dismiss()


class FloorPlan(Widget):
    """Floor plan background with rooms"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_floor_plan, size=self.draw_floor_plan)
    
    def draw_floor_plan(self, *args):
        """Draw the floor plan layout"""
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.95, 0.95, 0.95, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Wall color
            Color(0.2, 0.2, 0.2, 1)
            wall_width = dp(4)
            
            # Outer walls
            self.draw_rectangle_outline(self.pos, self.size, wall_width)
            
            # Internal walls (simplified version of your layout)
            w, h = self.size
            x, y = self.pos
            
            # Vertical dividers
            Line(points=[x + w*0.25, y, x + w*0.25, y + h*0.4], width=wall_width)  # Kitchen
            Line(points=[x + w*0.6, y + h*0.4, x + w*0.6, y + h], width=wall_width)  # Bedroom
            
            # Horizontal dividers  
            Line(points=[x, y + h*0.6, x + w*0.6, y + h*0.6], width=wall_width)  # Living/bedroom
            Line(points=[x + w*0.25, y + h*0.4, x + w, y + h*0.4], width=wall_width)  # Kitchen/living
            
            # Room labels
            Color(0.5, 0.5, 0.5, 0.8)
            self.draw_room_labels()
    
    def draw_rectangle_outline(self, pos, size, width):
        """Draw rectangle outline"""
        x, y = pos
        w, h = size
        
        # Four walls
        Line(points=[x, y, x + w, y], width=width)  # Bottom
        Line(points=[x + w, y, x + w, y + h], width=width)  # Right
        Line(points=[x + w, y + h, x, y + h], width=width)  # Top
        Line(points=[x, y + h, x, y], width=width)  # Left
    
    def draw_room_labels(self):
        """Draw room labels (simplified - would use Label widgets in full version)"""
        # In a full implementation, you'd place Label widgets here
        pass


class SmartHomeApp(FloatLayout):
    """Main application widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Floor plan
        self.floor_plan = FloorPlan(
            pos=(dp(50), dp(80)),
            size=(dp(700), dp(450))
        )
        self.add_widget(self.floor_plan)
        
        # Create devices
        self.devices = []
        self.create_devices()
        
        # Control panel
        self.create_control_panel()
        
        # Title
        self.create_title()
    
    def create_devices(self):
        """Create all draggable devices"""
        print(f"Creating {len(DEVICES)} devices...")
        
        # Ensure floor plan is created first
        floor_plan_x = self.floor_plan.x
        floor_plan_y = self.floor_plan.y
        floor_plan_w = self.floor_plan.width
        floor_plan_h = self.floor_plan.height
        
        print(f"Floor plan bounds: x={floor_plan_x}, y={floor_plan_y}, w={floor_plan_w}, h={floor_plan_h}")
        
        for i, device_config in enumerate(DEVICES):
            print(f"Creating device {i+1}: {device_config['name']}")
            
            # Create appropriate device widget
            if device_config["type"] == DeviceType.FAN:
                device_widget = AnimatedFan(device_config)
            else:
                device_widget = AnimatedLight(device_config)
            
            # Make it draggable
            draggable = DraggableDevice(device_widget, device_config)
            
            # Set initial position from config or use default
            if "default_position" in device_config:
                # Convert to dp and ensure within floor plan bounds
                x = dp(device_config["default_position"][0])
                y = dp(device_config["default_position"][1])
                
                # Clamp to floor plan area
                x = max(floor_plan_x + dp(25), min(x, floor_plan_x + floor_plan_w - dp(75)))
                y = max(floor_plan_y + dp(25), min(y, floor_plan_y + floor_plan_h - dp(75)))
                
                draggable.pos = (x, y)
            else:
                # Spread devices across the floor plan if no position specified
                x = floor_plan_x + dp(100 + (i % 3) * 150)
                y = floor_plan_y + dp(100 + (i // 3) * 100)
                draggable.pos = (x, y)
            
            print(f"  Device '{device_config['name']}' positioned at {draggable.pos}")
            print(f"  Device size: {device_widget.size}")
            print(f"  Device type: {device_config['type']}")
            
            self.add_widget(draggable)
            self.devices.append(draggable)
        
        print(f"✅ Total devices created: {len(self.devices)}")
        
        # Schedule a check to make sure devices are visible
        Clock.schedule_once(self.check_device_visibility, 2.0)
    
    def check_device_visibility(self, dt):
        """Debug function to check if devices are visible"""
        print("\n🔍 Device visibility check:")
        print(f"Window size: {Window.width} x {Window.height}")
        print(f"Floor plan: pos={self.floor_plan.pos}, size={self.floor_plan.size}")
        
        visible_count = 0
        for i, device in enumerate(self.devices):
            pos = device.pos
            size = device.size
            print(f"  Device {i+1}: '{device.device_config['name']}'")
            print(f"    Position: ({pos[0]:.1f}, {pos[1]:.1f})")
            print(f"    Size: ({size[0]:.1f}, {size[1]:.1f})")
            print(f"    Device widget size: {device.device_widget.size}")
            print(f"    Bounds: ({pos[0]:.1f}, {pos[1]:.1f}) to ({pos[0]+size[0]:.1f}, {pos[1]+size[1]:.1f})")
            
            # Check if within window bounds
            if (pos[0] >= 0 and pos[1] >= 0 and 
                pos[0] + size[0] <= Window.width and 
                pos[1] + size[1] <= Window.height):
                print(f"    ✅ Device is within window bounds")
                visible_count += 1
            else:
                print(f"    ⚠️  Device may be outside visible area")
                
            # Check if within floor plan bounds
            fp_x, fp_y = self.floor_plan.pos
            fp_w, fp_h = self.floor_plan.size
            if (pos[0] >= fp_x and pos[1] >= fp_y and 
                pos[0] + size[0] <= fp_x + fp_w and 
                pos[1] + size[1] <= fp_y + fp_h):
                print(f"    ✅ Device is within floor plan area")
            else:
                print(f"    ℹ️  Device is outside floor plan (but may still be visible)")
        
        print(f"\n📊 Summary: {visible_count}/{len(self.devices)} devices appear to be visible")
        
        if visible_count == 0:
            print("\n⚠️  NO DEVICES ARE VISIBLE!")
            print("🔧 Troubleshooting steps:")
            print("   1. Look for small colored dots on the screen")
            print("   2. Try moving mouse around the gray floor plan area")
            print("   3. Devices might be very small - look carefully")
            print("   4. Check console for device positioning info above")
            
        print("\n💡 Look for devices in the gray floor plan rectangle!")
        print("   - Fans appear as blue circles with rotating blades")
        print("   - lights appear as yellow/white glowing circles")
        print()
    
    def create_control_panel(self):
        """Create bottom control panel"""
        panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            pos_hint={'y': 0},
            spacing=dp(10),
            padding=[dp(20), dp(10)]
        )
        
        # Save layout button
        save_btn = Button(
            text="Save Layout",
            background_color=(0.2, 0.6, 0.2, 1),
            size_hint_x=0.2
        )
        save_btn.bind(on_press=self.save_layout)
        
        # Load layout button
        load_btn = Button(
            text="Load Layout", 
            background_color=(0.6, 0.2, 0.2, 1),
            size_hint_x=0.2
        )
        load_btn.bind(on_press=self.load_layout)
        
        # Refresh all devices
        refresh_btn = Button(
            text="Refresh All",
            background_color=(0.2, 0.2, 0.6, 1),
            size_hint_x=0.2
        )
        refresh_btn.bind(on_press=self.refresh_all_devices)
        
        # Instructions
        instructions = Label(
            text="Tap devices to control • Drag to reposition",
            color=(0.8, 0.8, 0.8, 1),
            font_size=dp(12)
        )
        
        panel.add_widget(save_btn)
        panel.add_widget(load_btn) 
        panel.add_widget(refresh_btn)
        panel.add_widget(instructions)
        
        self.add_widget(panel)
    
    def create_title(self):
        """Create app title"""
        title = Label(
            text="Smart Home Floor Plan",
            font_size=dp(24),
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(50),
            pos_hint={'top': 1}
        )
        self.add_widget(title)
    
    def save_layout(self, instance):
        """Save current device positions to file"""
        layout_data = []
        
        for i, device in enumerate(self.devices):
            layout_data.append({
                "device_name": device.device_config["name"],
                "position": list(device.pos)
            })
        
        try:
            with open("smart_home_layout.json", "w") as f:
                json.dump(layout_data, f, indent=2)
            
            # Show success popup
            self.show_message("Layout Saved", "Device positions saved successfully!")
        except Exception as e:
            self.show_message("Error", f"Failed to save layout: {str(e)}")
    
    def load_layout(self, instance):
        """Load device positions from file"""
        if not os.path.exists("smart_home_layout.json"):
            self.show_message("No Layout", "No saved layout found.")
            return
        
        try:
            with open("smart_home_layout.json", "r") as f:
                layout_data = json.load(f)
            
            # Apply positions to devices
            for item in layout_data:
                device_name = item["device_name"]
                position = tuple(item["position"])
                
                # Find matching device
                for device in self.devices:
                    if device.device_config["name"] == device_name:
                        device.pos = position
                        break
            
            self.show_message("Layout Loaded", "Device positions restored!")
        except Exception as e:
            self.show_message("Error", f"Failed to load layout: {str(e)}")
    
    def refresh_all_devices(self, instance):
        """Refresh status of all devices"""
        for device in self.devices:
            if hasattr(device.device_widget, 'check_initial_status'):
                device.device_widget.check_initial_status()
        
        self.show_message("Refreshed", "All device states updated!")
    
    def show_message(self, title, message):
        """Show popup message"""
        content = Label(text=message, text_size=(dp(250), None), halign="center")
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.6, 0.4),
            auto_dismiss=True
        )
        popup.open()


class SmartHomeFloorPlanApp(App):
    """Main application class"""
    
    def build(self):
        """Build and return the main widget"""
        # Set window properties
        Window.clearcolor = (0.1, 0.1, 0.15, 1)  # Dark blue background
        Window.size = (900, 650)  # Good size for the floor plan
        
        # Debug: Print device count
        print(f"App starting with {len(DEVICES)} devices configured")
        
        return SmartHomeApp()
    
    def on_start(self):
        """Called when app starts"""
        print("🏠 Smart Home Floor Plan App Started!")
        print(f"📱 Loaded {len(DEVICES)} devices from config")
        print("📱 Tap devices to control them")
        print("🖱️  Drag devices to reposition them") 
        print("💾 Use Save/Load to remember your layout")
        
        # Validate devices are visible
        main_widget = self.root
        if hasattr(main_widget, 'devices'):
            print(f"✅ {len(main_widget.devices)} devices created and added to layout")
            for i, device in enumerate(main_widget.devices):
                print(f"  Device {i}: {device.device_config['name']} at {device.pos}")
        else:
            print("❌ No devices found in main widget")


if __name__ == "__main__":
    SmartHomeFloorPlanApp().run()