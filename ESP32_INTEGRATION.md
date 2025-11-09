# ESP32 Integration Guide

## Overview

The Python vision and kinematics system can now control the real ESP32 robot arm in real-time. When a cup is detected and you press `g`, the system will:

1. Calculate inverse kinematics for each waypoint
2. Send servo commands to ESP32 via serial
3. Execute the harvesting sequence on the real robot arm

## Setup

### 1. Install Python Dependencies

```bash
pip install pyserial
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Upload ESP32 Control Code

1. Open `esp32_servo_control.ino` in Arduino IDE
2. Make sure you have:
   - ESP32 board support installed
   - ESP32Servo library installed
   - **ArduinoJson library installed** (required for JSON parsing)
     - Tools > Manage Libraries > Search "ArduinoJson" > Install
3. Upload to ESP32
4. Open Serial Monitor (115200 baud) to verify it's running

### 3. Connect ESP32 to Mac

- Connect ESP32 via USB cable
- Note the port name (e.g., `/dev/cu.usbserial-*` or `/dev/cu.SLAB_USBtoUART`)
- You can find it in Arduino IDE: Tools > Port

### 4. Run Python Code with ESP32

**Auto-detect port:**
```bash
python main_sim.py --esp32
```

**Specify port manually:**
```bash
python main_sim.py --esp32 /dev/cu.usbserial-*
```

**Simulation mode (no ESP32):**
```bash
python main_sim.py
```

## How It Works

### Communication Protocol

Python sends JSON commands to ESP32:
```json
{"op":"servos","base":1500,"shoulder":1500,"elbow":1500,"wrist":1500}
```

ESP32 responds with:
```
OK: servos set to 1500,1500,1500,1500
```

### Servo Control

- **Base (D5)**: MG996R 180°
- **Shoulder (D18)**: MG996R 180°
- **Elbow (D22)**: MG996R 180°
- **Wrist (D19)**: 9g servo 180°

Servo microseconds range: 900-2100
- 1500 = center (90°)
- 900 = -90° (or 0° depending on servo)
- 2100 = +90° (or 180° depending on servo)

### Harvesting Sequence

When you press `g` with a cup detected:

1. **Approach**: Move above cup (10cm high)
2. **Lower**: Go to minimum height (5mm) to grab tapered objects
3. **Lift**: Lift directly up (10cm) - this grabs the object
4. **Move side**: Move 5cm to the right
5. **Drop**: Lower and release (5mm)

Each waypoint:
- Calculates inverse kinematics
- Converts to servo microseconds
- Sends command to ESP32
- Waits 1 second for movement

## Troubleshooting

### "ESP32 control not available"
- Install pyserial: `pip install pyserial`

### "Could not find ESP32"
- Check USB cable connection
- Verify ESP32 is powered
- Try specifying port manually: `python main_sim.py --esp32 /dev/cu.usbserial-*`
- Check Arduino IDE: Tools > Port to see available ports

### "Failed to connect to ESP32"
- Make sure ESP32 code is uploaded (`esp32_servo_control.ino`)
- Check Serial Monitor in Arduino IDE - ESP32 should be waiting for commands
- Verify baud rate is 115200
- Try unplugging and replugging USB cable

### "ERROR: Invalid JSON"
- Make sure ArduinoJson library is installed on ESP32
- Check ESP32 Serial Monitor for error details

### Servos don't move
- Check power supply (external 5V for servos)
- Verify common ground connection
- Check wiring (signal wires on correct GPIO pins)
- Verify servo code is uploaded (not test code)

### Servos move wrong direction
- May need to reverse servo direction in code
- Or adjust angle mapping in `kinematics.py`

## Testing

### Test ESP32 Connection

```bash
python esp32_control.py
```

Or with specific port:
```bash
python esp32_control.py /dev/cu.usbserial-*
```

### Test Servo Control

You can manually test servos by running:
```python
from esp32_control import ESP32Controller

controller = ESP32Controller()
if controller.connect():
    # Set all servos to center
    controller.set_servos(1500, 1500, 1500, 1500)
    controller.disconnect()
```

## Next Steps

1. **Calibrate arm base position**: Update `arm_base_x` and `arm_base_y` in calibration
2. **Test harvesting sequence**: Place cup in front of camera, press `g`
3. **Adjust waypoints**: Modify heights and positions in `execute_harvesting_sequence()`
4. **Fine-tune servo centers**: Adjust if 90° isn't actually center for your servos

