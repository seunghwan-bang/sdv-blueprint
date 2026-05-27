#!/bin/bash
# Trigger CPU Load OFF - Stop workload

# All output goes to stdout so Python can capture it
{
    echo "========================================="
    echo "[CPU LOAD OFF] Stopping workload..."
    echo "Time: $(date)"
    echo "========================================="

    # Kill all stress-ng processes
    BEFORE=$(pgrep -x "stress-ng" | wc -l)
    echo "Processes before: $BEFORE"
    
    killall -9 stress-ng 2>/dev/null
    pkill -9 stress-ng 2>/dev/null
    sleep 1

    # Verify termination
    AFTER=$(pgrep -x "stress-ng" | wc -l)
    echo "Processes after: $AFTER"
    
    if [ "$AFTER" -eq 0 ]; then
        echo "✓ All stress-ng processes terminated"
    else
        echo "⚠ Warning: $AFTER stress-ng process(es) still running"
    fi
}
