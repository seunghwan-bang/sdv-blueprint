#!/bin/bash
# Trigger CPU Load OFF - Stop workload

# All output goes to stdout so Python can capture it
{
    echo "========================================="
    echo "[CPU LOAD OFF] Stopping workload..."
    echo "Time: $(date)"
    echo "========================================="

    # Count processes before termination
    BEFORE=$(ps aux | grep -E "stress-ng" | grep -v grep | wc -l)
    ZOMBIE_BEFORE=$(ps aux | grep stress-ng | grep defunct | grep -v grep | wc -l)
    echo "Processes before: $BEFORE (zombies: $ZOMBIE_BEFORE)"
    
    # Step 1: Try graceful termination first (SIGTERM) to avoid zombies
    echo "Step 1: Graceful termination (SIGTERM)..."
    
    # Kill by process group ID first
    if [ -f /tmp/stress-ng/pgid ]; then
        MAIN_PID=$(cat /tmp/stress-ng/pgid 2>/dev/null)
        if [ ! -z "$MAIN_PID" ]; then
            # Get the process group ID
            PGID=$(ps -o pgid= -p $MAIN_PID 2>/dev/null | tr -d ' ')
            if [ ! -z "$PGID" ]; then
                echo "  Terminating process group: $PGID (main PID: $MAIN_PID)"
                # Kill entire process group
                kill -15 -$PGID 2>/dev/null || true
                # Also kill main process explicitly
                kill -15 $MAIN_PID 2>/dev/null || true
            fi
        fi
        rm -f /tmp/stress-ng/pgid
    fi
    
    # Kill all stress-ng processes by name
    pkill -15 stress-ng 2>/dev/null || true
    killall -15 stress-ng 2>/dev/null || true
    sleep 2
    
    # Step 2: Force kill if still running
    REMAINING=$(ps aux | grep stress-ng | grep -v grep | grep -v defunct | wc -l)
    if [ "$REMAINING" -gt 0 ]; then
        echo "Step 2: Force kill remaining processes ($REMAINING)..."
        
        # Find all stress-ng PIDs and kill them explicitly
        for pid in $(pgrep -x "stress-ng" 2>/dev/null); do
            echo "  Force killing PID: $pid"
            kill -9 $pid 2>/dev/null || true
        done
        
        # Also use pkill/killall
        pkill -9 stress-ng 2>/dev/null || true
        killall -9 stress-ng 2>/dev/null || true
        killall -9 stress-ng-cpu 2>/dev/null || true
        sleep 2
    fi
    
    # Step 3: Clean up zombies by waiting for parent to reap them
    echo "Step 3: Waiting for zombie cleanup..."
    
    # Wait for all background jobs (if any)
    wait 2>/dev/null || true
    
    sleep 3
    
    # Step 4: If zombies still exist, try to force cleanup
    ZOMBIE_CHECK=$(ps aux | grep stress-ng | grep defunct | grep -v grep | wc -l)
    if [ "$ZOMBIE_CHECK" -gt 0 ]; then
        echo "Step 4: Zombies detected ($ZOMBIE_CHECK), attempting aggressive cleanup..."
        
        # Find all stress-ng zombie PIDs and their parents
        ZOMBIE_INFO=$(ps -eo pid,ppid,pgid,stat,cmd | grep -E "Z.*stress-ng")
        
        if [ ! -z "$ZOMBIE_INFO" ]; then
            echo "Zombie processes:"
            echo "$ZOMBIE_INFO" | while read pid ppid pgid stat cmd; do
                echo "  PID=$pid PPID=$ppid PGID=$pgid STAT=$stat"
            done
            
            # Try to reap zombies by sending signals to parent
            ZOMBIE_PARENTS=$(echo "$ZOMBIE_INFO" | awk '{print $2}' | sort -u)
            
            for ppid in $ZOMBIE_PARENTS; do
                if [ "$ppid" != "0" ] && [ "$ppid" != "1" ]; then
                    PARENT_CMD=$(ps -p $ppid -o cmd= 2>/dev/null)
                    echo "  Parent process $ppid: $PARENT_CMD"
                    
                    # Send SIGCHLD to trigger zombie reaping
                    kill -CHLD $ppid 2>/dev/null || true
                    
                    # If parent is bash/sh script, it should reap now
                    sleep 1
                fi
            done
            
            # Final check
            FINAL_ZOMBIE=$(ps aux | grep stress-ng | grep defunct | grep -v grep | wc -l)
            if [ "$FINAL_ZOMBIE" -gt 0 ]; then
                echo "  Warning: $FINAL_ZOMBIE zombie(s) still remain"
                echo "  These will be reaped when parent process exits"
            else
                echo "  All zombies successfully cleaned"
            fi
        fi
    fi
    
    sleep 1

    # Verify termination
    AFTER=$(ps aux | grep -E "stress-ng" | grep -v grep | wc -l)
    ZOMBIE_AFTER=$(ps aux | grep stress-ng | grep defunct | grep -v grep | wc -l)
    echo "Processes after: $AFTER (zombies: $ZOMBIE_AFTER)"
    
    if [ "$AFTER" -eq 0 ]; then
        echo "✓ All stress-ng processes terminated"
    else
        echo "⚠ Warning: $AFTER stress-ng process(es) still running ($ZOMBIE_AFTER zombies)"
        if [ "$ZOMBIE_AFTER" -gt 0 ]; then
            echo "⚠ Zombie processes require parent process cleanup"
            echo "Remaining zombie parent PIDs:"
            ps -eo pid,ppid,stat,comm | grep defunct | grep stress-ng | awk '{print $2}' | sort -u
        fi
    fi
}
