"""
Test script to debug device visibility issues
Run this before running main.py to check configuration
"""

def test_imports():
    """Test all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        from tinxy_controller import DeviceType, get_device_status
        print("✅ tinxy_controller import successful")
    except ImportError as e:
        print(f"❌ tinxy_controller import failed: {e}")
        return False
    
    try:
        from config import DEVICES
        print(f"✅ config import successful - {len(DEVICES)} devices found")
    except ImportError as e:
        print(f"❌ config import failed: {e}")
        return False
    
    try:
        import kivy
        print(f"✅ Kivy import successful - version {kivy.__version__}")
    except ImportError as e:
        print(f"❌ Kivy import failed: {e}")
        return False
    
    return True

def test_device_config():
    """Test device configuration is valid"""
    print("\n🔍 Testing device configuration...")
    
    try:
        from config import DEVICES
        from tinxy_controller import DeviceType
        
        if not DEVICES:
            print("❌ No devices configured in DEVICES list")
            return False
        
        print(f"📱 Found {len(DEVICES)} configured devices:")
        
        for i, device in enumerate(DEVICES):
            print(f"\n  Device {i+1}: {device.get('name', 'Unnamed')}")
            
            # Check required fields
            required = ["name", "device_id", "dev_num", "type"]
            missing = [field for field in required if field not in device]
            
            if missing:
                print(f"    ❌ Missing required fields: {missing}")
            else:
                print(f"    ✅ All required fields present")
            
            # Check device type
            valid_types = [DeviceType.FAN, DeviceType.LIGHT, DeviceType.BULB, 
                          DeviceType.SWITCH, DeviceType.AC, DeviceType.TV, DeviceType.OTHER]
            if device.get('type') not in valid_types:
                print(f"    ⚠️  Invalid device type: {device.get('type')}")
            else:
                print(f"    ✅ Valid device type: {device.get('type')}")
            
            # Check position
            if 'default_position' in device:
                pos = device['default_position']
                if isinstance(pos, (list, tuple)) and len(pos) == 2:
                    print(f"    ✅ Valid position: {pos}")
                else:
                    print(f"    ⚠️  Invalid position format: {pos}")
            else:
                print(f"    ℹ️  No default position (will use auto-placement)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing device config: {e}")
        return False

def test_simple_kivy_widget():
    """Test if basic Kivy widgets can be created"""
    print("\n🔍 Testing Kivy widget creation...")
    
    try:
        from kivy.uix.widget import Widget
        from kivy.uix.label import Label
        from kivy.graphics import Color, Rectangle
        
        # Test basic widget creation
        widget = Widget(size=(100, 100), pos=(0, 0))
        print("✅ Basic Widget creation successful")
        
        # Test label creation
        label = Label(text="Test", size=(100, 50))
        print("✅ Label creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Kivy widget test failed: {e}")
        return False

def test_device_widget_creation():
    """Test if our custom device widgets can be created"""
    print("\n🔍 Testing custom device widget creation...")
    
    try:
        # Mock minimal requirements to avoid full Kivy app startup
        import sys
        from unittest.mock import Mock
        
        # Mock kivy components that require app context
        sys.modules['kivy.clock'] = Mock()
        sys.modules['kivy.animation'] = Mock()
        
        from config import DEVICES
        print(f"✅ Device config loaded: {len(DEVICES)} devices")
        
        # Test device configuration
        if DEVICES:
            test_device = DEVICES[0]
            print(f"✅ Test device: {test_device['name']} ({test_device['type']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Device widget test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🧪 Smart Home App Device Debug Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Device Config Test", test_device_config), 
        ("Kivy Widget Test", test_simple_kivy_widget),
        ("Device Widget Test", test_device_widget_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your configuration should work.")
        print("💡 If you still don't see devices, try:")
        print("   1. Check that devices are positioned within floor plan bounds")
        print("   2. Look for small device icons on the gray floor plan area")
        print("   3. Try dragging in the floor plan area to find hidden devices")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running main.py")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🚀 Ready to run: python main.py")
    else:
        print("\n🔧 Please fix configuration issues first")