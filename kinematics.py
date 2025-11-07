"""
Kinematics module for coordinate conversion and inverse kinematics.
Converts pixel coordinates to table coordinates and generates servo commands.
Optimized for bird's eye view (top-down camera) setup.
"""
import json
import os

# Calibration parameters (can be saved/loaded from file)
CALIBRATION_FILE = "calibration.json"

# Default calibration for bird's eye view
DEFAULT_CALIBRATION = {
    "origin_px": [320, 240],  # Pixel coordinates of table origin (center)
    "scale_x": 0.0015,        # Meters per pixel in X direction
    "scale_y": 0.0015,        # Meters per pixel in Y direction
    "flip_x": False,           # Flip X axis (for mirrored cameras)
    "flip_y": True,            # Flip Y axis (camera Y is inverted)
    "table_width_m": 0.60,     # Table width in meters (for reference)
    "table_height_m": 0.40,    # Table height in meters (for reference)
    "arm_base_x": 0.0,         # Robot arm base X position in table coordinates
    "arm_base_y": 0.0,         # Robot arm base Y position in table coordinates
}

_calibration = None


def load_calibration():
    """Load calibration from file or use defaults."""
    global _calibration
    if _calibration is not None:
        return _calibration
    
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                _calibration = json.load(f)
                print(f"Loaded calibration from {CALIBRATION_FILE}")
                return _calibration
        except Exception as e:
            print(f"Error loading calibration: {e}, using defaults")
    
    _calibration = DEFAULT_CALIBRATION.copy()
    return _calibration


def save_calibration(calibration=None):
    """Save calibration to file."""
    if calibration is None:
        calibration = _calibration or load_calibration()
    
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(calibration, f, indent=2)
        print(f"Calibration saved to {CALIBRATION_FILE}")
        return True
    except Exception as e:
        print(f"Error saving calibration: {e}")
        return False


def px_to_table(cx, cy, calibration=None):
    """
    Convert pixel coordinates to table coordinates (meters) for bird's eye view.
    
    Args:
        cx, cy: Centroid pixel coordinates
        calibration: Calibration dict (uses loaded calibration if None)
    
    Returns:
        tuple: (x, y) in meters relative to table origin
    """
    if calibration is None:
        calibration = load_calibration()
    
    origin_px = calibration["origin_px"]
    scale_x = calibration["scale_x"]
    scale_y = calibration["scale_y"]
    flip_x = calibration.get("flip_x", False)
    flip_y = calibration.get("flip_y", True)
    
    # Convert pixel offset to meters
    dx = (cx - origin_px[0]) * scale_x
    dy = (cy - origin_px[1]) * scale_y
    
    # Apply flips
    if flip_x:
        dx = -dx
    if flip_y:
        dy = -dy
    
    return dx, dy


def table_to_px(x, y, calibration=None):
    """
    Convert table coordinates (meters) to pixel coordinates.
    Inverse of px_to_table.
    
    Args:
        x, y: Table coordinates in meters
        calibration: Calibration dict (uses loaded calibration if None)
    
    Returns:
        tuple: (cx, cy) pixel coordinates
    """
    if calibration is None:
        calibration = load_calibration()
    
    origin_px = calibration["origin_px"]
    scale_x = calibration["scale_x"]
    scale_y = calibration["scale_y"]
    flip_x = calibration.get("flip_x", False)
    flip_y = calibration.get("flip_y", True)
    
    # Apply flips
    if flip_x:
        x = -x
    if flip_y:
        y = -y
    
    # Convert meters to pixel offset
    cx = origin_px[0] + (x / scale_x)
    cy = origin_px[1] + (y / scale_y)
    
    return int(cx), int(cy)


