"""
Main simulation script for robot arm control.
Uses webcam to detect bottles and executes harvesting sequence when button is pressed.
"""
import cv2
import json
import time
import sys
import threading
from detect import find_cup, detect_all_objects
from kinematics import px_to_table, load_calibration

# Try to import ESP32 controller (optional)
try:
    from esp32_control import ESP32Controller
    ESP32_AVAILABLE = True
except ImportError:
    ESP32_AVAILABLE = False
    print("Note: ESP32 control not available (pyserial not installed). Running in simulation mode.")

PRINT_JSON_ONLY = False  # True to suppress windows
USE_ESP32 = False  # Set to True to control real servos
esp32_controller = None

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Camera 0 not available. Trying camera 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise SystemExit("Error: No camera available. Check camera permissions in System Settings > Privacy & Security > Camera")
    else:
        print("Using camera 1")
else:
    print("Using camera 0")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
print("Camera initialized successfully")

# Load calibration
calibration = load_calibration()
print("Calibration loaded")

# Initialize ESP32 controller if requested
if ESP32_AVAILABLE and len(sys.argv) > 1 and sys.argv[1] == "--esp32":
    USE_ESP32 = True
    port = sys.argv[2] if len(sys.argv) > 2 else None
    print("\nConnecting to ESP32...")
    esp32_controller = ESP32Controller(port=port)
    if esp32_controller.connect():
        print("✅ ESP32 connected! Servos will be controlled in real-time.")
        USE_ESP32 = True
    else:
        print("❌ Failed to connect to ESP32. Running in simulation mode.")
        USE_ESP32 = False
        esp32_controller = None
elif ESP32_AVAILABLE:
    print("\n💡 Tip: Run with '--esp32 [port]' to control real servos")
    print("   Example: python main_sim.py --esp32 /dev/cu.usbserial-*")
    print("   Or: python main_sim.py --esp32  (auto-detect port)")

print("\nControls: q=quit, g=grab/harvest bottle (moves it to the side)")


