# Robot Arm Simulator

A macOS-compatible robot arm simulation system that uses webcam vision, natural language commands, and simulated servo control.

## Features

- **Webcam Integration**: Uses OpenCV to access Mac's webcam
- **Red Object Detection**: HSV color masking with centroid and bounding box visualization
- **Natural Language Processing**: Parses commands like "grab the red one and put it a little to the left"
- **Coordinate Conversion**: Maps pixel coordinates to table coordinates (meters)
- **Simulated Servo Control**: Generates microsecond commands for waypoint-based motion planning

## Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note**: On first run, macOS will prompt for camera access. Allow access in System Settings > Privacy & Security > Camera.

## Usage

### Test Camera

```bash
python cam_test.py
```

Press `q` to quit. If the camera shows black, try changing the index from `0` to `1` in the script.

### Run Main Simulation

```bash
python main_sim.py
```

**Controls:**
- `q`: Quit the application
- `c`: Enter a natural language command

**Example Commands:**
- `grab the red one and put it a little to the left`
- `pick red and move 5 cm forward`
- `nudge that 3 cm right`
- `open`
- `close`

The system will:
1. Detect red objects in the camera view
2. Parse your natural language command
3. Generate waypoint plan (above_pick → pick → above_drop → drop)
4. Output JSON servo commands for each waypoint

## Project Structure

```
robot-arm-sim/
├── cam_test.py       # Camera test script
├── detect.py         # Red object detection (HSV masking)
├── nlu.py            # Natural language parsing
├── kinematics.py     # Coordinate conversion and IK stubs
├── main_sim.py       # Main simulation loop
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Bird's Eye View Setup

The system is optimized for a **bird's eye view** (top-down) camera setup:

1. **Mount the camera** above the table looking straight down
2. **Calibrate the coordinate system** using the calibration script:
   ```bash
   python calibrate.py
   ```
   - Click on the table center to set origin
   - Click on points 10cm away to set scale
   - Press 's' to save calibration

3. **Adjust arm base position** in `calibration.json`:
   ```json
   {
     "arm_base_x": 0.0,  // Robot arm base X position in table coordinates
     "arm_base_y": 0.0   // Robot arm base Y position in table coordinates
   }
   ```

## Tuning

### HSV Color Detection (`detect.py`)

Adjust the HSV ranges for better color detection:
```python
mask = cv2.inRange(hsv, (0, 0, 0), (179, 255, 50))  # Black detection
```

### Coordinate Mapping (`kinematics.py`)

Calibration is saved in `calibration.json`. You can edit it directly or use `calibrate.py`:
- `origin_px`: Pixel coordinates of the table origin (center)
- `scale_x`, `scale_y`: Meters per pixel (default: 0.0015 m/px = 1.5 mm/px)
- `arm_base_x`, `arm_base_y`: Robot arm base position in table coordinates

## Command Schema

The system supports the following command structure:

- **Tasks**: `pick_place`, `nudge`, `open`, `close`
- **Targets**: `color` (red/green/blue/etc), `label` (apple/marker/cube/etc), `nearest`
- **Directions**: `left`/`right`, `forward`/`back`
- **Distances**: "a little/bit/slightly" (0.03m), or explicit "N cm/mm/m"

## Output Format

Servo commands are output as JSON:
```json
{"op": "j", "us": [1500, 1500, 1500, 1500, 1200], "wp": "above_pick"}
```

Where `us` is `[base, shoulder, elbow, wrist, grip]` in microseconds (900-2100 range).

## Coordinate System

The system displays coordinates in two formats:

1. **Pixel coordinates** (cx, cy): Raw camera pixel positions
2. **Table coordinates** (x, y): Real-world positions in meters relative to table origin

The system automatically:
- Converts pixel → table coordinates
- Calculates robot arm joint angles
- Generates servo commands for arm orientation

## Robot Arm Orientation

When an object is detected, the system calculates:
- **Base rotation** (yaw): Angle to rotate arm base toward target
- **Shoulder angle**: Upper arm pitch
- **Elbow angle**: Lower arm pitch  
- **Wrist angle**: Gripper orientation
- **Servo microseconds**: Commands for each servo

All calculations are displayed in the console and on the video feed.

