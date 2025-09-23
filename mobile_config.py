"""
Mobile Configuration for Smart Home App
Now dynamically fetches devices from Tinxy API using token authentication
"""

import requests
import json

# =============================================================================
# API AUTHENTICATION - SET YOUR TOKEN HERE
# =============================================================================

# Your Tinxy API Token - REPLACE WITH YOUR ACTUAL TOKEN
API_TOKEN = "beadc11c0218338c6e151f4bb0a0fd083626074a"  # Set your API key here

# API Configuration
API_CONFIG = {
    "base_url": "https://backend.tinxy.in/v2/devices",
    "timeout": 15,
    "headers": {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
}

# =============================================================================
# DEVICE TYPES (LOCAL DEFINITION TO AVOID CIRCULAR IMPORT)
# =============================================================================

class DeviceType:
    """Local device type constants"""
    FAN = "fan"
    LIGHT = "light"
    BULB = "bulb"
    SWITCH = "switch"
    OUTLET = "outlet"
    AC = "ac"
    TV = "tv"
    OTHER = "other"

# =============================================================================
# DYNAMIC DEVICE DISCOVERY
# =============================================================================

def fetch_devices_from_api():
    """Fetch all devices from your Tinxy account"""
    if not API_TOKEN:
        print("⚠️  No API token set - using fallback devices")
        return get_fallback_devices()
    
    try:
        print("🔍 Fetching devices from Tinxy API...")
        
        # Get list of all devices in your account
        response = requests.get(
            API_CONFIG["base_url"], 
            headers=API_CONFIG["headers"], 
            timeout=API_CONFIG["timeout"]
        )
        
        if response.status_code == 200:
            api_devices = response.json()
            print(f"✅ Found {len(api_devices)} devices in your account")
            
            # Convert API response to our device format
            converted_devices = []
            for i, device in enumerate(api_devices):
                converted_device = convert_api_device(device, i)
                if converted_device:
                    converted_devices.append(converted_device)
            
            print(f"📱 Converted {len(converted_devices)} devices for mobile app")
            return converted_devices
            
        else:
            print(f"❌ API error {response.status_code}: {response.text}")
            return get_fallback_devices()
            
    except requests.exceptions.Timeout:
        print("⏰ API timeout - using fallback devices")
        return get_fallback_devices()
    except requests.exceptions.ConnectionError:
        print("🌐 Connection error - using fallback devices")
        return get_fallback_devices()
    except Exception as e:
        print(f"❌ Error fetching devices: {e}")
        return get_fallback_devices()

def convert_api_device(api_device, index):
    """Convert API device format to mobile app format"""
    try:
        # Extract device information from API response
        device_id = api_device.get("_id") or api_device.get("id")
        device_name = api_device.get("name", f"Device {index + 1}")
        
        # Get device switches/outputs
        switches = api_device.get("switches", [])
        if not switches:
            # Single device without switches
            switches = [{"number": 1, "name": device_name}]
        
        converted_devices = []
        
        # Convert each switch to a separate device
        for switch in switches:
            switch_num = switch.get("number", 1)
            switch_name = switch.get("name", f"{device_name} Switch {switch_num}")
            
            # Auto-detect device type from name
            device_type = detect_device_type(switch_name)
            
            # Calculate position based on device index
            position = calculate_default_position(len(converted_devices))
            
            converted_device = {
                "name": switch_name,
                "device_id": device_id,
                "dev_num": switch_num,
                "type": device_type,
                "room": detect_room_from_name(switch_name),
                "default_position": position,
                "supports_speed_control": device_type == DeviceType.FAN,
                "supports_dimming": device_type in [DeviceType.LIGHT, DeviceType.BULB],
                "api_source": True  # Mark as API-sourced
            }
            
            converted_devices.append(converted_device)
        
        return converted_devices[0] if len(converted_devices) == 1 else converted_devices
        
    except Exception as e:
        print(f"⚠️  Error converting device {api_device}: {e}")
        return None

def detect_device_type(name):
    """Auto-detect device type from name"""
    name_lower = name.lower()
    
    # Fan detection
    if any(word in name_lower for word in ['fan', 'exhaust', 'ceiling fan', 'table fan']):
        return DeviceType.FAN
    
    # Light detection
    elif any(word in name_lower for word in ['light', 'lamp', 'led', 'tube light', 'cfl']):
        return DeviceType.LIGHT
    
    # Bulb detection
    elif any(word in name_lower for word in ['bulb', 'chandelier']):
        return DeviceType.BULB
    
    # AC detection
    elif any(word in name_lower for word in ['ac', 'air conditioner', 'cooling', 'hvac']):
        return DeviceType.AC
    
    # TV detection
    elif any(word in name_lower for word in ['tv', 'television', 'monitor']):
        return DeviceType.TV
    
    # Default to switch
    else:
        return DeviceType.SWITCH

def detect_room_from_name(name):
    """Auto-detect room from device name"""
    name_lower = name.lower()
    
    # Room detection patterns
    room_patterns = {
        'living_room': ['living', 'hall', 'drawing'],
        'bedroom': ['bedroom', 'bed room', 'master', 'guest'],
        'kitchen': ['kitchen', 'dining'],
        'bathroom': ['bathroom', 'bath', 'toilet', 'washroom'],
        'balcony': ['balcony', 'terrace', 'porch'],
        'office': ['office', 'study', 'work'],
        'garage': ['garage', 'parking']
    }
    
    for room, patterns in room_patterns.items():
        if any(pattern in name_lower for pattern in patterns):
            return room
    
    return 'other'

def calculate_default_position(index):
    """Calculate default position for devices based on index"""
    # Distribute devices across floor plan
    positions = [
        (0.3, 0.4),  # Kitchen area
        (0.6, 0.6),  # Living room
        (0.7, 0.8),  # Master bedroom
        (0.2, 0.7),  # Bathroom
        (0.8, 0.4),  # Balcony
        (0.5, 0.3),  # Dining
        (0.4, 0.8),  # Guest bedroom
        (0.9, 0.7),  # Office
    ]
    
    if index < len(positions):
        return positions[index]
    else:
        # Generate position for additional devices
        x = 0.2 + (index % 4) * 0.2
        y = 0.3 + ((index // 4) % 3) * 0.25
        return (x, y)

def get_fallback_devices():
    """Fallback devices when API is not available"""
    print("📱 Using fallback device configuration")
    return [
        {
            "name": "Living Room Fan",
            "device_id": "649d9d4dd6587b445bdcd3af",
            "dev_num": 1,
            "type": DeviceType.FAN,
            "room": "living_room",
            "default_position": (0.6, 0.6),
            "supports_speed_control": True,
            "api_source": False
        },
        {
            "name": "Kitchen Light", 
            "device_id": "649d9d4dd6587b445bdcd3af",
            "dev_num": 2,
            "type": DeviceType.LIGHT,
            "room": "kitchen", 
            "default_position": (0.3, 0.4),
            "supports_dimming": True,
            "api_source": False
        },
        {
            "name": "Master Bedroom Light",
            "device_id": "649d9d4dd6587b445bdcd3af", 
            "dev_num": 3,
            "type": DeviceType.BULB,
            "room": "master_bedroom",
            "default_position": (0.7, 0.8),
            "supports_dimming": True,
            "api_source": False
        },
        {
            "name": "Bathroom Light",
            "device_id": "649d9d4dd6587b445bdcd3af",
            "dev_num": 4, 
            "type": DeviceType.LIGHT,
            "room": "bathroom",
            "default_position": (0.2, 0.7),
            "supports_dimming": False,
            "api_source": False
        }
    ]

# =============================================================================
# DEVICE CONFIGURATION (NOW DYNAMIC)
# =============================================================================

# Fetch devices dynamically from API
try:
    DEVICES = fetch_devices_from_api()
    print(f"📱 Loaded {len(DEVICES)} devices into mobile app")
    
    # Print device summary
    for i, device in enumerate(DEVICES):
        print(f"  {i+1}. {device['name']} ({device['type']}) - {'API' if device.get('api_source') else 'Fallback'}")

except Exception as e:
    print(f"❌ Critical error loading devices: {e}")
    DEVICES = get_fallback_devices()

# =============================================================================
# EXISTING MOBILE SETTINGS (UNCHANGED)
# =============================================================================

# Device sizing (as percentage of screen size)
DEVICE_SIZING = {
    "fan": {
        "min_size": 40,
        "max_size": 100,
        "screen_percentage": 0.06
    },
    "light": {
        "min_size": 35,
        "max_size": 80,
        "screen_percentage": 0.05
    }
}

# Touch settings for mobile
TOUCH_SETTINGS = {
    "drag_threshold": 20,    # Pixels to move before drag starts (larger for mobile)
    "touch_timeout": 0.5,    # Seconds for long press
    "double_tap_time": 0.3   # Max time between taps for double tap
}

# Layout margins and spacing (responsive)
LAYOUT_SETTINGS = {
    "margin_percentage": 0.02,      # 2% of screen width/height as margin
    "button_height_portrait": 60,   # Button height in portrait mode (dp)
    "button_height_landscape": 45,  # Button height in landscape mode (dp)
    "title_height": 50,             # Title height (dp)
    "control_panel_height": 80,     # Control panel height (dp)
    "min_floor_plan_size": 300      # Minimum floor plan size (dp)
}

# Font scaling for different screen sizes
FONT_SCALING = {
    "small_screen": {    # < 5 inches diagonal
        "title": 18,
        "button": 12,
        "label": 10,
        "popup": 14
    },
    "medium_screen": {   # 5-7 inches diagonal  
        "title": 20,
        "button": 14,
        "label": 12,
        "popup": 16
    },
    "large_screen": {    # > 7 inches diagonal
        "title": 24,
        "button": 16,
        "label": 14,
        "popup": 18
    }
}

# =============================================================================
# ORIENTATION SETTINGS
# =============================================================================

# Portrait mode layout
PORTRAIT_LAYOUT = {
    "floor_plan_height_ratio": 0.65,  # Floor plan takes 65% of available height
    "control_panel_bottom": True,     # Controls at bottom
    "title_top": True,                # Title at top
    "device_list_side": False         # No side device list
}

# Landscape mode layout  
LANDSCAPE_LAYOUT = {
    "floor_plan_width_ratio": 0.75,   # Floor plan takes 75% of width
    "control_panel_side": True,       # Controls on side
    "title_embedded": True,           # Title embedded in controls
    "device_list_side": True          # Device list in control panel
}

# =============================================================================
# ANIMATION SETTINGS (MOBILE OPTIMIZED)
# =============================================================================

# Reduced animations for better mobile performance
ANIMATION_SETTINGS = {
    "fan_rotation": {
        "low_speed": 3.0,     # Seconds per rotation (reduced from 4.0)
        "medium_speed": 1.5,  # Seconds per rotation (reduced from 2.0) 
        "high_speed": 0.8     # Seconds per rotation (reduced from 1.0)
    },
    "light_pulse": {
        "duration": 2.0,      # Pulse duration (reduced from 3.0)
        "scale_range": 0.15   # Pulse scale variation (reduced)
    },
    "transitions": {
        "layout_change": 0.3,  # Layout transition duration
        "device_drag": 0.1,    # Drag animation duration
        "popup_open": 0.2      # Popup animation duration
    }
}

# =============================================================================
# PLATFORM-SPECIFIC SETTINGS
# =============================================================================

# Android-specific settings
ANDROID_SETTINGS = {
    "statusbar_height": 24,      # Android status bar height (dp)
    "navigation_height": 48,     # Android navigation bar height (dp)
    "back_button_handler": True, # Handle back button
    "hardware_back": True        # Use hardware back button
}

# iOS-specific settings
IOS_SETTINGS = {
    "safe_area_top": 44,         # iOS safe area top (dp)
    "safe_area_bottom": 34,      # iOS safe area bottom (dp)
    "home_indicator": True,      # Account for home indicator
    "status_bar_style": "light"  # Status bar style
}

# =============================================================================
# COLOR THEMES (MOBILE OPTIMIZED)
# =============================================================================

# High contrast colors for mobile screens
MOBILE_COLORS = {
    "background": (0.05, 0.05, 0.08, 1),     # Very dark background
    "floor_plan": (0.95, 0.95, 0.95, 1),     # Light floor plan
    "walls": (0.2, 0.2, 0.2, 1),             # Dark walls
    
    # Device colors (higher contrast)
    "fan_on": (0.3, 0.6, 1, 1),              # Bright blue
    "fan_off": (0.4, 0.4, 0.4, 0.9),         # Medium gray
    "light_on": (1, 0.9, 0.6, 1),            # Warm white
    "light_off": (0.3, 0.3, 0.3, 0.8),       # Dark gray
    "light_glow": (1, 0.8, 0.3, 0.4),        # Orange glow
    
    # UI colors
    "button_primary": (0.2, 0.4, 0.8, 1),    # Blue buttons
    "button_success": (0.2, 0.7, 0.2, 1),    # Green buttons
    "button_danger": (0.8, 0.2, 0.2, 1),     # Red buttons
    "text_primary": (1, 1, 1, 1),            # White text
    "text_secondary": (0.8, 0.8, 0.8, 1),    # Light gray text
    
    # Popup colors
    "popup_background": (0.1, 0.1, 0.1, 0.95), # Dark popup background
    "popup_border": (0.3, 0.3, 0.3, 1)         # Popup border
}

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Mobile performance optimizations
PERFORMANCE_SETTINGS = {
    "max_fps": 30,               # Limit FPS for battery life
    "animation_quality": "medium", # Reduce animation quality
    "canvas_cache": True,        # Enable canvas caching
    "texture_quality": "medium", # Reduce texture quality
    "auto_save_interval": 60     # Auto-save every 60 seconds
}

# =============================================================================
# ACCESSIBILITY SETTINGS
# =============================================================================

# Mobile accessibility features
ACCESSIBILITY_SETTINGS = {
    "large_touch_targets": True,  # Larger touch areas
    "high_contrast": False,       # High contrast mode
    "haptic_feedback": True,      # Vibration feedback
    "screen_reader": True,        # Screen reader support
    "voice_control": False        # Voice control (future)
}

# =============================================================================
# VALIDATION AND HELPERS
# =============================================================================

def get_screen_size_category():
    """Determine screen size category for responsive design"""
    from kivy.core.window import Window
    import math
    
    # Calculate diagonal in inches (approximate)
    width_inches = Window.width / 160  # Assuming ~160 DPI
    height_inches = Window.height / 160
    diagonal = math.sqrt(width_inches**2 + height_inches**2)
    
    if diagonal < 5:
        return "small_screen"
    elif diagonal < 7:
        return "medium_screen"
    else:
        return "large_screen"

def get_font_sizes():
    """Get appropriate font sizes for current screen"""
    category = get_screen_size_category()
    return FONT_SCALING[category]

def is_portrait():
    """Check if device is in portrait orientation"""
    from kivy.core.window import Window
    return Window.height > Window.width

def get_safe_area():
    """Get safe area margins for current platform"""
    from kivy.utils import platform
    
    if platform == 'android':
        return {
            'top': ANDROID_SETTINGS['statusbar_height'],
            'bottom': ANDROID_SETTINGS['navigation_height'],
            'left': 0,
            'right': 0
        }
    elif platform == 'ios':
        return {
            'top': IOS_SETTINGS['safe_area_top'],
            'bottom': IOS_SETTINGS['safe_area_bottom'], 
            'left': 0,
            'right': 0
        }
    else:
        return {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

def validate_mobile_config():
    """Validate mobile configuration"""
    errors = []
    
    # Check devices have relative positions
    for device in DEVICES:
        if 'default_position' in device:
            pos = device['default_position']
            if not (0 <= pos[0] <= 1 and 0 <= pos[1] <= 1):
                errors.append(f"Device {device['name']} has invalid relative position: {pos}")
    
    # Check required settings exist
    required_sections = ['DEVICE_SIZING', 'TOUCH_SETTINGS', 'LAYOUT_SETTINGS']
    for section in required_sections:
        if section not in globals():
            errors.append(f"Missing required configuration section: {section}")
    
    return errors

if __name__ == "__main__":
    print("📱 Mobile Configuration Test")
    print("=" * 40)
    
    errors = validate_mobile_config()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  {error}")
    else:
        print("✅ Mobile configuration is valid")
    
    print(f"📱 Configured devices: {len(DEVICES)}")
    print(f"🎨 Screen size category: {get_screen_size_category()}")
    print(f"📐 Orientation: {'Portrait' if is_portrait() else 'Landscape'}")
    print(f"🔤 Font sizes: {get_font_sizes()}")
    print(f"🔒 Safe areas: {get_safe_area()}")