# KUKSA Bridge - Fail Operation Guest

KUKSA databroker subscriber running on NUC Guest.
Receives button events and triggers CPU workload via shell scripts.

## Overview

This bridge subscribes to `Vehicle.Cabin.FailOperation.ButtonPressed` signal from KUKSA databroker.
When a button press is detected, it toggles the `stress-ng` workload to simulate CPU load.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Master Node    │────▶│  KUKSA Broker   │────▶│  KUKSA Bridge   │
│  (Button Press) │     │  (Port 55556)   │     │  (this)         │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   stress-ng     │
                                                │   (CPU Load)    │
                                                └─────────────────┘
```

## Configuration

Container settings are managed via the `.env` file.

### .env File Format

```bash
# Shell scripts for toggle mode
TRIGGER_ON_SCRIPT=/app/script/trigger-on.sh
TRIGGER_OFF_SCRIPT=/app/script/trigger-off.sh
```

## Build

```bash
cd /home/lge/Desktop/new/sdv-blueprint/fail-operation/nuc_base/nuc_guest/kuksa-bridge
sudo podman build -t localhost/failop-kuksa-bridge-guest:latest .
```

## Run

```bash
sudo podman run --rm -d \
  --name failop-kuksa-bridge-guest \
  --network host \
  --privileged \
  -v /home/lge/Desktop/new/sdv-blueprint/fail-operation/nuc_base/nuc_guest/kuksa-bridge/.env:/app/.env:ro \
  -v /home/lge/Desktop/new/sdv-blueprint/fail-operation/nuc_base/nuc_guest/script:/app/script:ro \
  -e PYTHONUNBUFFERED=1 \
  localhost/failop-kuksa-bridge-guest:latest
```

## Logs

```bash
# Real-time log monitoring
sudo podman logs failop-kuksa-bridge-guest -f

# Recent logs
sudo podman logs failop-kuksa-bridge-guest --tail=20
```

## Behavior

1. **KUKSA Databroker Connection**
   - Port: `55556` (fail-operation databroker)
   - Signal: `Vehicle.Cabin.FailOperation.ButtonPressed`

2. **Button Event Handling**
   - Button PRESSED (toggle ON) → Execute `trigger-on.sh`
   - Button PRESSED (toggle OFF) → Execute `trigger-off.sh`

3. **Workload Control**
   - ON: `stress-ng --cpu 0 --cpu-method all --timeout 0`
   - OFF: `killall -9 stress-ng`

## Shell Scripts

### trigger-on.sh
- Kills any existing stress-ng processes
- Starts stress-ng in background using nohup+disown
- Uses all CPU cores with various stress methods

### trigger-off.sh
- Terminates all stress-ng processes
- Verifies clean termination

## Notes

- The bridge runs in toggle mode: each button press alternates ON/OFF
- `stress-ng` runs in background, detached from the bridge process
- `.env` changes take effect on next button event (no restart needed)
- Requires `--privileged` for process management on host

