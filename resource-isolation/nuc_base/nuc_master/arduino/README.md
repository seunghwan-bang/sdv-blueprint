# Fail Operation Demo with Arduino

Run on NUC (Master) using CentOS Stream with x86_64 architecture

## Prerequisites

### Fix Device Path

The `/dev/ttyACMx` path can change each time a device is connected, so it needs to be fixed

The `99-arduino.rules` file is structured as follows

```
# Joystick Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="48CA435E506C", SYMLINK+="arduino_joystick"

# LED Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="F0F5BD507E9C", SYMLINK+="arduino_led"

# Gear Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="D885ACA7070C", SYMLINK+="arduino_gear"
```

Here, `2341` is Arduino's vendor code, and each device's serial can be verified with the command below.

```bash
udevadm info -a -n /dev/ttyACM0 | grep '{serial}' -m 1
```

`ttyACM0` increments each time an Arduino device is connected. You can see which path it connected to using the `arduino-cli board list` command.

Finally, run the following command to verify it was created correctly

```bash
sudo cp 99-arduino.rules /etc/udev/rules.d/99-arduino.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -al /dev/arduino_*
```

**Expected result:**
```
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_gear -> ttyACM0
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_joystick -> ttyACM2
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_led -> ttyACM1
```

## Arduino Setup

This project uses 3 Arduino UNO R4 WiFi boards:

- **ardn_stick**: Joystick button input (detects button press/release)
- **ardn_led**: NeoPixel LED control (receives GREEN/RED/OFF commands)
- **ardn_gear**: Rotary encoder input + NeoPixel LED (detects CW/CCW, displays color)

## Compile

The following library needs to be installed to use LED.

```bash
arduino-cli lib install "Adafruit NeoPixel"
```

Run `compile.sh` to compile. The `.ino` filename must match the folder name for compilation.

```bash
./compile.sh
```

**Internal operation:**
```bash
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_stick
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_led
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_gear
```

If compilation completes successfully, you should see the following logs.

```
Sketch uses 52224 bytes (19%) of program storage space. Maximum is 262144 bytes.
Global variables use 6740 bytes (20%) of dynamic memory, leaving 26028 bytes for local variables. Maximum is 32768 bytes.
```

## Install

Run `install.sh` to install. However, there are some precautions.

```bash
./install.sh
```

**Internal operation:**
```bash
arduino-cli upload -p /dev/ttyACM2 --fqbn arduino:renesas_uno:unor4wifi ardn_stick
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:renesas_uno:unor4wifi ardn_led
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi ardn_gear
```

As shown in the script above, the installation requires the original path instead of `/dev/arduino_*`.
Therefore, you must match the folder and device paths correctly using `ls -al /dev/arduino_*`.

## Arduino Program Description

### ardn_stick (Joystick)
- **Pin configuration**: Pin 8 (Joystick SW)
- **Function**: Detects button press/release
- **Output**: Sends "1" (press) or "0" (release) via serial
- **Usage**: Received by bridge.py to send DataBroker + LED control

### ardn_led (LED Controller)
- **Pin configuration**: Pin 6 (NeoPixel data)
- **Function**: Receives serial commands to change LED color
- **Commands**:
  - `GREEN\n`: Display green
  - `RED\n`: Display red
  - `OFF\n`: Turn off LED

### ardn_gear (Rotary Encoder + LED)
- **Pin configuration**:
  - Pin 5, 6: Rotary encoder A/B
  - Pin 7: Encoder button
  - Pin 8: NeoPixel data
- **Function**: 
  - Detects rotation direction (CW/CCW)
  - Sends "CW" or "CCW" via serial
  - Receives color commands from bridge.py (PURPLE/GREEN/RED)
- **State Machine**: 
  - Initial state=0: Only CW allowed → LAUNCH
  - state=1: Only CCW allowed → STOP
  - Invalid direction input shows red LED

## Debugging

To check the serial output of each Arduino directly:

```bash
# Joystick monitoring
arduino-cli monitor -p /dev/ttyACM2 -c baudrate=115200

# LED monitoring
arduino-cli monitor -p /dev/ttyACM1 -c baudrate=115200

# Gear monitoring
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```
