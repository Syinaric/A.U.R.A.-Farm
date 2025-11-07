"""
Calibration helper script for bird's eye view camera setup.
Helps you calibrate the camera-to-table coordinate mapping.
"""
import cv2
import json
from kinematics import load_calibration, save_calibration, px_to_table, table_to_px

print("=== Camera-to-Table Calibration ===")
print("\nThis script helps you calibrate the coordinate mapping between")
print("pixel coordinates and table coordinates (meters).")
print("\nInstructions:")
print("1. Mount your camera for bird's eye view of the table")
print("2. Place a known-size object (e.g., 10cm square) on the table")
print("3. Click on the object corners to set calibration points")
print("\nPress 'q' to quit, 's' to save calibration, 'r' to reset")

calibration = load_calibration()
print(f"\nCurrent calibration:")
print(f"  Origin (pixels): {calibration['origin_px']}")
print(f"  Scale: {calibration['scale_x']*1000:.2f} mm/px (X), {calibration['scale_y']*1000:.2f} mm/px (Y)")
print(f"  Table size: {calibration['table_width_m']*100:.0f}cm x {calibration['table_height_m']*100:.0f}cm")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

click_points = []
click_mode = "origin"  # origin, scale_x, scale_y

def mouse_callback(event, x, y, flags, param):
    """Handle mouse clicks for calibration."""
    global click_points, click_mode
    
    if event == cv2.EVENT_LBUTTONDOWN:
        click_points.append((x, y))
        print(f"Clicked: ({x}, {y})")
        
        if click_mode == "origin":
            calibration['origin_px'] = [x, y]
            print(f"Set origin to ({x}, {y})")
            click_mode = "scale_x"
            print("Now click on a point 10cm to the right for X scale...")
        elif click_mode == "scale_x":
            if len(click_points) >= 2:
                dx_px = abs(click_points[-1][0] - click_points[-2][0])
                # Assume 10cm = 0.10m
                calibration['scale_x'] = 0.10 / dx_px if dx_px > 0 else calibration['scale_x']
                print(f"Set X scale to {calibration['scale_x']*1000:.2f} mm/px")
                click_mode = "scale_y"
                print("Now click on a point 10cm forward for Y scale...")
        elif click_mode == "scale_y":
            if len(click_points) >= 3:
                dy_px = abs(click_points[-1][1] - click_points[-2][1])
                # Assume 10cm = 0.10m
                calibration['scale_y'] = 0.10 / dy_px if dy_px > 0 else calibration['scale_y']
                print(f"Set Y scale to {calibration['scale_y']*1000:.2f} mm/px")
                print("Calibration complete! Press 's' to save.")

print("\nClick on the table center to set origin...")

cv2.namedWindow("Calibration")
cv2.setMouseCallback("Calibration", mouse_callback)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    
    # Flip frame horizontally (mirror effect)
    frame = cv2.flip(frame, 1)
    
    # Draw calibration points
    vis = frame.copy()
    
    # Draw origin
    origin = calibration['origin_px']
    cv2.circle(vis, tuple(origin), 10, (0, 255, 0), 2)
    cv2.putText(vis, "Origin", (origin[0] + 15, origin[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Draw clicked points
    for i, pt in enumerate(click_points):
        cv2.circle(vis, pt, 5, (255, 0, 0), -1)
        cv2.putText(vis, str(i+1), (pt[0] + 10, pt[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    
    # Draw coordinate grid
    origin_x, origin_y = origin
    for i in range(-3, 4):
        for j in range(-3, 4):
            px_x = origin_x + i * 50
            px_y = origin_y + j * 50
            if 0 <= px_x < 640 and 0 <= px_y < 480:
                table_x, table_y = px_to_table(px_x, px_y, calibration)
                cv2.circle(vis, (px_x, px_y), 2, (128, 128, 128), -1)
                if i == 0 or j == 0:
                    cv2.putText(vis, f"({table_x:.2f},{table_y:.2f})", 
                               (px_x + 5, px_y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128, 128, 128), 1)
    
    # Show current calibration info
    info_text = [
        f"Origin: {origin}",
        f"Scale: {calibration['scale_x']*1000:.2f}mm/px (X), {calibration['scale_y']*1000:.2f}mm/px (Y)",
        f"Click mode: {click_mode}",
        "Press 's' to save, 'r' to reset, 'q' to quit"
    ]
    for i, text in enumerate(info_text):
        cv2.putText(vis, text, (10, 20 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow("Calibration", vis)
    
    k = cv2.waitKey(1) & 0xFF
    if k == ord('q'):
        break
    elif k == ord('s'):
        save_calibration(calibration)
        print("Calibration saved!")
    elif k == ord('r'):
        click_points = []
        click_mode = "origin"
        calibration = load_calibration()
        print("Calibration reset")

cap.release()
cv2.destroyAllWindows()

