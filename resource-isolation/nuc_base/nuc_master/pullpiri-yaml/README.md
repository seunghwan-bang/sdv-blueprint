# Pullpiri YAML Artifacts

YAML artifacts for Pullpiri container orchestration on the Guest node.

## Overview

These YAML files define container deployment specifications sent to Pullpiri via HTTP API when the rotary encoder is rotated on the Master node.

## Files

| File | Trigger | Action |
|------|---------|--------|
| `yaml/container-launch.yaml` | Rotary CW | Launch LED controller containers |
| `yaml/container-stop.yaml` | Rotary CCW | Stop LED controller containers |

## Schedule Configuration

```yaml
spec:
  - name: led_timpani
    priority: 50
    policy: FIFO
    cpu_affinity: 4096      # CPU core 12 (0x1000)
    period: 500000          # 500ms in microseconds
    release_time: 0
    runtime: 10000          # 10ms
    deadline: 500000        # 500ms
    node_id: guest
    max_dmiss: 3            # Max deadline misses before alert
```
