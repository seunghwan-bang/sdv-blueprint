# Serial Bridge

Python serial bridge connecting Arduino devices to KUKSA Databroker and Pullpiri.

## Overview

This bridge reads input from Arduino devices and:
1. Sends joystick button state to KUKSA Databroker
2. Sends YAML artifacts to Pullpiri based on rotary encoder input
3. Controls LED colors on Arduino devices

## Build

```bash
sudo podman build -t localhost/failop-serial-bridge:latest .
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABROKER_IP` | `failop-databroker` | KUKSA Databroker hostname/IP |
| `DATABROKER_PORT` | `55555` | KUKSA Databroker port |
| `MASTER_IP` | `192.168.0.3` | Pullpiri server IP (on Guest) |

## Serial Ports

| Port | Device | Direction |
|------|--------|-----------|
| `/dev/arduino_joystick` | Joystick button | Input |
| `/dev/arduino_led` | NeoPixel LED | Output |
| `/dev/arduino_gear` | Rotary encoder + LED | Input/Output |

## Data Flow

### Joystick → KUKSA + LED

1. Button press detected → Queue message `True`
2. Thread-DB sends to DataBroker: `Vehicle.Cabin.FailOperation.ButtonPressed=True`
3. Main thread sends `GREEN\n` to LED Arduino
4. Button release → Same flow with `False` and `OFF\n`

### Rotary Encoder → Pullpiri

State machine controls allowed directions:

| Current State | Input | Action | LED Color | Next State |
|---------------|-------|--------|-----------|------------|
| 0 (INIT) | CW | LAUNCH | PURPLE | 1 |
| 0 (INIT) | CCW | Ignored | RED | 0 |
| 1 (LAUNCHED) | CCW | STOP | GREEN | -1 |
| 1 (LAUNCHED) | CW | Ignored | RED | 1 |
| -1 (STOPPED) | CW | LAUNCH | PURPLE | 1 |
| -1 (STOPPED) | CCW | Ignored | RED | -1 |

## YAML Artifacts

Located in `/yaml/` directory (mounted volume):
- `container-launch.yaml` - Sent on CW rotation (LAUNCH)
- `container-stop.yaml` - Sent on CCW rotation (STOP)

