# Robot Arm Specification Requirements

To configure the inverse kinematics system for your CAD-designed arm, I need the following information:

## 1. Arm Geometry (Link Lengths)

Measure from joint center to joint center:

- **Shoulder Height** (`shoulder_height_m`): 
  - Distance from table surface to shoulder joint center (meters)
  - Example: 0.15m = 15cm

- **Upper Arm Length** (`upper_arm_length_m`):
  - Distance from shoulder joint center to elbow joint center (meters)
  - Example: 0.20m = 20cm

- **Lower Arm Length** (`lower_arm_length_m`):
  - Distance from elbow joint center to wrist joint center (meters)
  - Example: 0.15m = 15cm

- **Wrist Offset** (`wrist_offset_m`):
  - Any offset from wrist joint to gripper center (meters)
  - Usually 0.0 if gripper is at wrist center
  - Example: 0.05m = 5cm

- **Gripper Length** (`gripper_length_m`):
  - Length of gripper from wrist to tip (meters)
  - Used for collision checking
  - Example: 0.05m = 5cm

## 2. Joint Limits (Degrees)

For each joint, specify the minimum and maximum angles:

- **Base Joint** (rotation/yaw):
  - Min angle: -180° to 180°
  - Max angle: -180° to 180°
  - Home position: Usually 0°

- **Shoulder Joint** (pitch):
  - Min angle: Typically -90° to 0°
  - Max angle: Typically 0° to 90°
  - Home position: Usually 0° (horizontal) or 45°

- **Elbow Joint** (pitch):
  - Min angle: Typically 0° to 90°
  - Max angle: Typically 90° to 180°
  - Home position: Usually 90° (bent)

- **Wrist Joint** (pitch):
  - Min angle: Typically -90° to 0°
  - Max angle: Typically 0° to 90°
  - Home position: Usually 0° (level)

## 3. Servo Configuration

For each servo motor, specify:

- **Center Position** (`center_us`):
  - Microsecond value at 0° (usually 1500)
  - Example: 1500

- **Range** (`range_us`):
  - Microseconds per 90° (usually ±1000 for ±90°)
  - Example: 1000

- **Direction** (`direction`):
  - 1 = normal, -1 = reversed
  - Example: 1

- **Angle per Microsecond** (`angle_per_us`):
  - Degrees per microsecond (usually 0.09°/us for ±90° = ±1000us)
  - Example: 0.09

**Gripper Servo:**
- **Open Position** (`open_us`): Microseconds when gripper is open
- **Closed Position** (`closed_us`): Microseconds when gripper is closed
- Example: open=1200, closed=1800

## 4. Mounting Position

Where is the arm base located relative to the table coordinate system?

- **Arm Base X** (`arm_base_x_m`):
  - X position of arm base in table coordinates (meters)
  - Example: 0.0 (center) or -0.20 (20cm left)

- **Arm Base Y** (`arm_base_y_m`):
  - Y position of arm base in table coordinates (meters)
  - Example: 0.0 (center) or 0.30 (30cm forward)

- **Arm Base Z** (`arm_base_z_m`):
  - Height of arm base above table (meters)
  - Usually 0.0 if base is on table

- **Base Rotation Offset** (`base_rotation_offset_deg`):
  - Any rotation offset of arm base relative to table coordinate system
  - Example: 0° (aligned) or 45° (rotated)

## 5. Workspace Constraints

What are the physical limits of your arm?

- **Maximum Reach** (`max_reach_m`):
  - Maximum distance arm can reach from base (meters)
  - Usually: upper_arm + lower_arm
  - Example: 0.35m

- **Minimum Reach** (`min_reach_m`):
  - Minimum distance arm can reach (due to joint limits)
  - Example: 0.05m

- **Maximum Height** (`max_height_m`):
  - Maximum height arm can reach above table (meters)
  - Example: 0.30m

- **Minimum Height** (`min_height_m`):
  - Minimum height arm can reach (table surface)
  - Example: 0.02m (2cm above table)

## 6. Coordinate System

Define your table coordinate system:

- **Origin**: Where is (0, 0) on the table?
  - Usually center of table or corner

- **X-axis**: Which direction is positive X?
  - Usually: right = positive

- **Y-axis**: Which direction is positive Y?
  - Usually: forward = positive

- **Z-axis**: Which direction is positive Z?
  - Usually: up = positive

## How to Provide This Information

1. **Fill out the template**: Use `arm_spec_template.json` as a starting point
2. **From your CAD model**: Measure the link lengths and joint positions
3. **From servo datasheets**: Get servo specifications
4. **From physical testing**: Test joint limits and workspace

## Example

For a typical desktop robot arm:
```json
{
  "arm_geometry": {
    "shoulder_height_m": 0.10,
    "upper_arm_length_m": 0.15,
    "lower_arm_length_m": 0.12,
    "wrist_offset_m": 0.0,
    "gripper_length_m": 0.04
  },
  "joint_limits_deg": {
    "base": {"min": -180, "max": 180, "home": 0},
    "shoulder": {"min": -45, "max": 90, "home": 45},
    "elbow": {"min": 0, "max": 135, "home": 90},
    "wrist": {"min": -60, "max": 60, "home": 0}
  },
  "mounting": {
    "arm_base_x_m": 0.0,
    "arm_base_y_m": 0.0,
    "arm_base_z_m": 0.0,
    "base_rotation_offset_deg": 0
  }
}
```

Once you provide these specifications, I can update the kinematics system to match your exact arm design!

