#!/bin/bash
# Trigger CPU Load ON - Start workload

# All output goes to stdout so Python can capture it
{
    echo "========================================="
    echo "[CPU LOAD ON] Starting workload..."
    echo "Time: $(date)"
    echo "========================================="

    # Check if stress-ng is already running
    if pgrep -x "stress-ng" > /dev/null; then
        echo "⚠ stress-ng is already running, killing..."
        pkill -9 stress-ng
        killall -9 stress-ng 2>/dev/null
        sleep 1
    fi

    # Start stress-ng on all CPU cores in background (detached from shell)
    # Use nohup and disown to ensure it continues after script exits
    nohup stress-ng --cpu 0 --cpu-method all --timeout 0 >/dev/null 2>&1 &
    STRESS_PID=$!
    disown $STRESS_PID
    sleep 1

    # Verify process is running
    if ps -p $STRESS_PID > /dev/null 2>&1; then
        PROC_COUNT=$(pgrep -x "stress-ng" | wc -l)
        echo "✓ CPU Load started (PID: $STRESS_PID | nohup+disown)"
        echo "✓ Total stress-ng processes: $PROC_COUNT"
    else
        # Double check with pgrep (process might have forked)
        PROC_COUNT=$(pgrep -x "stress-ng" | wc -l)
        if [ "$PROC_COUNT" -gt 0 ]; then
            echo "✓ CPU Load started (forked, $PROC_COUNT processes)"
        else
            echo "✗ Failed to start stress-ng (no processes found)"
        fi
    fi
}
