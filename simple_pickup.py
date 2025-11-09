"""
Simple hardcoded pickup sequence for robot arm.
Picks up cup directly in front and moves it to the left.
"""
import time
import sys

# Try to import ESP32 controller (optional)
try:
    from esp32_control import ESP32Controller
    ESP32_AVAILABLE = True
except ImportError:
    ESP32_AVAILABLE = False
    print("Note: ESP32 control not available. Running in simulation mode.")

# Hardcoded servo positions (microseconds)
# Format: [base, shoulder, elbow, wrist]
# 1500 = center (90°), 900 = 0°, 2100 = 180°

# Home position (all servos at center)
HOME = [1500, 1500, 1500, 1500]

# Pickup sequence positions
# Servo microseconds: 1500 = center (90°), 900 = 0°, 2100 = 180°
# Base: lower = left, higher = right
# Shoulder: lower = arm up, higher = arm down
# Elbow: lower = elbow up, higher = elbow down
# Wrist: compensates to keep hand level

PICKUP_SEQUENCE = [
    # 1. Approach position (above cup, directly in front, arm extended forward)
    {"name": "approach", "servos": [1500, 1300, 1700, 1500], "delay": 2.0},
    
    # 2. Lower to grab (shoulder down, elbow down to reach low)
    {"name": "lower", "servos": [1500, 1800, 1900, 1500], "delay": 2.0},
    
    # 3. Lift up (shoulder up, elbow up to grab cup)
    {"name": "lift", "servos": [1500, 1300, 1700, 1500], "delay": 2.0},
    
    # 4. Move left (rotate base left, keep arm position)
    {"name": "move_left", "servos": [1200, 1300, 1700, 1500], "delay": 2.0},
    
    # 5. Lower to drop (shoulder down, elbow down)
    {"name": "drop", "servos": [1200, 1800, 1900, 1500], "delay": 2.0},
    
    # 6. Lift up (release cup)
    {"name": "release", "servos": [1200, 1300, 1700, 1500], "delay": 1.5},
    
    # 7. Return to home
    {"name": "home", "servos": HOME, "delay": 2.0},
]

def run_sequence(controller=None):
    """Run the hardcoded pickup sequence."""
    print("\n" + "="*60)
    print("SIMPLE PICKUP SEQUENCE")
    print("="*60)
    print("\nThis will:")
    print("1. Move above cup (directly in front)")
    print("2. Lower to grab")
    print("3. Lift up (grabs cup)")
    print("4. Move left")
    print("5. Lower and release")
    print("6. Lift up (releases cup)")
    print("7. Return to home")
    print("\n" + "="*60)
    
    # Auto-start (no user input needed)
    print("\nStarting sequence in 2 seconds...")
    print("(Press Ctrl+C to cancel)")
    time.sleep(2)
    
    for i, step in enumerate(PICKUP_SEQUENCE, 1):
        print(f"\n[{i}/{len(PICKUP_SEQUENCE)}] {step['name'].upper()}")
        print(f"  Servos: Base={step['servos'][0]}us, Shoulder={step['servos'][1]}us, "
              f"Elbow={step['servos'][2]}us, Wrist={step['servos'][3]}us")
        
        # Send to ESP32 if connected
        if controller:
            success = controller.set_servos_from_us_list(step['servos'])
            if success:
                print(f"  ✅ Command sent to ESP32")
            else:
                print(f"  ❌ Failed to send command")
        else:
            print(f"  (Simulation mode - no ESP32)")
        
        # Wait for movement
        time.sleep(step['delay'])
    
    print("\n" + "="*60)
    print("SEQUENCE COMPLETE!")
    print("="*60 + "\n")

def main():
    """Main function."""
    controller = None
    use_esp32 = False
    
    # Check if ESP32 should be used
    if ESP32_AVAILABLE and len(sys.argv) > 1 and sys.argv[1] == "--esp32":
        use_esp32 = True
        port = sys.argv[2] if len(sys.argv) > 2 else None
        print("\nConnecting to ESP32...")
        controller = ESP32Controller(port=port)
        if controller.connect():
            print("✅ ESP32 connected!")
            use_esp32 = True
        else:
            print("❌ Failed to connect to ESP32. Running in simulation mode.")
            use_esp32 = False
            controller = None
    elif ESP32_AVAILABLE:
        print("\n💡 Tip: Run with '--esp32 [port]' to control real servos")
        print("   Example: python simple_pickup.py --esp32 /dev/cu.usbserial-0001")
    
    try:
        # Run the sequence
        run_sequence(controller)
        
    except KeyboardInterrupt:
        print("\n\nSequence cancelled by user.")
    finally:
        # Return to home position
        if controller:
            print("\nReturning to home position...")
            controller.set_servos_from_us_list(HOME)
            time.sleep(1)
            controller.disconnect()

if __name__ == "__main__":
    main()

