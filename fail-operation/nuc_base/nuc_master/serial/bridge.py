import serial
import sys
import threading
import queue
import json
import time
import os

PORT_LIGHT = "/dev/arduino_light"
BAUD = 115200

def main(stop_event):
    while not stop_event.is_set():
        try:
            with serial.Serial(PORT_LIGHT, BAUD, timeout=0) as s_light:
                while not stop_event.is_set():
                    raw = s_light.readline()
                    if not raw:
                        continue
                    line = raw.decode(errors="replace").strip()
                    if not line:
                        continue
                    print(f"Light: {line}")
                    time.sleep(0.1)
        except (serial.SerialException, OSError) as e:
            print(f"Serial error: {e}. Reconnecting in 1 seconds...", file=sys.stderr)
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 1 seconds...", file=sys.stderr)
            time.sleep(1)

if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        main(stop_event)
    except KeyboardInterrupt:
        print("Stopped.")
        stop_event.set()
        sys.exit(0)
