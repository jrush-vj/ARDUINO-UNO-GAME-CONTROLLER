from flask import Flask, render_template, jsonify
import threading
import time
import logging
import json
import os
import sys
from queue import Queue

# Import vgamepad and serial, ensure they're installed
try:
    import vgamepad as vg
    import serial
except ImportError:
    print("Missing required packages. Install with: pip install vgamepad pyserial")
    sys.exit(1)

# Constants
SERIAL_PORT = 'COM5'  # Change this to your Arduino port
BAUD_RATE = 9600
RECONNECT_DELAY = 3
JOYSTICK_DEADZONE_LEFT = 0   # Deadzone for movement (left stick)
JOYSTICK_DEADZONE_RIGHT = 0  # Deadzone for camera (right stick)
TRIGGER_DEADZONE = 10

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Create a queue for passing gamepad data to the web interface
gamepad_data_queue = Queue(maxsize=1)
# Global state for connection status
arduino_connected = False

class ArduinoGamepad:
    def __init__(self, port=SERIAL_PORT, baud_rate=BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.gamepad = vg.VX360Gamepad()
        self.running = True
        
        self.button_map = {
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "LSW": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "RSW": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER
        }
        self.button_states = {btn: False for btn in self.button_map}
        self.current_lx = self.current_ly = self.current_rx = self.current_ry = 0
        self.current_lt = self.current_rt = 0
        self.connect()

    def connect(self):
        global arduino_connected
        try:
            if self.ser: self.ser.close()
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)
            logger.info(f"Connected to Arduino on {self.port}")
            self.ser.flushInput()
            self.reset_controller_state()
            arduino_connected = True
            return True
        except Exception as e:
            arduino_connected = False
            logger.error(f"Connection error: {e}")
            return False

    def reset_controller_state(self):
        for button in self.button_map.values():
            self.gamepad.release_button(button)
        self.gamepad.left_joystick(0, 0)
        self.gamepad.right_joystick(0, 0)
        self.gamepad.left_trigger(0)
        self.gamepad.right_trigger(0)
        self.gamepad.update()

    def map_joystick(self, val, axis=''):
        centered = val - 512
        deadzone = JOYSTICK_DEADZONE_LEFT if 'L' in axis else JOYSTICK_DEADZONE_RIGHT
        if abs(centered) < deadzone // 2:
            return 0
        return int((centered / 511.0) * 32767 if centered > 0 else (centered / 512.0) * 32768)


    def map_trigger(self, val, max_input=512):
        if val < TRIGGER_DEADZONE:
            return 0
        norm = min(val, max_input) / max_input
        return min(255, int(norm * norm * 255))  # Non-linear curve for analog feel

    def update_button(self, name, is_pressed):
        if name not in self.button_map:
            return False
        button_enum = self.button_map[name]
        if is_pressed != self.button_states[name]:
            (self.gamepad.press_button if is_pressed else self.gamepad.release_button)(button_enum)
            self.button_states[name] = is_pressed
            return True
        return False

    def run(self):
        global arduino_connected
        logger.info("Controller active. Thread running.")
        changes_detected = False
        last_update_time = time.time()

        while self.running:
            try:
                if not self.ser or not self.ser.is_open:
                    logger.warning("Serial disconnected. Reconnecting...")
                    arduino_connected = False
                    if not self.connect():
                        time.sleep(RECONNECT_DELAY)
                        continue

                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 12:
                    continue

                try:
                    xL = self.map_joystick(int(parts[0]), 'xL')
                    yL = self.map_joystick(int(parts[1]), 'yL')
                    xR_raw = int(parts[2])
                    yR_raw = int(parts[3])
                    xR = self.map_joystick(xR_raw, 'xR')
                    yR = -self.map_joystick(1023 - yR_raw, 'yR')  # Inverted Y
                    lt = self.map_trigger(int(parts[4]), max_input=512)
                    rt = self.map_trigger(int(parts[5]), max_input=512)
                    y_btn = int(parts[6])
                    a_btn = int(parts[7])
                    x_btn = int(parts[8])
                    b_btn = int(parts[9])
                    lsw = int(parts[10])
                    rsw = int(parts[11])
                    
                    # Update the data queue with the latest controller state
                    gamepad_data = {
                        'axes': [
                            xL / 32767.0, yL / 32767.0,  # Left stick
                            xR / 32767.0, yR / 32767.0,  # Right stick
                        ],
                        'buttons': [
                            {'pressed': bool(a_btn), 'value': float(a_btn)},  # A
                            {'pressed': bool(b_btn), 'value': float(b_btn)},  # B
                            {'pressed': bool(x_btn), 'value': float(x_btn)},  # X
                            {'pressed': bool(y_btn), 'value': float(y_btn)},  # Y
                            {'pressed': bool(lsw), 'value': float(lsw)},      # Left shoulder
                            {'pressed': bool(rsw), 'value': float(rsw)},      # Right shoulder
                            {'pressed': lt > 0, 'value': lt / 255.0},         # Left trigger
                            {'pressed': rt > 0, 'value': rt / 255.0},         # Right trigger
                        ],
                        'id': 'Arduino Custom Gamepad',
                        'index': 0,
                        'connected': True,
                        'mapping': 'standard'
                    }
                    
                    # Update the queue with fresh data
                    if gamepad_data_queue.full():
                        gamepad_data_queue.get()
                    gamepad_data_queue.put(gamepad_data)
                    
                except Exception as e:
                    logger.error(f"Data parsing error: {e}")
                    continue

                if any(abs(v1 - v2) > 1000 for v1, v2 in zip((xL, yL, xR, yR), (self.current_lx, self.current_ly, self.current_rx, self.current_ry))):
                    self.gamepad.left_joystick(xL, yL)
                    self.gamepad.right_joystick(xR, yR)
                    self.current_lx, self.current_ly = xL, yL
                    self.current_rx, self.current_ry = xR, yR
                    changes_detected = True

                if abs(lt - self.current_lt) > 5 or abs(rt - self.current_rt) > 5:
                    self.gamepad.left_trigger(lt)
                    self.gamepad.right_trigger(rt)
                    self.current_lt, self.current_rt = lt, rt
                    changes_detected = True

                changes_detected |= self.update_button("Y", y_btn)
                changes_detected |= self.update_button("A", a_btn)
                changes_detected |= self.update_button("X", x_btn)
                changes_detected |= self.update_button("B", b_btn)
                changes_detected |= self.update_button("LSW", lsw)
                changes_detected |= self.update_button("RSW", rsw)

                if changes_detected or time.time() - last_update_time > 0.1:
                    self.gamepad.update()
                    last_update_time = time.time()
                    changes_detected = False

            except Exception as e:
                logger.error(f"Loop error: {e}")
                arduino_connected = False
                time.sleep(0.1)

    def cleanup(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.reset_controller_state()
        logger.info("Cleanup done.")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({
        'arduino_connected': arduino_connected
    })

@app.route('/gamepad-data')
def gamepad_data():
    try:
        # Get latest data if available, otherwise return empty state
        if not gamepad_data_queue.empty():
            data = gamepad_data_queue.get()
            return jsonify(data)
        else:
            return jsonify({
                'connected': arduino_connected,
                'axes': [0, 0, 0, 0],
                'buttons': [
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                    {'pressed': False, 'value': 0},
                ],
                'id': 'Arduino Custom Gamepad (No Data)',
                'index': 0,
                'mapping': 'standard'
            })
    except Exception as e:
        logger.error(f"Error getting gamepad data: {e}")
        return jsonify({'error': str(e)}), 500

# Create controller thread
def start_controller():
    port = os.environ.get('ARDUINO_PORT', SERIAL_PORT)
    controller = ArduinoGamepad(port=port)
    try:
        controller.run()
    finally:
        controller.cleanup()

if __name__ == '__main__':
    # Start the controller in a separate thread
    controller_thread = threading.Thread(target=start_controller)
    controller_thread.daemon = True
    controller_thread.start()
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)