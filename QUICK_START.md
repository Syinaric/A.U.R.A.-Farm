# Quick Start - Simple Pickup Sequence

## Problem
The ESP32 ports are busy (Arduino Serial Monitor is probably open).

## Solution

### Step 1: Close Arduino Serial Monitor
- Close the Serial Monitor window in Arduino IDE
- This will free up the ESP32 port

### Step 2: Run the Simple Pickup Sequence

**With ESP32 (auto-detect port):**
```bash
python simple_pickup.py --esp32
```

**With ESP32 (specify port):**
```bash
python simple_pickup.py --esp32 /dev/cu.usbserial-0001
```

**Simulation mode (no ESP32):**
```bash
python simple_pickup.py
```

## What It Does

The sequence will:
1. **Approach**: Move above cup (directly in front)
2. **Lower**: Go down to grab position
3. **Lift**: Lift up (grabs cup)
4. **Move Left**: Rotate base left
5. **Drop**: Lower to drop position
6. **Release**: Lift up (releases cup)
7. **Home**: Return to center position

## Adjusting Servo Positions

If the positions don't work perfectly, edit `simple_pickup.py` and adjust the `PICKUP_SEQUENCE` values:

```python
PICKUP_SEQUENCE = [
    {"name": "approach", "servos": [1500, 1300, 1700, 1500], "delay": 2.0},
    # Format: [base, shoulder, elbow, wrist]
    # 1500 = center (90°)
    # Lower = left/up, Higher = right/down
]
```

**Servo mapping:**
- **Base**: Lower = left, Higher = right
- **Shoulder**: Lower = arm up, Higher = arm down
- **Elbow**: Lower = elbow up, Higher = elbow down
- **Wrist**: Keep at 1500 for now

## Troubleshooting

### "Resource busy" error
- Close Arduino Serial Monitor
- Unplug and replug ESP32 USB cable
- Try the other port: `/dev/cu.SLAB_USBtoUART`

### Servos don't move correctly
- Adjust servo positions in `PICKUP_SEQUENCE`
- Increase delays if movements are too fast
- Check power supply (external 5V for servos)

### Need to test positions
Run in simulation mode first to see the commands:
```bash
python simple_pickup.py
```

This will print all servo commands without controlling the real arm.

