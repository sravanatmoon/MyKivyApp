"""
Enhanced Tinxy Controller API
A clean, robust API for controlling Tinxy smart home devices
"""

import requests
import logging
from typing import Optional, Dict, Any, Literal
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceType:
    """Device type constants for icons and behavior"""
    FAN = "fan"
    LIGHT = "light" 
    BULB = "bulb"
    SWITCH = "switch"
    OUTLET = "outlet"
    AC = "ac"
    TV = "tv"
    OTHER = "other"

class TinxyController:
    """Enhanced Tinxy device controller with comprehensive error handling"""
    
    def __init__(self, api_key: str):
        """Initialize controller with API key"""
        self.api_key = api_key
        self.base_url = "https://backend.tinxy.in/v2/devices"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 15
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum seconds between requests
    
    def _rate_limit(self):
        """Simple rate limiting to prevent API overload"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_device_status(self, device_id: str, dev_num: int) -> Optional[int]:
        """
        Get device status with robust error handling
        Returns: 1 for ON, 0 for OFF, None for error
        """
        self._rate_limit()
        api_url = f"{self.base_url}/{device_id}/state?deviceNumber={dev_num}"
        
        try:
            logger.debug(f"Getting status for device {device_id}, switch {dev_num}")
            response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                state = str(data.get("state", "")).lower()
                return 1 if state == "on" else 0
            else:
                logger.warning(f"API returned status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout getting device {device_id} status")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for device {device_id}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting device status: {e}")
            
        return None
    
    def switch_device(self, device_id: str, dev_num: int, 
                     state: Literal["on", "off", "low", "medium", "high"]) -> bool:
        """
        Switch device to specific state with brightness support
        Returns: True if successful, False otherwise
        """
        self._rate_limit()
        
        # Prepare payload based on state
        state_dict = self._prepare_state_payload(state.lower())
        if not state_dict:
            logger.error(f"Invalid state: {state}")
            return False
        
        payload = {
            "request": state_dict,
            "deviceNumber": dev_num
        }
        
        api_url = f"{self.base_url}/{device_id}/toggle"
        
        try:
            logger.debug(f"Switching device {device_id}:{dev_num} to {state}")
            response = requests.post(
                api_url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Device {device_id}:{dev_num} switched to {state}")
                return True
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout switching device {device_id}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error switching device {device_id}")
        except Exception as e:
            logger.error(f"Error switching device: {e}")
            
        return False
    
    def toggle_device(self, device_id: str, dev_num: int) -> bool:
        """
        Toggle device between on/off states
        Returns: True if successful, False otherwise
        """
        current_state = self.get_device_status(device_id, dev_num)
        if current_state is None:
            logger.error("Cannot toggle - unable to determine current state")
            return False
        
        new_state = "off" if current_state == 1 else "on"
        return self.switch_device(device_id, dev_num, new_state)
    
    def _prepare_state_payload(self, state: str) -> Optional[Dict[str, Any]]:
        """Prepare API payload for different states"""
        state_map = {
            "on": {"state": 1},
            "off": {"state": 0},
            "low": {"state": 1, "brightness": 33},
            "medium": {"state": 1, "brightness": 66}, 
            "high": {"state": 1, "brightness": 100}
        }
        return state_map.get(state)

# Global controller instance - FIXED CIRCULAR IMPORT
try:
    from mobile_config import API_TOKEN
    API_KEY = API_TOKEN
except ImportError:
    API_KEY = ""  # Fallback if mobile_config not available
    
_controller = None

def get_controller():
    """Get singleton controller instance"""
    global _controller
    if _controller is None:
        if not API_KEY:
            # For testing without API key
            logger.warning("No API key set - using mock controller")
            return MockController()
        _controller = TinxyController(API_KEY)
    return _controller

# Backward compatibility functions
def get_device_status(device_id: str, dev_num: int) -> Optional[int]:
    return get_controller().get_device_status(device_id, dev_num)

def switch_device(device_id: str, dev_num: int, state: str) -> bool:
    return get_controller().switch_device(device_id, dev_num, state)

def toggle_device(device_id: str, dev_num: int) -> bool:
    return get_controller().toggle_device(device_id, dev_num)

class MockController:
    """Mock controller for testing without API"""
    def __init__(self):
        self.device_states = {}
        
    def get_device_status(self, device_id: str, dev_num: int) -> Optional[int]:
        key = f"{device_id}:{dev_num}"
        return self.device_states.get(key, 0)
        
    def switch_device(self, device_id: str, dev_num: int, state: str) -> bool:
        key = f"{device_id}:{dev_num}"
        self.device_states[key] = 1 if state != "off" else 0
        print(f"Mock: Set {key} to {state}")
        return True
        
    def toggle_device(self, device_id: str, dev_num: int) -> bool:
        current = self.get_device_status(device_id, dev_num)
        new_state = "off" if current == 1 else "on"
        return self.switch_device(device_id, dev_num, new_state)

# Sample device configurations
SAMPLE_DEVICES = [
    {
        "name": "Living Room Fan",
        "device_id": "649d9d4dd6587b445bdcd3af", 
        "dev_num": 1,
        "type": DeviceType.FAN,
        "room": "living_room"
    },
    {
        "name": "Kitchen Light",
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 2, 
        "type": DeviceType.LIGHT,
        "room": "kitchen"
    },
    {
        "name": "Master Bedroom Light",
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 3,
        "type": DeviceType.BULB,
        "room": "master_bedroom"
    },
    {
        "name": "Bathroom Light", 
        "device_id": "649d9d4dd6587b445bdcd3af",
        "dev_num": 4,
        "type": DeviceType.LIGHT,
        "room": "bathroom"
    }
]

if __name__ == "__main__":
    # Test the controller
    if not API_KEY:
        print("⚠️  Set API_KEY to test with real devices")
        print("Testing with mock controller...")
        
    controller = get_controller()
    
    # Test device operations
    test_device_id = "649d9d4dd6587b445bdcd3af"
    test_dev_num = 1
    
    print(f"Initial state: {controller.get_device_status(test_device_id, test_dev_num)}")
    print(f"Toggle result: {controller.toggle_device(test_device_id, test_dev_num)}")
    print(f"Final state: {controller.get_device_status(test_device_id, test_dev_num)}")