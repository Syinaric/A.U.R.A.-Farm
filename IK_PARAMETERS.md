# Inverse Kinematics Parameters

## Current Arm Configuration (4-DOF)

### Servo Configuration
- **Base**: D5 - MG996R 180° (rotation/yaw)
- **Shoulder**: D18 - MG996R 180° (pitch)
- **Elbow**: D22 - MG996R 180° (pitch)
- **Wrist**: D19 - 9g servo 180° (x-axis rotation, up/down pitch)
- **Gripper**: None (hand is locked in position)

### Arm Geometry (from arm_spec_template.json)
- **Base height**: 61.2mm (0.0612m) - from table to base
- **Shoulder height**: 95mm (0.095m) - from table to shoulder joint
- **Upper arm length**: 12cm (0.12m) - shoulder to elbow
- **Lower arm length**: 9cm (0.09m) - elbow to wrist
- **Hand length**: 6cm (0.06m) - wrist to grabbing point (hand extends downward)

### Joint Limits
- **Base**: -180° to +180° (full rotation)
- **Shoulder**: -90° to +90° (from arm_spec, adjust if needed)
- **Elbow**: 0° to 180° (from arm_spec, adjust if needed)
- **Wrist**: -90° to +90° (x-axis rotation, up/down)

### Servo Mapping
- **Center position**: 1500μs
- **Range**: ±600μs for ±90°
- **Formula**: `us = 1500 + (angle_deg / 90) * 600`
- **Limits**: 900μs to 2100μs

### Workspace
- **Max reach**: ~0.21m (upper_arm + lower_arm = 0.12 + 0.09)
- **Min reach**: ~0.05m
- **Max height**: ~0.30m (from table)
- **Min height**: ~0.005m (5mm - as low as possible for grabbing)
- **Total reach**: ~0.27m (includes hand length for grabbing point)

## Inverse Kinematics Calculation

### Steps:
1. **Base rotation**: Calculate angle to target in XY plane
   - `base_angle = atan2(rel_y, rel_x)`

2. **Shoulder-Elbow-Wrist chain**:
   - Input (x, y, z) is the desired grabbing point position
   - Adjust target: wrist position = (x, y, z + hand_length) since hand extends downward
   - Calculate distance from shoulder to wrist in 3D
   - Use law of cosines for 2-link arm
   - Calculate shoulder and elbow angles
   - Wrist compensates to keep hand level

3. **Wrist angle**: 
   - `wrist_angle = -(shoulder_angle + elbow_angle - 90)`
   - Keeps hand perpendicular to ground for grabbing

### Required Parameters for Accurate IK:

1. **Physical dimensions** (already in arm_spec_template.json):
   - Base height
   - Shoulder height
   - Upper arm length
   - Lower arm length
   - Hand length (6cm - wrist to grabbing point)
   - Wrist offset (if any)

2. **Joint limits** (verify these match your hardware):
   - Base: -180° to +180°
   - Shoulder: -90° to +90° (verify)
   - Elbow: 0° to 180° (verify)
   - Wrist: -90° to +90° (verify)

3. **Servo calibration**:
   - Center position (typically 1500μs)
   - Angle per microsecond
   - Direction (normal or reversed)

4. **Mounting position**:
   - Arm base X, Y position in table coordinates
   - Base rotation offset (if arm is rotated)

## Harvesting Sequence

The harvesting sequence uses these waypoints:
1. **Approach**: Move above cup (10cm high)
2. **Lower**: Go as low as possible (5mm) to grab tapered objects
3. **Lift**: Lift directly up (10cm) - this grabs the object
4. **Move side**: Move 5cm to the right
5. **Drop**: Lower and release (5mm)

The hand is locked in position, so the grabbing motion relies on:
- Lowering to minimum height (5mm)
- Lifting directly up
- The tapered shape of objects allows them to be grabbed by the fixed hand

