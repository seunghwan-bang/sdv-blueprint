# Fail Operation Demo - NUC Guest

This folder contains the NUC Guest setup for the fail-operation demonstration.

## Purpose

The Guest node:
1. Subscribes to KUKSA databroker for button press signals
2. Executes workload containers when button is pressed
3. Receives Pullpiri commands to launch/terminate containers

## Components

### KUKSA Bridge

- `kuksa-bridge/bridge.py` - Subscribes to `Vehicle.Cabin.FailOperation.ButtonPressed`
- When button is pressed, runs a shell script to start or stop the stress-ng process

## Container Execution

### Button Press (via KUKSA)
- Triggered by joystick button on Master
- Executes: `podman run stress-ng --cpu 2 --timeout 30s`

### Rotary Encoder (via Pullpiri)
- Triggered by gear rotation on Master
- Pullpiri manages container lifecycle based on YAML specs

## Running the Bridge

```bash
cd kuksa-bridge/
python bridge.py
```

Or use Docker Compose (see parent folder).

## Prerequisites

- KUKSA databroker must be accessible at `databroker:55555`
- Podman installed and accessible
- Stress-ng container image available: `localhost/stress-ng:latest`

## Building Stress-ng Container

```bash
podman build -t stress-ng - <<EOF
FROM alpine:latest
RUN apk add --no-cache stress-ng
ENTRYPOINT ["stress-ng"]
EOF
```
