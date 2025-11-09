"""
ESP32 Serial Communication Module
Handles communication between Python and ESP32 for servo control.
"""
import serial
import serial.tools.list_ports
import json
import time
import sys


class ESP32Controller:
    """Controller for ESP32 robot arm via serial communication."""
    
    def __init__(self, port=None, baud_rate=115200, timeout=1.0):
        """
        Initialize ESP32 controller.
        
        Args:
            port: Serial port (e.g., '/dev/cu.usbserial-*' on Mac, 'COM3' on Windows)
                 If None, will try to auto-detect ESP32
            baud_rate: Serial baud rate (default: 115200)
            timeout: Serial timeout in seconds (default: 1.0)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn = None
        self.connected = False
        
    def find_esp32_port(self):
        """
        Try to auto-detect ESP32 serial port.
        
        Returns:
            str: Port name if found, None otherwise
        """
        # Common ESP32 USB-to-Serial chip identifiers
        esp32_identifiers = [
            'CP210',  # Silicon Labs CP210x
            'CH340',  # WCH CH340
            'CH341',  # WCH CH341
            'FTDI',   # FTDI
            'USB Serial',  # Generic
            'SLAB',   # Silicon Labs
        ]
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            description = port.description.upper()
            for identifier in esp32_identifiers:
                if identifier.upper() in description:
                    print(f"Found potential ESP32: {port.device} - {port.description}")
                    return port.device
        
        return None
    
    def connect(self):
        """
        Connect to ESP32 via serial.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.connected and self.serial_conn and self.serial_conn.is_open:
            return True
        
        # Auto-detect port if not specified
        if self.port is None:
            self.port = self.find_esp32_port()
            if self.port is None:
                print("Error: Could not find ESP32. Please specify port manually.")
                return False
        
        try:
            print(f"Connecting to ESP32 on {self.port} at {self.baud_rate} baud...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            time.sleep(2)  # Wait for ESP32 to reset
            self.connected = True
            print(f"Connected to ESP32 successfully!")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to ESP32: {e}")
            print(f"Available ports:")
            for port in serial.tools.list_ports.comports():
                print(f"  - {port.device}: {port.description}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False
        print("Disconnected from ESP32")
    
    def send_command(self, command):
        """
        Send command to ESP32.
        
        Args:
            command: dict with command data
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Convert command to JSON string
            json_str = json.dumps(command) + '\n'
            self.serial_conn.write(json_str.encode('utf-8'))
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
            return False
    
    def set_servos(self, base_us, shoulder_us, elbow_us, wrist_us):
        """
        Set all servo positions using microsecond values.
        
        Args:
            base_us: Base servo microseconds (900-2100)
            shoulder_us: Shoulder servo microseconds (900-2100)
            elbow_us: Elbow servo microseconds (900-2100)
            wrist_us: Wrist servo microseconds (900-2100)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        command = {
            "op": "servos",
            "base": int(base_us),
            "shoulder": int(shoulder_us),
            "elbow": int(elbow_us),
            "wrist": int(wrist_us)
        }
        return self.send_command(command)
    
    def set_servos_from_us_list(self, us_list):
        """
        Set all servos from a list of microsecond values.
        
        Args:
            us_list: [base_us, shoulder_us, elbow_us, wrist_us]
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if len(us_list) != 4:
            print(f"Error: Expected 4 servo values, got {len(us_list)}")
            return False
        return self.set_servos(us_list[0], us_list[1], us_list[2], us_list[3])
    
    def read_response(self, timeout=0.5):
        """
        Read response from ESP32.
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            str: Response string, or None if timeout
        """
        if not self.connected:
            return None
        
        try:
            old_timeout = self.serial_conn.timeout
            self.serial_conn.timeout = timeout
            response = self.serial_conn.readline().decode('utf-8').strip()
            self.serial_conn.timeout = old_timeout
            return response if response else None
        except Exception as e:
            print(f"Error reading response: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def test_connection(port=None):
    """Test ESP32 connection."""
    controller = ESP32Controller(port=port)
    if controller.connect():
        print("Connection test successful!")
        controller.disconnect()
        return True
    else:
        print("Connection test failed!")
        return False


if __name__ == "__main__":
    # Test connection
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = None
    
    test_connection(port)

