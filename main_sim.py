"""
Main simulation script for robot arm control.
Uses webcam to detect objects (by color or label) and processes natural language commands.
"""
import cv2
import json
import time
from detect import find_object, find_by_color, detect_all_objects
from nlu import parse
from kinematics import px_to_table, fake_ik_to_us, get_arm_orientation_info, load_calibration

PRINT_JSON_ONLY = False  # True to suppress windows

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Controls: q=quit, c=type a command (e.g., 'grab the apple' or 'pick the red one')")


def draw_ui(frame, pt, text="", label=None, confidence=None, all_detections=None):
    """
    Draw detection UI on frame.
    
    Args:
        frame: Input frame
        pt: Detection point dict with 'cx', 'cy', 'bbox' keys (or None) - for selected target
        text: Status text to display
        label: Detected object label (for object detection)
        confidence: Detection confidence (for object detection)
        all_detections: List of all detected objects to display
        
    Returns:
        Annotated frame
    """
    vis = frame.copy()
    
    # Draw all detected objects
    if all_detections:
        for det in all_detections:
            x, y, w, h = det["bbox"]
            cx, cy = det["cx"], det["cy"]
            det_label = det.get("label", "")
            det_conf = det.get("confidence", 0)
            
            # Draw bounding box (green for all objects)
            cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(vis, (cx, cy), 4, (0, 255, 0), -1)
            
            # Calculate table coordinates
            table_x, table_y = px_to_table(cx, cy)
            
            # Draw label, confidence, and coordinates
            label_text = f"{det_label} ({det_conf:.2f})"
            pixel_coord_text = f"px: ({cx}, {cy})"
            table_coord_text = f"table: ({table_x:.3f}m, {table_y:.3f}m)"
            
            # Draw label above bounding box
            cv2.putText(vis, label_text, (x, max(0, y - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            # Draw pixel coordinates below bounding box
            cv2.putText(vis, pixel_coord_text, (x, y + h + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
            
            # Draw table coordinates below pixel coordinates
            cv2.putText(vis, table_coord_text, (x, y + h + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    
    # Highlight selected target if provided
    if pt:
        cx, cy = pt["cx"], pt["cy"]
        x, y, w, h = pt["bbox"]
        # Draw thicker box in blue for selected target
        cv2.rectangle(vis, (x, y), (x + w, y + h), (255, 0, 0), 3)
        cv2.circle(vis, (cx, cy), 8, (255, 0, 0), -1)
        
        # Calculate table coordinates and arm orientation
        table_x, table_y = px_to_table(cx, cy)
        orientation_info = get_arm_orientation_info(table_x, table_y, z=0.02)
        
        # Display coordinates and label if available
        info_text = f"TARGET: {label if label else 'object'}"
        pixel_text = f"px: ({cx}, {cy})"
        table_text = f"table: ({table_x:.3f}m, {table_y:.3f}m)"
        angle_text = f"base: {orientation_info['angles_deg']['base_deg']:.1f}°"
        
        cv2.putText(vis, info_text, (x, max(0, y - 50)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        cv2.putText(vis, pixel_text, (x, max(0, y - 35)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
        cv2.putText(vis, table_text, (x, max(0, y - 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
        cv2.putText(vis, angle_text, (x, max(0, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    
    if text:
        cv2.putText(vis, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return vis


# Default detection (for continuous display)
current_target_type = "nearest"
current_target_value = None
selected_target = None  # Currently selected target for pick/place

# Detection frequency control (run YOLO every N frames for performance)
detection_frame_count = 0
detection_interval = 5  # Run YOLO every 5 frames
all_detections = []  # Store all detected objects

while True:
    ok, frame = cap.read()
    if not ok:
        break
    
    # Flip frame horizontally (mirror effect)
    frame = cv2.flip(frame, 1)
    
    # Run YOLO detection every N frames (for performance)
    detection_frame_count += 1
    if detection_frame_count >= detection_interval:
        all_detections, vis_img = detect_all_objects(frame, confidence=0.25)
        detection_frame_count = 0
        if all_detections:
            print(f"Detected {len(all_detections)} objects:")
            for det in all_detections:
                table_x, table_y = px_to_table(det['cx'], det['cy'])
                print(f"  - {det['label']}: px=({det['cx']}, {det['cy']}), "
                      f"table=({table_x:.3f}m, {table_y:.3f}m), conf={det['confidence']:.2f}")
        else:
            print("No objects detected")
    
    # Determine selected target based on current_target_type
    pt = None
    if current_target_type == "label" and current_target_value and all_detections:
        # Find matching object from all detections
        for det in all_detections:
            if current_target_value.lower() in det.get("label", "").lower():
                pt = det
                break
    elif current_target_type == "color" and current_target_value:
        # Use color detection
        pt, vis_img = find_by_color(frame, current_target_value)
    elif selected_target:
        # Use previously selected target
        pt = selected_target
    
    # Determine status text
    if all_detections:
        status = f"Objects detected: {len(all_detections)}"
        if pt:
            status += f" | TARGET: {pt.get('label', 'selected')}"
    else:
        status = "Scanning for objects..."
    
    if not PRINT_JSON_ONLY:
        # Show YOLO annotated frame
        if len(all_detections) > 0:
            cv2.imshow("detection", vis_img)
        else:
            cv2.imshow("detection", frame)
        
        cv2.imshow("webcam", draw_ui(frame, pt, status, 
                                     label=pt.get("label") if pt else None,
                                     confidence=pt.get("confidence") if pt else None,
                                     all_detections=all_detections))
    
    k = cv2.waitKey(1) & 0xFF
    if k == ord('q'):
        break
    
    if k == ord('c'):
        text = input("\nSay/type a command: ")
        cmd = parse(text)
        print("Parsed command:", cmd.model_dump())
        
        if cmd.task in ("open", "close"):
            print(json.dumps({"op": "grip", "state": cmd.task}))
            continue
        
        # Update current target for continuous detection
        current_target_type = cmd.target.type
        current_target_value = cmd.target.value
        selected_target = None
        
        # Force immediate detection
        if cmd.target.type == "label" and cmd.target.value:
            # Find matching object from current detections
            for det in all_detections:
                if cmd.target.value.lower() in det.get("label", "").lower():
                    selected_target = det
                    pt = det
                    break
            
            if not pt:
                # Run fresh detection
                all_detections, vis_img = detect_all_objects(frame, confidence=0.25)
                for det in all_detections:
                    if cmd.target.value.lower() in det.get("label", "").lower():
                        selected_target = det
                        pt = det
                        break
        elif cmd.target.type == "color" and cmd.target.value:
            pt, vis_img = find_by_color(frame, cmd.target.value)
            selected_target = pt
        else:
            # Use nearest/largest from all detections
            if all_detections:
                pt = max(all_detections, key=lambda d: d.get("confidence", 0))
                selected_target = pt
        
        if not pt:
            target_desc = f"{cmd.target.value} {cmd.target.type}" if cmd.target.value else "target"
            print(f"No {target_desc} detected. Show the object to the camera.")
            print(f"Available objects: {[d['label'] for d in all_detections]}")
            continue
        
        cx, cy = pt["cx"], pt["cy"]
        x, y = px_to_table(cx, cy)
        xd, yd = x + cmd.drop.dx, y + cmd.drop.dy
        
        # Get arm orientation info for target
        orientation_info = get_arm_orientation_info(x, y, z=0.02)
        print(f"\nTarget position: ({x:.3f}m, {y:.3f}m)")
        print(f"Arm angles: base={orientation_info['angles_deg']['base_deg']:.1f}°, "
              f"shoulder={orientation_info['angles_deg']['shoulder_deg']:.1f}°, "
              f"elbow={orientation_info['angles_deg']['elbow_deg']:.1f}°")
        print(f"Servo commands: {orientation_info['servo_us']}")
        
        waypoints = [
            {"name": "above_pick", "x": x, "y": y, "z": 0.10, "grip": "open"},
            {"name": "pick", "x": x, "y": y, "z": 0.02, "grip": "close"},
            {"name": "above_drop", "x": xd, "y": yd, "z": 0.10, "grip": "close"},
            {"name": "drop", "x": xd, "y": yd, "z": 0.02, "grip": "open"},
        ]
        
        print("\n--- PLAN ---")
        for wp in waypoints:
            us = fake_ik_to_us(wp["x"], wp["y"], wp["z"])
            us[-1] = 1200 if wp["grip"] == "open" else 1800
            print(json.dumps({"op": "j", "us": us, "wp": wp["name"]}))
            time.sleep(0.15)

cap.release()
cv2.destroyAllWindows()

