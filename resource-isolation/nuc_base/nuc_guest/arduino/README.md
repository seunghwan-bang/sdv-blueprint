# Fail Operation Demo - NUC Guest

The following instructions are based on a CentOS Stream environment with x86_64 architecture.

## Overview

This demo demonstrates **TIMPANI-based real-time LED control** vs **normal interval-based LED control** to visualize the difference in timing precision under CPU load.

## Quick Start

### 1. Setup Arduino Devices

```bash
cd arduino
./compile.sh    # Compile sketches
./install.sh    # Upload to devices (check ACM paths first)
```

See [arduino/README.md](./arduino/) for detailed instructions.

### 2. Build Docker Images

```bash
# LED TIMPANI Controller
cd led-timpani-controller
sudo podman build -t localhost/led-timpani-controller:latest .

# LED Normal Controller
cd ../led-normal-controller
sudo podman build -t localhost/led-normal-controller:latest .

# KUKSA Bridge
cd ../kuksa-bridge
sudo podman build -t localhost/failop-kuksa-bridge-guest:latest .
```

### 3. Start Monitoring

```bash
cd monitoring
./start.sh
# Access Grafana at http://localhost:3000 (admin/admin)
```

### 4. Run LED Controllers

The LED controllers are launched by **TIMPANI-N** orchestration.
See the orchestration YAML in the parent directory.

### 5. Trigger CPU Load

Button press on Master node triggers `stress-ng` via KUKSA bridge:
- **Button ON**: Starts `stress-ng --cpu 0 --cpu-method all`
- **Button OFF**: Kills all `stress-ng` processes

## Expected Results

| Condition | TIMPANI Controller | Normal Controller |
|-----------|-------------------|-------------------|
| No Load | 500ms interval | 500ms interval |
| CPU Load | **500ms interval** (precise) | **>500ms interval** (delayed) |

The Grafana dashboard visualizes this difference in real-time.

## Prerequisites

- **Arduino CLI**: For compiling and uploading sketches
- **Podman**: For container management
- **TIMPANI-N**: For real-time signal delivery
- **KUKSA Databroker**: Running on port 55556
- **stress-ng**: Installed on host or as container