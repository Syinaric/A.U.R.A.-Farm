# ESP32 Upload Guide

## Quick Start - Arduino IDE

### Step 1: Install Arduino IDE
1. Download from: https://www.arduino.cc/en/software
2. Install and open Arduino IDE

### Step 2: Add ESP32 Board Support

**On Mac:**
1. **Arduino > Preferences** (or press `Cmd + ,`)
2. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Click OK

**On Windows/Linux:**
1. **File > Preferences** (or press `Ctrl + ,`)
2. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Click OK

4. **Tools > Board > Boards Manager**
5. Search for "ESP32"
6. Install "esp32 by Espressif Systems" (latest version)
7. Close Boards Manager

### Step 3: Install ESP32Servo Library
1. **Tools > Manage Libraries**
2. Search for "ESP32Servo"
3. Install "ESP32Servo by Kevin Harrington"
4. Close Library Manager

### Step 4: Select Board and Port
1. **Tools > Board > ESP32 Arduino > ESP32 Dev Module**
2. **Tools > Port > Select your ESP32 port**
   - On Mac: Usually `/dev/cu.usbserial-*` or `/dev/cu.SLAB_USBtoUART`
   - On Windows: Usually `COM3`, `COM4`, etc.
   - On Linux: Usually `/dev/ttyUSB0` or `/dev/ttyACM0`

### Step 5: Upload Code
1. Open `esp32_servo_test.ino` in Arduino IDE
2. Click **Upload** button (→ arrow icon) or press `Ctrl+U` (Windows/Linux) / `Cmd+U` (Mac)
3. Wait for compilation and upload to complete
4. You should see "Done uploading" message

### Step 6: View Serial Output
1. Click **Serial Monitor** button (magnifying glass icon) or press `Ctrl+Shift+M` (Windows/Linux) / `Cmd+Shift+M` (Mac)
2. Set baud rate to **115200**
3. You should see test sequence output

## Troubleshooting

### "Port not found" or "No device found"
- **Check USB cable**: Use a data cable, not just a charging cable
- **Check drivers**: Install CP2102 or CH340 drivers if needed
- **Try different USB port**: Some ports may not work
- **Hold BOOT button**: Some ESP32 boards need BOOT button held during upload

### "Failed to connect to ESP32"
1. Hold **BOOT** button on ESP32
2. Press and release **RESET** button (while holding BOOT)
3. Release **BOOT** button
4. Try uploading again

### "Permission denied" (Linux/Mac)
```bash
# Add your user to dialout group (Linux)
sudo usermod -a -G dialout $USER
# Log out and back in

# Or use sudo (not recommended)
sudo chmod 666 /dev/ttyUSB0
```

### Upload keeps failing
1. **Check board selection**: Make sure "ESP32 Dev Module" is selected
2. **Check port**: Make sure correct port is selected
3. **Try different upload speed**: Tools > Upload Speed > 115200
4. **Disconnect other USB devices**: May cause conflicts
5. **Restart Arduino IDE**

### Servos don't move after upload
- **Check power supply**: Servos need external 5V power (not from ESP32)
- **Check ground connection**: Common ground between ESP32 and power supply
- **Check wiring**: Verify signal wires are on correct GPIO pins
- **Open Serial Monitor**: Check for error messages

## Current Servo Configuration

- **Base**: GPIO 5 (D5) - MG996R 180°
- **Shoulder**: GPIO 18 (D18) - MG996R 180°
- **Elbow**: GPIO 22 (D22) - MG996R 180°
- **Wrist**: GPIO 19 (D19) - 9g servo 180°

## Test Sequence

After upload, the code automatically runs:
1. Individual servo tests (each moves 0° → 90° → 180° → 90°)
2. All servos together (synchronized movement)
3. Smooth sweep test (each servo sweeps 0° to 180°)

All servos end at 90° (center position).

## Next Steps

After testing servos:
1. Verify all servos move correctly
2. Check if any servos need direction reversal
3. Calibrate servo centers if needed
4. Integrate with Python kinematics code