def draw_ui(frame, bottle=None, all_detections=None):
    """
    Draw detection UI on frame.
    """
    vis = frame.copy()
    
    # Draw all detections in gray (for reference)
    if all_detections:
        for det in all_detections:
            if det.get("label") != "bottle":  # Don't draw bottle twice
                x, y, w, h = det["bbox"]
                cx, cy = det["cx"], det["cy"]
                cv2.rectangle(vis, (x, y), (x + w, y + h), (100, 100, 100), 1)
                label = f"{det.get('label', 'object')} ({det.get('confidence', 0):.2f})"
                cv2.putText(vis, label, (x, max(0, y - 5)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
    
    # Draw bottle detection prominently
    if bottle:
        cx, cy = bottle["cx"], bottle["cy"]
        x, y, w, h = bottle["bbox"]
        
        # Draw bounding box in green
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        # Draw centroid
        cv2.circle(vis, (cx, cy), 8, (0, 255, 0), -1)
        cv2.circle(vis, (cx, cy), 12, (0, 255, 0), 2)
        
        # Draw label
        label = f"BOTTLE ({bottle.get('confidence', 0):.2f})"
        cv2.putText(vis, label, (x, max(0, y - 10)), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw coordinates
        x_table, y_table = px_to_table(cx, cy, calibration=calibration)
        coord_text = f"Table: ({x_table:.3f}m, {y_table:.3f}m)"
        cv2.putText(vis, coord_text, (x, y + h + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw pixel coordinates
        px_text = f"Pixel: ({cx}, {cy})"
        cv2.putText(vis, px_text, (x, y + h + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Draw status
    status = "BOTTLE DETECTED" if bottle else "No bottle detected"
    cv2.putText(vis, status, (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return vis


# Hardcoded pickup sequence positions
# Servo microseconds: 1500 = center (90°), 900 = 0°, 2100 = 180°
# Base: lower = left, higher = right
# Shoulder: lower = arm up, higher = arm down
# Elbow: lower = elbow up, higher = elbow down
# Wrist: compensates to keep hand level

HOME = [1500, 1500, 1500, 1500]

PICKUP_SEQUENCE = [
    # 1. Approach position (above bottle, directly in front, arm extended forward)
    {"name": "approach", "servos": [1500, 1700, 1700, 1500], "delay": 3.0},
    
    # 2. Lower partway (smooth transition)
    {"name": "lower_partway", "servos": [1500, 1300, 1900, 1500], "delay": 2.5},
    
    # 3. Lower to grab (shoulder down - REVERSED: lower microseconds = down)
    {"name": "lower", "servos": [1500, 900, 2100, 1500], "delay": 3.0},
    
    # 4. Lift partway (smooth transition)
    {"name": "lift_partway", "servos": [1500, 1300, 1900, 1500], "delay": 2.5},
    
    # 5. Lift up (shoulder up - REVERSED: higher microseconds = up)
    {"name": "lift", "servos": [1500, 1700, 1700, 1500], "delay": 3.0},
    
    # 6. Move left partway (smooth rotation)
    {"name": "move_left_partway", "servos": [1350, 1700, 1700, 1500], "delay": 2.5},
    
    # 7. Move left (rotate base left, keep arm position)
    {"name": "move_left", "servos": [1200, 1700, 1700, 1500], "delay": 3.0},
    
    # 8. Lower partway (smooth transition)
    {"name": "lower_drop_partway", "servos": [1200, 1300, 1900, 1500], "delay": 2.5},
    
    # 9. Lower to drop (shoulder down - REVERSED: lower microseconds = down)
    {"name": "drop", "servos": [1200, 900, 2100, 1500], "delay": 3.0},
    
    # 10. Lift partway (smooth transition)
    {"name": "release_partway", "servos": [1200, 1300, 1900, 1500], "delay": 2.5},
    
    # 11. Lift up (release cup)
    {"name": "release", "servos": [1200, 1700, 1700, 1500], "delay": 3.0},
    
    # 12. Return base partway (smooth rotation)
    {"name": "return_base_partway", "servos": [1350, 1700, 1700, 1500], "delay": 2.5},
    
    # 13. Return base to center
    {"name": "return_base", "servos": [1500, 1700, 1700, 1500], "delay": 3.0},
    
    # 14. Return to home position (smooth transition)
    {"name": "home_transition", "servos": [1500, 1600, 1600, 1500], "delay": 2.0},
    
    # 15. Return to home position
    {"name": "home", "servos": HOME, "delay": 3.0},
]

# Flag to prevent multiple sequences running at once
sequence_running = False

def execute_harvesting_sequence(bottle):
    """
    Execute the hardcoded harvesting sequence: grab bottle and move it to the left.
    Runs in a separate thread so it doesn't block the camera.
    
    Args:
        bottle: Bottle detection dict with 'cx', 'cy', 'bbox' (used for display only)
    """
    global sequence_running
    
    if sequence_running:
        print("\n⚠️  Sequence already running. Please wait...")
        return
    
    def run_sequence():
        global sequence_running
        sequence_running = True
        
        # Convert pixel coordinates to table coordinates (for display)
        cx, cy = bottle["cx"], bottle["cy"]
        x, y = px_to_table(cx, cy, calibration=calibration)
        
        print(f"\n{'='*60}")
        print(f"HARVESTING SEQUENCE INITIATED")
        print(f"{'='*60}")
        print(f"Bottle detected at pixel: ({cx}, {cy})")
        print(f"Table coordinates: ({x:.3f}m, {y:.3f}m)")
        print(f"\nExecuting hardcoded pickup sequence...")
        print(f"{'='*60}")
        
        for i, step in enumerate(PICKUP_SEQUENCE, 1):
            print(f"\n[{i}/{len(PICKUP_SEQUENCE)}] {step['name'].upper()}")
            print(f"  Servos: Base={step['servos'][0]}us, Shoulder={step['servos'][1]}us, "
                  f"Elbow={step['servos'][2]}us, Wrist={step['servos'][3]}us")
            
            # Send command to ESP32 if connected
            if USE_ESP32 and esp32_controller:
                success = esp32_controller.set_servos_from_us_list(step['servos'])
                if success:
                    print(f"  ✅ Command sent to ESP32")
                else:
                    print(f"  ❌ Failed to send command to ESP32")
            else:
                print(f"  (Simulation mode - no ESP32)")
            
            # Wait for movement (shorter delay to prevent lag)
            time.sleep(step['delay'])
        
        print(f"\n{'='*60}")
        print(f"HARVESTING SEQUENCE COMPLETE")
        print(f"{'='*60}\n")
        
        sequence_running = False
    
    # Run sequence in separate thread
    thread = threading.Thread(target=run_sequence, daemon=True)
    thread.start()


# Main loop
frame_count = 0
all_detections = []

while True:
    ok, frame = cap.read()
    if not ok:
        break
    
    # Flip frame horizontally
    frame = cv2.flip(frame, 1)
    
    # Detect bottle every frame
    bottle, _ = find_cup(frame, confidence=0.25)
    
    # Detect all objects every 5 frames (for display only)
    if frame_count % 5 == 0:
        all_detections, _ = detect_all_objects(frame, confidence=0.25)
    
    frame_count += 1
    
    # Draw UI
    vis = draw_ui(frame, bottle, all_detections)
    
    if not PRINT_JSON_ONLY:
        cv2.imshow("A.U.R.A. FARM - Bottle Detection", vis)
    
    k = cv2.waitKey(1) & 0xFF
    
    if k == ord('q'):
        break
    
    if k == ord('g'):
        # Grab/harvest command - run hardcoded sequence regardless of bottle detection
        print("\n🔄 Initiating harvesting sequence...")
        print("   (Running hardcoded sequence - bottle detection is for display only)")
        # Use a dummy bottle dict for display purposes
        dummy_bottle = {"cx": 320, "cy": 240, "bbox": (280, 200, 80, 80), "confidence": 1.0}
        execute_harvesting_sequence(dummy_bottle)

cap.release()
cv2.destroyAllWindows()

# Disconnect ESP32 if connected
if esp32_controller:
    esp32_controller.disconnect()

print("Camera released. Exiting.")