def calculate_arm_angles(x, y, z=0.02, calibration=None):
    """
    Calculate robot arm joint angles for a given target position.
    
    This is a simplified IK calculation for a typical 5-DOF arm:
    - Base rotation (yaw)
    - Shoulder pitch
    - Elbow pitch
    - Wrist pitch
    - Gripper
    
    Args:
        x: X position in meters (right is positive)
        y: Y position in meters (forward is positive)
        z: Z position in meters (height above table, default: 0.02)
        calibration: Calibration dict (uses loaded calibration if None)
    
    Returns:
        dict: Joint angles in degrees and servo microseconds
    """
    if calibration is None:
        calibration = load_calibration()
    
    # Get arm base position
    arm_base_x = calibration.get("arm_base_x", 0.0)
    arm_base_y = calibration.get("arm_base_y", 0.0)
    
    # Calculate relative position from arm base
    rel_x = x - arm_base_x
    rel_y = y - arm_base_y
    
    # Calculate base rotation (yaw) - angle to target in XY plane
    import math
    base_angle_deg = math.degrees(math.atan2(rel_y, rel_x))
    
    # Calculate distance in XY plane
    xy_dist = math.sqrt(rel_x**2 + rel_y**2)
    
    # Simplified arm geometry (adjust these based on your arm)
    # Assuming arm with shoulder height = 0.15m, upper arm = 0.20m, lower arm = 0.15m
    shoulder_height = 0.15
    upper_arm_length = 0.20
    lower_arm_length = 0.15
    
    # Calculate target distance from shoulder
    target_dist = math.sqrt(xy_dist**2 + (z - shoulder_height)**2)
    
    # Check if target is reachable
    max_reach = upper_arm_length + lower_arm_length
    if target_dist > max_reach:
        print(f"Warning: Target at {target_dist:.3f}m exceeds max reach {max_reach:.3f}m")
        target_dist = max_reach
    
    # Use law of cosines for 2-link arm
    # cos(shoulder_angle) = (upper^2 + target^2 - lower^2) / (2 * upper * target)
    cos_shoulder = (upper_arm_length**2 + target_dist**2 - lower_arm_length**2) / (2 * upper_arm_length * target_dist)
    cos_shoulder = max(-1, min(1, cos_shoulder))  # Clamp to valid range
    shoulder_angle_deg = math.degrees(math.acos(cos_shoulder))
    
    # Elbow angle
    cos_elbow = (upper_arm_length**2 + lower_arm_length**2 - target_dist**2) / (2 * upper_arm_length * lower_arm_length)
    cos_elbow = max(-1, min(1, cos_elbow))
    elbow_angle_deg = 180 - math.degrees(math.acos(cos_elbow))
    
    # Wrist angle to keep gripper level (simplified)
    wrist_angle_deg = -(shoulder_angle_deg + elbow_angle_deg - 90)
    
    return {
        "base_deg": base_angle_deg,
        "shoulder_deg": shoulder_angle_deg,
        "elbow_deg": elbow_angle_deg,
        "wrist_deg": wrist_angle_deg,
        "gripper_deg": 0,  # Open/close handled separately
    }


def fake_ik_to_us(x, y, z=0.02, calibration=None):
    """
    Convert table coordinates to servo microsecond values.
    
    This maps joint angles to servo positions. Adjust the mapping
    based on your specific servo configuration.
    
    Args:
        x: X position in meters (right is positive)
        y: Y position in meters (forward is positive)
        z: Z position in meters (height above table, default: 0.02)
        calibration: Calibration dict (uses loaded calibration if None)
    
    Returns:
        list: [base_us, shoulder_us, elbow_us, wrist_us, grip_us]
              Servo microsecond values (clamped to 900-2100 range)
    """
    angles = calculate_arm_angles(x, y, z, calibration)
    
    # Map angles to servo microseconds
    # Adjust these ranges based on your servo configuration
    # Typical: 1500 = center, 900 = -90deg, 2100 = +90deg
    
    base_us = 1500 + int(angles["base_deg"] * 10 / 9)  # ±90deg = ±1000us
    shoulder_us = 1500 + int(angles["shoulder_deg"] * 10 / 9)
    elbow_us = 1500 + int(angles["elbow_deg"] * 10 / 9)
    wrist_us = 1500 + int(angles["wrist_deg"] * 10 / 9)
    grip_us = 1800  # Will be set by grip state
    
    clamp = lambda u: max(900, min(2100, u))
    return list(map(clamp, [base_us, shoulder_us, elbow_us, wrist_us, grip_us]))


def get_arm_orientation_info(x, y, z=0.02, calibration=None):
    """
    Get detailed orientation information for debugging.
    
    Returns:
        dict: Complete orientation info including angles and servo values
    """
    angles = calculate_arm_angles(x, y, z, calibration)
    servo_us = fake_ik_to_us(x, y, z, calibration)
    
    return {
        "position_m": {"x": x, "y": y, "z": z},
        "angles_deg": angles,
        "servo_us": servo_us,
        "servo_names": ["base", "shoulder", "elbow", "wrist", "grip"]
    }

