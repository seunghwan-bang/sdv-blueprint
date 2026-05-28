# Fail Operation Demo - Multi-Node NUC Setup

The following instructions are based on a CentOS Stream environment with x86_64 architecture.

## Overview

This demo demonstrates **TIMPANI real-time signal-based LED control** vs **normal interval-based LED control** across a multi-node NUC setup. Under CPU load, the TIMPANI-controlled LED maintains precise 500ms intervals while the normal LED experiences delays.

## Hardware Setup

### Master Node (NUC #1)

| Device | Function | Serial Port |
|--------|----------|-------------|
| Arduino Joystick | Button input → KUKSA → CPU load control | `/dev/arduino_joystick` |
| Arduino Rotary | CW/CCW → Launch/Terminate containers | `/dev/arduino_gear` |
| Arduino LED | Status indicator (GREEN/RED/PURPLE) | `/dev/arduino_led` |

### Guest Node (NUC #2)

| Device | Function | Serial Port |
|--------|----------|-------------|
| Arduino LED (TIMPANI) | Controlled by TIMPANI signal (500ms) | `/dev/arduino_led_timpani` |
| Arduino LED (Normal) | Controlled by sleep interval (500ms) | `/dev/arduino_led_normal` |

## Data Flow

### 1. Container Lifecycle (Rotary Encoder)

```
Master: Rotary CW  →  serial-bridge  →  Pullpiri Master  →  Pullpiri Agent  →  Launch Containers
                              │                                    │
                              │                                    ├── led-timpani-controller
                              │                                    ├── led-normal-controller
                              │                                    └── kuksa-serial-bridge
                              │
Master: Rotary CCW →  serial-bridge  →  Pullpiri Master  →  Pullpiri Agent  →  Terminate Containers
```

### 2. CPU Load Control (Joystick Button)

```
Master: Joystick Press & Release →  serial-bridge  →  KUKSA Databroker  →  Guest kuksa-bridge  →  stress-ng START
Master: Joystick Press & Release →  serial-bridge  →  KUKSA Databroker  →  Guest kuksa-bridge  →  stress-ng STOP
```

### 3. LED Control (500ms interval)

```
┌─ TIMPANI Path ─────────────────────────────────────────────────────────────────┐
│ Timpani-O (Master)  →  Timpani-N (Guest)  →  led-timpani-controller  →  LED ON/OFF │
│                         (SIGRTMIN+2)          (precise timing)                    │
└───────────────────────────────────────────────────────────────────────────────────┘

┌─ Normal Path ──────────────────────────────────────────────────────────────────┐
│ led-normal-controller  →  sleep(0.5)  →  LED ON/OFF                            │
│ (affected by CPU load)                                                          │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## Test Procedure

### Prerequisites

- Pullpiri Master running on Master node
- Pullpiri Agent running on Guest node
- All Arduino devices connected and configured

### Step 1: Start Timpani-O (Master)

```bash
# On Master node
cd /TIMPANI/timpani-o/build
./timpani-o -c /pullpiri/examples/resources/timpani/node_configurations.yaml
```

> **Note**: Modify the configuration path according to your environment.

### Step 2: Launch Containers (Rotary CW)

Rotate the joystick **clockwise (CW)** to launch containers:
- LED turns **PURPLE** to indicate LAUNCH command sent
- Wait for containers to start on Guest

**Expected log on Master:**
```
Gear signal: CW
[Gear] State=0 + CW → LAUNCH (state becomes 1)
[POST] http://192.168.0.3:47099/api/artifact yaml=container-launch.yaml status=200
```

### Step 3: Start Timpani-N (Guest)

```bash
# On Guest node
cd /TIMPANI/timpani-n/build
sudo ./timpani-n -n guest -s -l 4 -P 80 192.168.0.3
```

> **Note**: Adjust parameters according to your environment.
> - `-n guest`: Node name
> - `-s`: Enable signal delivery
> - `-l 4`: Log level
> - `-P 80`: Priority
> - `192.168.0.3`: Master IP address

### Step 4: CPU Load Test (Joystick Button)

Press and release the joystick button to toggle CPU load:

| Action | Result |
|--------|--------|
| **Press & Release** | `stress-ng` starts → CPU load ON |
| **Press & Release** | `stress-ng` stops → CPU load OFF |

**Observe Grafana dashboard** at `http://<guest-ip>:3000`:
- TIMPANI LED maintains ~500ms interval under load
- Normal LED interval increases under load (>500ms)

### Step 5: Check Logs

```bash
# On Guest node
sudo podman logs -f led_normal_model_led_normal
sudo podman logs -f led_timpani_model_led_timpani
```