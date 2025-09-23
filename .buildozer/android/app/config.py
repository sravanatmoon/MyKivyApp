"""
Configuration file for Smart Home Floor Plan App
Customize your devices, API settings, and app behavior here
"""

from tinxy_controller import DeviceType

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Your Tinxy API Key - REPLACE WITH YOUR ACTUAL KEY
API_KEY = ""  # Set your API key here

# API Settings
API_TIMEOUT = 15  # seconds
MIN_REQUEST_INTERVAL = 0.5  # seconds between API calls

# =============================================================================
# DEVICE CONFIGURATION
# =============================================================================

# Your smart home devices
# You can add, remove, or modify devices here
DEVICES = [
    {
        "name": "Living Room Fan",
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 1,
        "type": DeviceType.FAN,
        "room": "living_room",
        "default_position": (450, 350),  # x, y coordinates (will be converted to dp)
        "supports_speed_control": True
    },
    {
        "name": "Kitchen Light", 
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 2,
        "type": DeviceType.LIGHT,
        "room": "kitchen", 
        "default_position": (180, 250),
        "supports_dimming": True
    },
    {
        "name": "Master Bedroom Light",
        "device_id": "649d9d4dd6587b445bdcd3af", 
        "dev_num": 3,
        "type": DeviceType.BULB,
        "room": "master_bedroom",
        "default_position": (350, 450),
        "supports_dimming": True
    },
    {
        "name": "Bathroom Light",
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 4, 
        "type": DeviceType.LIGHT,
        "room": "bathroom",
        "default_position": (150, 450),
        "supports_dimming": False
    },
    # Add more devices here - just uncomment and modify:
    # {
    #     "name": "Bedroom Fan",
    #     "device_id": "649d9d4dd6587b445bdcd3af", 
    #     "dev_num": 5,
    #     "type": DeviceType.FAN,
    #     "room": "bedroom",
    #     "default_position": (500, 450),
    #     "supports_speed_control": True
    # },
]

# =============================================================================
# VISUAL SETTINGS
# =============================================================================

# App window settings
WINDOW_SIZE = (900, 650)
WINDOW_TITLE = "Smart Home Floor Plan"

# Floor plan settings
FLOOR_PLAN_SIZE = (700, 450)
FLOOR_PLAN_POSITION = (50, 80)

# Device visual settings
FAN_SIZE = (50, 50)
LIGHT_SIZE = (40, 40)
DEVICE_DRAG_THRESHOLD = 15  # pixels to move before drag starts

# Animation settings
FAN_SPEEDS = {
    "off": 0,
    "low": 4.0,    # seconds per rotation
    "medium": 2.0,
    "high": 1.0
}

LIGHT_PULSE_DURATION = 3.0  # seconds for glow pulse

# =============================================================================
# COLOR THEMES
# =============================================================================

# Background colors
BACKGROUND_COLOR = (0.1, 0.1, 0.15, 1)  # Dark blue
FLOOR_PLAN_COLOR = (0.95, 0.95, 0.95, 1)  # Light gray
WALL_COLOR = (0.2, 0.2, 0.2, 1)  # Dark gray

# Device colors
FAN_COLORS = {
    "on": (0.4, 0.7, 1, 0.9),    # Blue when on
    "off": (0.4, 0.4, 0.4, 0.8)  # Gray when off
}

LIGHT_COLORS = {
    "on": (1, 0.95, 0.7, 1),     # Warm white
    "off": (0.4, 0.4, 0.4, 0.7), # Gray when off
    "glow": (1, 0.9, 0.4, 0.3)   # Yellow glow
}

# Button colors
BUTTON_COLORS = {
    "save": (0.2, 0.6, 0.2, 1),     # Green
    "load": (0.6, 0.2, 0.2, 1),     # Red  
    "refresh": (0.2, 0.2, 0.6, 1),  # Blue
    "control": (0.2, 0.4, 0.8, 1)   # Default blue
}

# =============================================================================
# ROOM LAYOUT CONFIGURATION  
# =============================================================================

# Room boundaries as percentages of floor plan size
ROOM_LAYOUT = {
    "kitchen": {
        "bounds": (0, 0, 0.25, 0.4),  # x1, y1, x2, y2 as percentages
        "label_position": (0.125, 0.2)
    },
    "living_room": {
        "bounds": (0.25, 0, 1.0, 0.6),
        "label_position": (0.625, 0.3) 
    },
    "master_bedroom": {
        "bounds": (0, 0.6, 0.6, 1.0),
        "label_position": (0.3, 0.8)
    },
    "bathroom": {
        "bounds": (0, 0.4, 0.25, 0.6), 
        "label_position": (0.125, 0.5)
    },
    "bedroom_2": {
        "bounds": (0.6, 0.6, 1.0, 1.0),
        "label_position": (0.8, 0.8)
    }
}

# Wall definitions (as percentage coordinates)
WALLS = [
    # Outer walls are automatic
    # Internal walls: (x1, y1, x2, y2) as percentages
    (0.25, 0, 0.25, 0.4),    # Kitchen divider
    (0.6, 0.4, 0.6, 1.0),    # Bedroom divider  
    (0, 0.6, 0.6, 0.6),      # Living/bedroom separator
    (0.25, 0.4, 1.0, 0.4),   # Kitchen/living separator
    (0, 0.4, 0.25, 0.4),     # Bathroom separator
]

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable/disable features
ENABLE_ANIMATIONS = True
ENABLE_SOUND_EFFECTS = False  # Future feature
ENABLE_AUTO_SAVE = True
ENABLE_DEVICE_GROUPING = False  # Future feature

# Debug settings
DEBUG_MODE = False
SHOW_DEVICE_IDS = False
MOCK_API = False  # Use mock controller instead of real API

# Auto-refresh interval (seconds, 0 to disable)
AUTO_REFRESH_INTERVAL = 30

# =============================================================================
# FILE PATHS
# =============================================================================

LAYOUT_FILE = "smart_home_layout.json"
LOG_FILE = "smart_home_app.log"
BACKUP_DIR = "layouts_backup"

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check API key
    if not API_KEY:
        errors.append("⚠️  API_KEY not set - app will use mock mode")
    
    # Check devices
    if not DEVICES:
        errors.append("❌ No devices configured")
    
    # Check for duplicate device numbers
    device_keys = set()
    for device in DEVICES:
        key = f"{device['device_id']}:{device['dev_num']}"
        if key in device_keys:
            errors.append(f"❌ Duplicate device: {device['name']}")
        device_keys.add(key)
    
    # Validate device types
    valid_types = [DeviceType.FAN, DeviceType.LIGHT, DeviceType.BULB, 
                   DeviceType.SWITCH, DeviceType.AC, DeviceType.TV]
    for device in DEVICES:
        if device['type'] not in valid_types:
            errors.append(f"❌ Invalid device type for {device['name']}")
    
    return errors

def print_config_status():
    """Print configuration validation results"""
    print("🔧 Configuration Status:")
    errors = validate_config()
    
    if not errors:
        print("✅ Configuration valid!")
        print(f"📱 {len(DEVICES)} devices configured")
        print(f"🏠 {len(ROOM_LAYOUT)} rooms defined")
    else:
        print("Configuration issues found:")
        for error in errors:
            print(f"  {error}")
    print()

if __name__ == "__main__":
    print_config_status()