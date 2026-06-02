# Resource isolation Demo - NUC Master

This folder contains the NUC Master setup for the fail-operation demonstration.

## Prerequisites

### Required Docker Images

The following Docker images must be built beforehand:

- `failop-serial-bridge:latest` - Bridge connecting Arduino and KUKSA/Pullpiri
- `quay.io/eclipse-kuksa/kuksa-databroker:0.6.0` - KUKSA databroker (official image)

### Build Docker Images

```bash
# Build Serial bridge image
cd /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_master
docker compose build failop-serial-bridge
```

**Verify:**
```bash
docker images | grep failop-serial-bridge
# failop-serial-bridge   latest   ...
```

KUKSA databroker is automatically pulled from docker-compose.yml.

## Arduino Setup

See [arduino](./arduino/README.md) for details

**Summary:**
1. Fix device path with udev rules configuration
2. Compile and upload Arduino firmware
3. 3 boards: Joystick, LED, Gear

## Hardware Setup

- **3 Arduino UNO R4 WiFi boards:**
  - `ardn_stick` - Joystick with button (input)
  - `ardn_led` - NeoPixel LED strip (output)
  - `ardn_gear` - Rotary encoder with LED ring (input)

## Architecture

### Data Flow

1. **Joystick Button → LED + KUKSA**
   - `ardn_stick` detects button press/release
   - Sends signal to `bridge.py`
   - `bridge.py` forwards to:
     - Local `ardn_led` Arduino (GREEN on press, OFF on release)
     - KUKSA databroker (for Guest to receive)

2. **Rotary Encoder → Pullpiri**
   - `ardn_gear` detects rotation (CW/CCW)
   - `bridge.py` manages state-based filtering:
     - state=0 or -1: Only CW allowed → LAUNCH
     - state=1: Only CCW allowed → STOP
     - Invalid direction → RED LED
   - Sends YAML artifact to Pullpiri via HTTP API (`192.168.0.3:47099/api/artifact`)

## Components

### Arduino Programs

- `ardn_stick/ardn_stick.ino` - Joystick button detection
- `ardn_led/ardn_led.ino` - LED controller (GREEN/RED/OFF)
- `ardn_gear/ardn_gear.ino` - Rotary encoder with state machine

### Python Bridge

- `serial/bridge.py` - Main bridge connecting Arduino ↔ KUKSA ↔ Pullpiri
  - Main Thread: Joystick → DataBroker + LED Control
  - Thread-DB: DataBroker worker (queue consumer)
  - Thread-Gear: Gear → YAML artifacts (CW/CCW)

### Pullpiri YAML

- `pullpiri-yaml/yaml/container-launch.yaml` - Launch containers
- `pullpiri-yaml/yaml/container-stop.yaml` - Stop containers

## Running

### 1. Start Docker Compose

```bash
cd /sdv-blueprint/fail-operation/nuc_base/nuc_master
docker compose up -d
```

**Verify:**
```bash
docker compose ps
# NAME                   IMAGE                                          STATUS
# failop-databroker      quay.io/eclipse-kuksa/kuksa-databroker:0.6.0   Up
# failop-serial-bridge   failop-serial-bridge:latest                    Up
```

### 2. Stop

```bash
docker compose down
```
