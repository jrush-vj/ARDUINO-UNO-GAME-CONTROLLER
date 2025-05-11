# 🎮 Arduino-Based Custom Game Controller

Build your **own game controller** using an Arduino Uno and interface it with any Windows PC as an Xbox 360 controller using Python and the `vgamepad` library.

---

## 🚀 Installation & Setup

### 1. 🖼️ Circuit Diagram

Connect components as follows:

| Component        | Arduino Pin |
|------------------|-------------|
| Left Joystick X  | A0          |
| Left Joystick Y  | A1          |
| Right Joystick X | A2          |
| Right Joystick Y | A3          |
| LT Trigger Axis  | A4          |
| RT Trigger Axis  | A5          |
| Button Y         | 2           |
| Button X         | 3           |
| Button A         | 4           |
| Button B         | 5           |
| LSW (LB)         | 6           |
| RSW (RB)         | 7           |

> 🧰 Tools like [Fritzing](https://fritzing.org/) can help you create a visual wiring diagram.

---

### 2. 💻 Arduino Sketch Upload
- Connect the Arduino UNO Setup
- Open Arduino IDE.
- Copy-paste the Arduino code into a new sketch.
- Select `Arduino Uno` from Tools > Board.
- Select the correct COM port under Tools > Port.
- Upload the sketch.
  
    ![Screenshot 2025-05-11 194858](https://github.com/user-attachments/assets/c7620eda-177d-4ce6-821f-97aeae919e0b)

- **IMPORTANT NOTE: AFTER UPLOADING SKETCH, MUST CLOSE ARDUINO IDE**  
---

### 3. 🐍 Python Setup

> 🐍 Python 3.10 or higher is recommended

Install required libraries:

```bash
pip install pyserial vgamepad
```
- Install ViGEmBus Driver (required for vgamepad on Windows):
  > Download from: ViGEmBus Releases

-Run the installer and complete setup.

### ▶️ Run the Gamepad Emulator

- Run the python file 'gamepad.py'
    
- If you see this output **CONGRATULATIONS!!! CODE IS WORKING**
    ![Screenshot 2025-05-11 195110](https://github.com/user-attachments/assets/4acba8f4-6014-4703-81a6-3f715a11fe38)
(IF NOT, MAKE SURE 'COM' PORT IS SAME IN BOTH ARDUINO SKETCH AND PYTHON FILE.)

- To CHECK if python code is working open this link.
    ![Screenshot 2025-05-11 195110](https://github.com/user-attachments/assets/41ac868f-03a1-4dc3-b3a5-ea2b1db85cf0)

---

### 🎥 Demo
Add a link to a YouTube video or GIF here
Example: Watch Demo on YouTube

### 📖 How It Works
The Arduino reads analog joystick and trigger inputs, as well as button states, and sends them as CSV-formatted data via serial.

The Python script reads the data, processes deadzones, filters, and maps it to Xbox controller inputs using the vgamepad library.

The ViGEm driver presents a virtual Xbox 360 controller to the operating system, compatible with most games and emulators.

🔭 Future Scope
Add Bluetooth using an HC-05 module

Use an OLED or LCD display for battery or mode info

Add DPAD and Start/Select buttons

Integrate vibration motors

Enclose in a 3D-printed case

Switch to native USB HID using Arduino Leonardo or Pro Micro


### 👨‍💻 Author
V Jerush Vijay
Student, REVA University

